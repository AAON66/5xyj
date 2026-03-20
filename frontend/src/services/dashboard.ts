import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';

export interface DashboardTotals {
  total_batches: number;
  total_source_files: number;
  total_normalized_records: number;
  total_validation_issues: number;
  total_match_results: number;
  total_export_jobs: number;
  active_employee_masters: number;
}

export interface DashboardRecentBatch {
  batch_id: string;
  batch_name: string;
  status: string;
  file_count: number;
  normalized_record_count: number;
  validation_issue_count: number;
  match_result_count: number;
  export_job_count: number;
  created_at: string;
  updated_at: string;
}

export interface DashboardOverview {
  generated_at: string;
  totals: DashboardTotals;
  batch_status_counts: Record<string, number>;
  match_status_counts: Record<string, number>;
  issue_severity_counts: Record<string, number>;
  export_status_counts: Record<string, number>;
  recent_batches: DashboardRecentBatch[];
}

export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  const response = await apiClient.get<ApiSuccessResponse<DashboardOverview>>('/dashboard/overview');
  return response.data.data;
}
