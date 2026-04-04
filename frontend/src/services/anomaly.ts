import type { ApiSuccessResponse } from "./api";
import { apiClient } from "./api";

export interface AnomalyRecord {
  id: string;
  employee_identifier: string;
  person_name: string | null;
  company_name: string | null;
  region: string | null;
  left_period: string;
  right_period: string;
  field_name: string;
  left_value: number | null;
  right_value: number | null;
  change_percent: number;
  threshold_percent: number;
  status: "pending" | "confirmed" | "excluded";
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface DetectAnomaliesRequest {
  left_period: string;
  right_period: string;
  thresholds: Record<string, number>;
}

export async function detectAnomalies(
  request: DetectAnomaliesRequest,
): Promise<AnomalyRecord[]> {
  const response = await apiClient.post<ApiSuccessResponse<AnomalyRecord[]>>(
    "/anomalies/detect",
    request,
  );
  return response.data.data;
}

export async function fetchAnomalies(params: {
  left_period?: string;
  right_period?: string;
  status?: string;
  field_name?: string;
  page?: number;
  page_size?: number;
}): Promise<{ items: AnomalyRecord[]; total: number }> {
  const searchParams: Record<string, string | number> = {};
  if (params.left_period) searchParams.left_period = params.left_period;
  if (params.right_period) searchParams.right_period = params.right_period;
  if (params.status) searchParams.status = params.status;
  if (params.field_name) searchParams.field_name = params.field_name;
  if (params.page !== undefined) searchParams.page = params.page;
  searchParams.page_size = params.page_size ?? 20;

  const response = await apiClient.get<{
    success: boolean;
    data: AnomalyRecord[];
    pagination: { total: number; page: number; page_size: number };
  }>("/anomalies", { params: searchParams });
  return {
    items: response.data.data,
    total: response.data.pagination.total,
  };
}

export async function updateAnomalyStatus(
  status: "confirmed" | "excluded",
  anomalyIds: string[],
): Promise<{ updated_count: number }> {
  const response = await apiClient.patch<
    ApiSuccessResponse<{ updated_count: number }>
  >("/anomalies/status", {
    status,
    anomaly_ids: anomalyIds,
  });
  return response.data.data;
}
