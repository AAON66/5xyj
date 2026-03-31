import axios, { AxiosError, AxiosHeaders } from "axios";

import { getApiBaseUrl } from "../config/env";
import { clearAuthSession, readAuthSession } from "./authSession";

export const DEFAULT_REQUEST_TIMEOUT_MS = 600000;
export const LONG_RUNNING_REQUEST_TIMEOUT_MS = 900000;

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
  timeout: DEFAULT_REQUEST_TIMEOUT_MS,
});

export function normalizeApiError(error: unknown): ApiClientError {
  if (error instanceof ApiClientError) {
    return error;
  }

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiFailureResponse>;
    const payload = axiosError.response?.data;
    const isTimeout = axiosError.code === "ECONNABORTED" || /timeout/i.test(axiosError.message || "");
    const fallbackMessage = isTimeout ? "请求超时，请稍后重试，或减少单次处理文件数量。" : axiosError.message || "Request failed.";

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
      const session = readAuthSession();

      if (session?.accessToken) {
        const headers = AxiosHeaders.from(config.headers ?? {});
        headers.set("Authorization", `Bearer ${session.accessToken}`);
        config.headers = headers;
      }

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
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        clearAuthSession();
      }
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
