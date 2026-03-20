import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';
import { fetchImportBatches, type ImportBatchSummary } from './imports';

export interface ValidationIssue {
  normalized_record_id: string | null;
  source_row_number: number;
  issue_type: string;
  severity: string;
  field_name: string | null;
  message: string;
}

export interface SourceFileValidation {
  source_file_id: string;
  file_name: string;
  raw_sheet_name: string;
  issue_count: number;
  issues: ValidationIssue[];
}

export interface BatchValidation {
  batch_id: string;
  batch_name: string;
  status: string;
  total_issue_count: number;
  source_files: SourceFileValidation[];
}

export interface MatchRecord {
  normalized_record_id: string | null;
  source_row_number: number;
  person_name: string | null;
  id_number: string | null;
  employee_id: string | null;
  employee_master_id: string | null;
  match_status: string;
  match_basis: string | null;
  confidence: number | null;
  candidate_employee_ids: string[];
}

export interface SourceFileMatch {
  source_file_id: string;
  file_name: string;
  raw_sheet_name: string;
  result_count: number;
  results: MatchRecord[];
}

export interface BatchMatch {
  batch_id: string;
  batch_name: string;
  status: string;
  employee_master_available: boolean;
  employee_master_count: number;
  blocked_reason: string | null;
  total_records: number;
  matched_count: number;
  unmatched_count: number;
  duplicate_count: number;
  low_confidence_count: number;
  source_files: SourceFileMatch[];
}

export interface ExportArtifact {
  template_type: string;
  status: string;
  file_path: string | null;
  error_message: string | null;
  row_count: number;
}

export interface BatchExport {
  batch_id: string;
  batch_name: string;
  status: string;
  export_job_id: string | null;
  export_status: string | null;
  blocked_reason: string | null;
  artifacts: ExportArtifact[];
  completed_at: string | null;
}

export async function fetchRuntimeBatches(): Promise<ImportBatchSummary[]> {
  return fetchImportBatches();
}

export async function validateBatch(batchId: string): Promise<BatchValidation> {
  const response = await apiClient.post<ApiSuccessResponse<BatchValidation>>(`/imports/${batchId}/validate`);
  return response.data.data;
}

export async function fetchBatchValidation(batchId: string): Promise<BatchValidation> {
  const response = await apiClient.get<ApiSuccessResponse<BatchValidation>>(`/imports/${batchId}/validation`);
  return response.data.data;
}

export async function matchBatch(batchId: string): Promise<BatchMatch> {
  const response = await apiClient.post<ApiSuccessResponse<BatchMatch>>(`/imports/${batchId}/match`);
  return response.data.data;
}

export async function fetchBatchMatch(batchId: string): Promise<BatchMatch> {
  const response = await apiClient.get<ApiSuccessResponse<BatchMatch>>(`/imports/${batchId}/match`);
  return response.data.data;
}

export async function exportBatch(batchId: string): Promise<BatchExport> {
  const response = await apiClient.post<ApiSuccessResponse<BatchExport>>(`/imports/${batchId}/export`);
  return response.data.data;
}

export async function fetchBatchExport(batchId: string): Promise<BatchExport> {
  const response = await apiClient.get<ApiSuccessResponse<BatchExport>>(`/imports/${batchId}/export`);
  return response.data.data;
}
