import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';

export interface AggregateEmployeeImport {
  file_name: string;
  imported_count: number;
  created_count: number;
  updated_count: number;
}

export interface AggregateSourceFile {
  source_file_id: string;
  file_name: string;
  region: string | null;
  company_name: string | null;
  normalized_record_count: number;
  filtered_row_count: number;
}

export interface AggregateArtifact {
  template_type: string;
  status: string;
  file_path: string | null;
  error_message: string | null;
  row_count: number;
}

export interface AggregateRunResult {
  batch_id: string;
  batch_name: string;
  status: string;
  export_status: string | null;
  blocked_reason: string | null;
  employee_master: AggregateEmployeeImport | null;
  total_issue_count: number;
  matched_count: number;
  unmatched_count: number;
  duplicate_count: number;
  low_confidence_count: number;
  source_files: AggregateSourceFile[];
  artifacts: AggregateArtifact[];
}

export async function runSimpleAggregate(input: {
  files: File[];
  employeeMasterFile?: File | null;
  batchName?: string;
}): Promise<AggregateRunResult> {
  const formData = new FormData();
  input.files.forEach((file) => formData.append('files', file));
  if (input.employeeMasterFile) {
    formData.append('employee_master_file', input.employeeMasterFile);
  }
  if (input.batchName?.trim()) {
    formData.append('batch_name', input.batchName.trim());
  }

  const response = await apiClient.post<ApiSuccessResponse<AggregateRunResult>>('/aggregate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data.data;
}
