import type { ApiSuccessResponse } from "./api";
import { apiClient } from "./api";

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
}

export async function fetchSystemHealth(): Promise<SystemHealth> {
  const response = await apiClient.get<ApiSuccessResponse<SystemHealth>>("/system/health");
  return response.data.data;
}
