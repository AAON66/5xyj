import type { ApiSuccessResponse } from './api';
import { LONG_RUNNING_REQUEST_TIMEOUT_MS, apiClient } from './api';

export interface ImportSourceFile {
  id: string;
  file_name: string;
  file_path: string;
  file_size: number;
  region: string | null;
  company_name: string | null;
  file_hash: string | null;
  uploaded_at: string;
}

export interface ImportBatchSummary {
  id: string;
  batch_name: string;
  status: string;
  created_at: string;
  updated_at: string;
  file_count: number;
  created_by_name?: string | null;
  normalized_record_count?: number | null;
}

export interface ImportBatchDetail extends ImportBatchSummary {
  source_files: ImportSourceFile[];
}

export interface HeaderMappingPreview {
  raw_header: string;
  raw_header_signature: string;
  canonical_field: string | null;
  mapping_source: string;
  confidence: number | null;
  candidate_fields: string[];
  matched_rules: string[];
  llm_attempted: boolean;
  llm_status: string;
  rule_overrode_llm: boolean;
}

export interface FilteredRowPreview {
  row_number: number;
  reason: string;
  first_value: string;
}

export interface NormalizedPreviewRecord {
  source_row_number: number;
  values: Record<string, unknown>;
  unmapped_values: Record<string, unknown>;
  raw_values: Record<string, unknown>;
  raw_payload: Record<string, unknown>;
}

export interface SourceFilePreview {
  source_file_id: string;
  file_name: string;
  region: string | null;
  company_name: string | null;
  raw_sheet_name: string;
  raw_header_signature: string;
  normalized_record_count: number;
  filtered_row_count: number;
  unmapped_headers: string[];
  header_mappings: HeaderMappingPreview[];
  filtered_rows: FilteredRowPreview[];
  preview_records: NormalizedPreviewRecord[];
}

export interface ImportBatchPreview {
  batch_id: string;
  batch_name: string;
  status: string;
  source_files: SourceFilePreview[];
}

export interface BulkDeleteImportBatchesResult {
  deleted_count: number;
  deleted_ids: string[];
  missing_ids: string[];
}

export interface CreateImportBatchInput {
  files: File[];
  batchName?: string;
  region?: string;
  companyName?: string;
}

export interface FetchImportBatchPreviewOptions {
  sourceFileId?: string;
}

export interface BatchDeletionImpact {
  batch_id: string;
  batch_name: string;
  record_count: number;
  match_count: number;
  issue_count: number;
}

export async function fetchBatchDeletionImpact(batchId: string): Promise<BatchDeletionImpact> {
  const response = await apiClient.get<ApiSuccessResponse<BatchDeletionImpact>>(
    `/imports/${batchId}/deletion-impact`,
  );
  return response.data.data;
}

export async function fetchImportBatches(): Promise<ImportBatchSummary[]> {
  const response = await apiClient.get<ApiSuccessResponse<ImportBatchSummary[]>>('/imports');
  return response.data.data;
}

export async function fetchImportBatch(batchId: string): Promise<ImportBatchDetail> {
  const response = await apiClient.get<ApiSuccessResponse<ImportBatchDetail>>(`/imports/${batchId}`);
  return response.data.data;
}

export async function deleteImportBatch(batchId: string): Promise<void> {
  await apiClient.delete(`/imports/${batchId}`);
}

export async function bulkDeleteImportBatches(batchIds: string[]): Promise<BulkDeleteImportBatchesResult> {
  const response = await apiClient.post<ApiSuccessResponse<BulkDeleteImportBatchesResult>>('/imports/bulk-delete', {
    batch_ids: batchIds,
  });
  return response.data.data;
}

export async function createImportBatch(input: CreateImportBatchInput): Promise<ImportBatchDetail> {
  const formData = new FormData();
  for (const file of input.files) {
    formData.append('files', file);
  }
  if (input.batchName?.trim()) {
    formData.append('batch_name', input.batchName.trim());
  }
  if (input.region?.trim()) {
    formData.append('regions', input.region.trim());
  }
  if (input.companyName?.trim()) {
    formData.append('company_names', input.companyName.trim());
  }

  const response = await apiClient.post<ApiSuccessResponse<ImportBatchDetail>>('/imports', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: LONG_RUNNING_REQUEST_TIMEOUT_MS,
  });
  return response.data.data;
}

export async function parseImportBatch(batchId: string): Promise<ImportBatchPreview> {
  const response = await apiClient.post<ApiSuccessResponse<ImportBatchPreview>>(`/imports/${batchId}/parse`, undefined, {
    timeout: LONG_RUNNING_REQUEST_TIMEOUT_MS,
  });
  return response.data.data;
}

export async function fetchImportBatchPreview(batchId: string, options: FetchImportBatchPreviewOptions = {}): Promise<ImportBatchPreview> {
  const response = await apiClient.get<ApiSuccessResponse<ImportBatchPreview>>(`/imports/${batchId}/preview`, {
    params: options.sourceFileId ? { source_file_id: options.sourceFileId } : undefined,
    timeout: LONG_RUNNING_REQUEST_TIMEOUT_MS,
  });
  return response.data.data;
}
