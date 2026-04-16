import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';
import { getApiBaseUrl } from '../config/env';
import { readAuthSession } from './authSession';

// ── Type definitions ──────────────────────────────────────────────

export interface SyncConfig {
  id: string;
  name: string;
  app_token: string;
  table_id: string;
  granularity: 'detail' | 'summary';
  field_mapping: Record<string, string>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SyncJob {
  id: string;
  config_id: string;
  direction: 'push' | 'pull';
  status: 'pending' | 'running' | 'success' | 'failed' | 'partial';
  total_records: number;
  success_records: number;
  failed_records: number;
  error_message: string | null;
  detail: Record<string, unknown> | null;
  triggered_by: string;
  created_at: string;
}

export interface ConflictRecord {
  record_key: string;
  person_name: string | null;
  system_values: Record<string, unknown>;
  feishu_values: Record<string, unknown>;
  diff_fields: string[];
}

export interface ConflictPreview {
  total_conflicts: number;
  conflicts: ConflictRecord[];
}

export interface FeatureFlags {
  feishu_sync_enabled: boolean;
  feishu_oauth_enabled: boolean;
  feishu_credentials_configured: boolean;
}

export interface FeishuCredentialsStatus {
  configured: boolean;
  masked_app_id: string | null;
  secret_configured: boolean;
}

export interface FeishuRuntimeSettings {
  feishu_sync_enabled: boolean;
  feishu_oauth_enabled: boolean;
  feishu_credentials_configured: boolean;
  masked_app_id: string | null;
  secret_configured: boolean;
}

export interface FeishuRuntimeSettingsUpdate {
  feishu_sync_enabled?: boolean;
  feishu_oauth_enabled?: boolean;
}

export interface FeishuCredentialsInput {
  app_id: string;
  app_secret: string;
}

export interface FeishuFieldInfo {
  field_id: string;
  field_name: string;
  field_type: number;
  ui_type: string | null;
  description: string | null;
}

export interface MappingSuggestion {
  feishu_field_id: string;
  feishu_field_name: string;
  canonical_field: string;
  confidence: number;
  matched_rule: string;
}

export interface SuggestMappingResponse {
  suggestions: MappingSuggestion[];
  unmatched: string[];
}

// ── Feature flags ─────────────────────────────────────────────────

export async function fetchFeatureFlags(): Promise<FeatureFlags> {
  const response = await apiClient.get<ApiSuccessResponse<FeatureFlags>>(
    '/system/features',
  );
  return response.data.data;
}

export async function fetchFeishuRuntimeSettings(): Promise<FeishuRuntimeSettings> {
  const response = await apiClient.get<ApiSuccessResponse<FeishuRuntimeSettings>>(
    '/feishu/settings/runtime',
  );
  return response.data.data;
}

export async function updateFeishuRuntimeSettings(
  payload: FeishuRuntimeSettingsUpdate,
): Promise<FeishuRuntimeSettings> {
  const response = await apiClient.put<ApiSuccessResponse<FeishuRuntimeSettings>>(
    '/feishu/settings/runtime',
    payload,
  );
  return response.data.data;
}

export async function fetchFeishuCredentialsStatus(): Promise<FeishuCredentialsStatus> {
  const response = await apiClient.get<ApiSuccessResponse<FeishuCredentialsStatus>>(
    '/feishu/settings/credentials/status',
  );
  return response.data.data;
}

export async function updateFeishuCredentials(
  payload: FeishuCredentialsInput,
): Promise<FeishuRuntimeSettings> {
  const response = await apiClient.put<ApiSuccessResponse<FeishuRuntimeSettings>>(
    '/feishu/settings/credentials',
    payload,
  );
  return response.data.data;
}

// ── Sync configs (admin settings) ─────────────────────────────────

export async function fetchSyncConfigs(): Promise<SyncConfig[]> {
  const response = await apiClient.get<ApiSuccessResponse<SyncConfig[]>>(
    '/feishu/settings/configs',
  );
  return response.data.data;
}

export async function createSyncConfig(
  config: Omit<SyncConfig, 'id' | 'created_at' | 'updated_at' | 'is_active'>,
): Promise<SyncConfig> {
  const response = await apiClient.post<ApiSuccessResponse<SyncConfig>>(
    '/feishu/settings/configs',
    config,
  );
  return response.data.data;
}

export async function updateSyncConfig(
  id: string,
  updates: Partial<SyncConfig>,
): Promise<SyncConfig> {
  const response = await apiClient.put<ApiSuccessResponse<SyncConfig>>(
    `/feishu/settings/configs/${id}`,
    updates,
  );
  return response.data.data;
}

export async function deleteSyncConfig(id: string): Promise<void> {
  await apiClient.delete(`/feishu/settings/configs/${id}`);
}

export async function saveSyncConfigMapping(
  id: string,
  fieldMapping: Record<string, string>,
): Promise<SyncConfig> {
  const response = await apiClient.post<ApiSuccessResponse<SyncConfig>>(
    `/feishu/settings/configs/${id}/mapping`,
    { field_mapping: fieldMapping },
  );
  return response.data.data;
}

export async function fetchFeishuFields(
  configId: string,
): Promise<FeishuFieldInfo[]> {
  const response = await apiClient.get<ApiSuccessResponse<FeishuFieldInfo[]>>(
    `/feishu/settings/configs/${configId}/feishu-fields`,
    { skipGlobalError: true } as Record<string, unknown>,
  );
  return response.data.data;
}

export async function suggestMapping(
  configId: string,
  feishuFields: Array<{ field_name: string; field_id: string }>,
  systemFields?: string[],
): Promise<SuggestMappingResponse> {
  const response = await apiClient.post<ApiSuccessResponse<SuggestMappingResponse>>(
    `/feishu/settings/configs/${configId}/suggest-mapping`,
    { feishu_fields: feishuFields, system_fields: systemFields },
  );
  return response.data.data;
}

// ── Sync operations ───────────────────────────────────────────────

function getAuthHeaders(): Record<string, string> {
  const session = readAuthSession();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (session?.accessToken) {
    headers['Authorization'] = `Bearer ${session.accessToken}`;
  }
  return headers;
}

export function pushToFeishu(
  configId: string,
  filters?: Record<string, string>,
): Promise<Response> {
  return fetch(`${getApiBaseUrl()}/feishu/sync/push`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ config_id: configId, filters }),
  });
}

export function confirmPush(
  configId: string,
  action: 'overwrite' | 'skip' | 'cancel',
  recordKeys?: string[],
): Promise<Response> {
  return fetch(`${getApiBaseUrl()}/feishu/sync/push/confirm`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      config_id: configId,
      action,
      record_keys: recordKeys,
    }),
  });
}

export async function previewPullConflicts(
  configId: string,
): Promise<ConflictPreview> {
  const response = await apiClient.post<ApiSuccessResponse<ConflictPreview>>(
    '/feishu/sync/pull/preview',
    { config_id: configId },
  );
  return response.data.data;
}

export function executePull(
  configId: string,
  strategy: string,
  perRecordChoices?: Record<string, string>,
): Promise<Response> {
  return fetch(`${getApiBaseUrl()}/feishu/sync/pull/execute`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      config_id: configId,
      strategy,
      per_record_choices: perRecordChoices,
    }),
  });
}

// ── Sync history (includes offset for pagination — addresses M5) ─

export async function fetchSyncHistory(
  configId?: string,
  limit?: number,
  offset?: number,
): Promise<SyncJob[]> {
  const params: Record<string, string | number> = {};
  if (configId) params.config_id = configId;
  if (limit !== undefined) params.limit = limit;
  if (offset !== undefined) params.offset = offset;

  const response = await apiClient.get<ApiSuccessResponse<SyncJob[]>>(
    '/feishu/sync/history',
    { params },
  );
  return response.data.data;
}

export async function retrySyncJob(jobId: string): Promise<SyncJob> {
  const response = await apiClient.post<ApiSuccessResponse<SyncJob>>(
    `/feishu/sync/${jobId}/retry`,
  );
  return response.data.data;
}

// ── OAuth ─────────────────────────────────────────────────────────

export interface Candidate {
  employee_master_id: string;
  person_name: string;
  department: string;
  employee_id_masked: string;
}

export type FeishuOAuthResult =
  | { status: 'matched' | 'auto_bound' | 'new_user'; access_token: string; role: string; username: string; display_name: string }
  | { status: 'pending_candidates'; pending_token: string; feishu_name: string; candidates: Candidate[] };

export async function fetchFeishuAuthorizeUrl(): Promise<string> {
  const response = await apiClient.get<ApiSuccessResponse<string>>(
    '/auth/feishu/authorize-url',
  );
  return response.data.data;
}

export async function feishuOAuthCallback(
  code: string,
  state: string,
): Promise<FeishuOAuthResult> {
  const response = await apiClient.post<ApiSuccessResponse<FeishuOAuthResult>>(
    '/auth/feishu/callback',
    { code, state },
  );
  return response.data.data;
}

export async function confirmFeishuBind(
  pendingToken: string,
  employeeMasterId: string,
): Promise<{ access_token: string; role: string; username: string; display_name: string }> {
  const response = await apiClient.post<
    ApiSuccessResponse<{ access_token: string; role: string; username: string; display_name: string }>
  >('/auth/feishu/confirm-bind', {
    pending_token: pendingToken,
    employee_master_id: employeeMasterId,
  });
  return response.data.data;
}

// ── NDJSON stream helper ──────────────────────────────────────────

export async function readNdjsonStream(
  response: Response,
  onEvent: (event: { type: string; [key: string]: unknown }) => void,
): Promise<void> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (line.trim()) {
        onEvent(JSON.parse(line));
      }
    }
  }
  if (buffer.trim()) {
    onEvent(JSON.parse(buffer));
  }
}
