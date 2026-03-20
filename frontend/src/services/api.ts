import axios, { AxiosError } from "axios";

import { getApiBaseUrl } from "../config/env";

export interface ApiSuccessResponse<T> {
  success: true;
  message: string;
  data: T;
}

export interface ApiFailureResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export class ApiClientError extends Error {
  statusCode?: number;
  code?: string;
  details?: unknown;
  raw?: unknown;

  constructor(message: string, options: { statusCode?: number; code?: string; details?: unknown; raw?: unknown } = {}) {
    super(message);
    this.name = "ApiClientError";
    this.statusCode = options.statusCode;
    this.code = options.code;
    this.details = options.details;
    this.raw = options.raw;
  }
}

export interface ApiInterceptorCallbacks {
  onRequestStart?: () => void;
  onRequestEnd?: () => void;
  onError?: (error: ApiClientError) => void;
}

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 15000,
});

export function normalizeApiError(error: unknown): ApiClientError {
  if (error instanceof ApiClientError) {
    return error;
  }

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiFailureResponse>;
    const payload = axiosError.response?.data;
    const fallbackMessage = axiosError.message || "Request failed.";

    return new ApiClientError(payload?.error.message ?? fallbackMessage, {
      statusCode: axiosError.response?.status,
      code: payload?.error.code,
      details: payload?.error.details,
      raw: error,
    });
  }

  if (error instanceof Error) {
    return new ApiClientError(error.message, { raw: error });
  }

  return new ApiClientError("Unknown request error.", { raw: error });
}

export function attachApiInterceptors(callbacks: ApiInterceptorCallbacks): () => void {
  const requestInterceptor = apiClient.interceptors.request.use(
    (config) => {
      callbacks.onRequestStart?.();
      return config;
    },
    (error) => {
      callbacks.onRequestEnd?.();
      return Promise.reject(normalizeApiError(error));
    },
  );

  const responseInterceptor = apiClient.interceptors.response.use(
    (response) => {
      callbacks.onRequestEnd?.();
      return response;
    },
    (error) => {
      callbacks.onRequestEnd?.();
      const normalized = normalizeApiError(error);
      callbacks.onError?.(normalized);
      return Promise.reject(normalized);
    },
  );

  return () => {
    apiClient.interceptors.request.eject(requestInterceptor);
    apiClient.interceptors.response.eject(responseInterceptor);
  };
}
