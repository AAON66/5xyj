import { getApiBaseUrl } from "../config/env";
import { ApiClientError, type ApiSuccessResponse, apiClient } from "./api";
import { clearAuthSession, readAuthSession } from "./authSession";

export type CompareCellValue = string | number | null;

export interface CompareBatchMeta {
  id: string;
  batch_name: string;
  status: string;
  record_count: number;
}

export interface CompareRecordSide {
  record_id: string | null;
  source_file_id: string | null;
  source_file_name: string | null;
  source_row_number: number | null;
  values: Record<string, CompareCellValue>;
}

export interface CompareRow {
  compare_key: string;
  match_basis: string;
  diff_status: string;
  different_fields: string[];
  left: CompareRecordSide;
  right: CompareRecordSide;
}

export interface BatchCompareResult {
  left_batch: CompareBatchMeta;
  right_batch: CompareBatchMeta;
  fields: string[];
  total_row_count: number;
  same_row_count: number;
  changed_row_count: number;
  left_only_count: number;
  right_only_count: number;
  rows: CompareRow[];
}

export interface CompareExportPayload {
  left_batch_name: string;
  right_batch_name: string;
  fields: string[];
  rows: CompareRow[];
}

export async function fetchBatchCompare(leftBatchId: string, rightBatchId: string): Promise<BatchCompareResult> {
  const response = await apiClient.get<ApiSuccessResponse<BatchCompareResult>>("/compare", {
    params: {
      left_batch_id: leftBatchId,
      right_batch_id: rightBatchId,
    },
  });
  return response.data.data;
}

export async function exportBatchCompare(payload: CompareExportPayload): Promise<{ blob: Blob; fileName: string }> {
  const session = readAuthSession();
  const response = await fetch(`${getApiBaseUrl()}/compare/export`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(session?.accessToken ? { Authorization: `Bearer ${session.accessToken}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuthSession();
    }
    let message = `Request failed with status ${response.status}.`;
    try {
      const errorPayload = (await response.json()) as { error?: { message?: string } };
      if (errorPayload.error?.message) {
        message = errorPayload.error.message;
      }
    } catch {
      // Ignore response parse errors and keep the generic message.
    }
    throw new ApiClientError(message, { statusCode: response.status });
  }

  const blob = await response.blob();
  return {
    blob,
    fileName: resolveDownloadFileName(response.headers.get("content-disposition")) ?? "compare.xlsx",
  };
}

// --- Period comparison types and API ---

export interface PeriodCompareSummaryGroup {
  company_name: string | null;
  region: string | null;
  total_count: number;
  changed_count: number;
  left_only_count: number;
  right_only_count: number;
  same_count: number;
}

export interface PeriodCompareResult {
  left_period: string;
  right_period: string;
  fields: string[];
  total_row_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  returned_row_count: number;
  diff_only: boolean;
  search_text: string | null;
  same_row_count: number;
  changed_row_count: number;
  left_only_count: number;
  right_only_count: number;
  rows: CompareRow[];
  summary_groups: PeriodCompareSummaryGroup[];
}

export async function fetchPeriodCompare(
  leftPeriod: string,
  rightPeriod: string,
  options?: {
    region?: string;
    companyName?: string;
    searchText?: string;
    diffOnly?: boolean;
    page?: number;
    pageSize?: number;
  },
): Promise<PeriodCompareResult> {
  const params: Record<string, string | number> = {
    left_period: leftPeriod,
    right_period: rightPeriod,
  };
  if (options?.region) params.region = options.region;
  if (options?.companyName) params.company_name = options.companyName;
  if (options?.searchText?.trim()) params.search_text = options.searchText.trim();
  if (options?.diffOnly !== undefined) params.diff_only = options.diffOnly ? "true" : "false";
  if (options?.page !== undefined) params.page = options.page;
  params.page_size = options?.pageSize ?? 20;

  const response = await apiClient.get<ApiSuccessResponse<PeriodCompareResult>>("/compare/periods", { params });
  return response.data.data;
}

function resolveDownloadFileName(contentDisposition: string | null): string | null {
  if (!contentDisposition) {
    return null;
  }

  const encodedMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (encodedMatch?.[1]) {
    return decodeURIComponent(encodedMatch[1]);
  }

  const plainMatch = contentDisposition.match(/filename="([^"]+)"/i);
  if (plainMatch?.[1]) {
    return plainMatch[1];
  }

  return null;
}
