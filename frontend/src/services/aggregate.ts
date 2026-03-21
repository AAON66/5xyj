import { getApiBaseUrl } from '../config/env';
import { ApiClientError, type ApiSuccessResponse, apiClient } from './api';

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

export interface AggregateProgressEvent {
  stage: string;
  label: string;
  message: string;
  percent: number;
  batch_id?: string;
  batch_name?: string;
}

interface AggregateStreamProgressEnvelope extends AggregateProgressEvent {
  event: 'progress';
}

interface AggregateStreamResultEnvelope {
  event: 'result';
  data: AggregateRunResult;
}

interface AggregateStreamErrorEnvelope {
  event: 'error';
  code?: string;
  message: string;
}

type AggregateStreamEnvelope =
  | AggregateStreamProgressEnvelope
  | AggregateStreamResultEnvelope
  | AggregateStreamErrorEnvelope;

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

export async function runSimpleAggregateWithProgress(input: {
  files: File[];
  employeeMasterFile?: File | null;
  batchName?: string;
  onProgress?: (event: AggregateProgressEvent) => void;
}): Promise<AggregateRunResult> {
  const formData = new FormData();
  input.files.forEach((file) => formData.append('files', file));
  if (input.employeeMasterFile) {
    formData.append('employee_master_file', input.employeeMasterFile);
  }
  if (input.batchName?.trim()) {
    formData.append('batch_name', input.batchName.trim());
  }

  const response = await fetch(`${getApiBaseUrl()}/aggregate/stream`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new ApiClientError(`Request failed with status ${response.status}.`, { statusCode: response.status });
  }
  if (!response.body) {
    throw new ApiClientError('Streaming response body was not available.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalResult: AggregateRunResult | null = null;

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });

    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line) {
        continue;
      }

      const payload = JSON.parse(line) as AggregateStreamEnvelope;
      if (payload.event === 'progress') {
        input.onProgress?.(payload);
        continue;
      }
      if (payload.event === 'error') {
        throw new ApiClientError(payload.message, { code: payload.code });
      }
      finalResult = payload.data;
    }

    if (done) {
      break;
    }
  }

  if (buffer.trim()) {
    const trailingPayload = JSON.parse(buffer.trim()) as AggregateStreamEnvelope;
    if (trailingPayload.event === 'progress') {
      input.onProgress?.(trailingPayload);
    } else if (trailingPayload.event === 'error') {
      throw new ApiClientError(trailingPayload.message, { code: trailingPayload.code });
    } else {
      finalResult = trailingPayload.data;
    }
  }

  if (!finalResult) {
    throw new ApiClientError('Aggregate stream finished without a final result.');
  }
  return finalResult;
}
