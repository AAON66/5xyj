import { getApiBaseUrl } from '../config/env';
import { ApiClientError, type ApiSuccessResponse, apiClient } from './api';
import { clearAuthSession, readAuthSession } from './authSession';

export interface AggregateEmployeeImport {
  file_name: string;
  imported_count: number;
  created_count: number;
  updated_count: number;
}

export interface AggregateSourceFile {
  source_file_id: string;
  file_name: string;
  source_kind: string;
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
  fusion_messages: string[];
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
  parse_summary?: {
    total_files: number;
    worker_count: number;
    active_count: number;
    analyzed_count: number;
    saved_count: number;
    queued_count: number;
  };
  parse_files?: Array<{
    source_file_id?: string;
    file_index: number;
    file_name: string;
    source_kind?: string | null;
    region?: string | null;
    company_name?: string | null;
    phase: string;
    normalized_record_count?: number;
    filtered_row_count?: number;
    unmapped_header_count?: number;
    raw_sheet_name?: string;
  }>;
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

export interface AggregateInput {
  files: File[];
  housingFundFiles?: File[];
  employeeMasterFile?: File | null;
  employeeMasterMode?: 'none' | 'upload' | 'existing';
  burdenFile?: File | null;
  burdenSourceMode?: 'none' | 'excel' | 'feishu';
  burdenFeishuConfigId?: string | null;
  fusionRuleIds?: string[];
  batchName?: string;
}

function buildAggregateFormData(input: AggregateInput): FormData {
  const formData = new FormData();
  input.files.forEach((file) => formData.append('files', file));
  (input.housingFundFiles ?? []).forEach((file) => formData.append('housing_fund_files', file));
  if (input.employeeMasterFile) {
    formData.append('employee_master_file', input.employeeMasterFile);
  }
  if (input.employeeMasterMode) {
    formData.append('employee_master_mode', input.employeeMasterMode);
  }
  if (input.burdenFile) {
    formData.append('burden_file', input.burdenFile);
  }
  if (input.burdenSourceMode) {
    formData.append('burden_source_mode', input.burdenSourceMode);
  }
  if (input.burdenFeishuConfigId) {
    formData.append('burden_feishu_config_id', input.burdenFeishuConfigId);
  }
  if (input.fusionRuleIds) {
    formData.append('fusion_rule_ids', JSON.stringify(input.fusionRuleIds));
  }
  if (input.batchName?.trim()) {
    formData.append('batch_name', input.batchName.trim());
  }
  return formData;
}

function buildAuthorizedHeaders(headers?: HeadersInit): Headers {
  const resolvedHeaders = new Headers(headers);
  const session = readAuthSession();
  if (session?.accessToken) {
    resolvedHeaders.set('Authorization', `Bearer ${session.accessToken}`);
  }
  return resolvedHeaders;
}

export async function runSimpleAggregate(input: AggregateInput): Promise<AggregateRunResult> {
  const response = await apiClient.post<ApiSuccessResponse<AggregateRunResult>>('/aggregate', buildAggregateFormData(input), {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  });
  return response.data.data;
}

export async function runSimpleAggregateWithProgress(
  input: AggregateInput & {
    onProgress?: (event: AggregateProgressEvent) => void;
    signal?: AbortSignal;
  },
): Promise<AggregateRunResult> {
  const response = await fetch(`${getApiBaseUrl()}/aggregate/stream`, {
    method: 'POST',
    body: buildAggregateFormData(input),
    signal: input.signal,
    headers: buildAuthorizedHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuthSession();
    }
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

export async function downloadAggregateArtifact(batchId: string, templateType: string): Promise<{ blob: Blob; fileName: string }> {
  const response = await apiClient.get<Blob>(`/imports/${encodeURIComponent(batchId)}/export/${encodeURIComponent(templateType)}/download`, {
    responseType: 'blob',
  });

  return {
    blob: response.data,
    fileName: resolveDownloadFileName(response.headers['content-disposition']) ?? `${templateType}.xlsx`,
  };
}

export function getAggregateArtifactDownloadUrl(batchId: string, templateType: string): string {
  return `${getApiBaseUrl()}/imports/${encodeURIComponent(batchId)}/export/${encodeURIComponent(templateType)}/download`;
}

function resolveDownloadFileName(contentDisposition: string | null | undefined): string | null {
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
