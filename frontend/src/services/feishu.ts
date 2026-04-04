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

export interface FeishuFieldInfo {
  field_id: string;
  field_name: string;
  field_type: number;
  description: string | null;
}

// ── Feature flags ─────────────────────────────────────────────────

export async function fetchFeatureFlags(): Promise<FeatureFlags> {
  const response = await apiClient.get<ApiSuccessResponse<FeatureFlags>>(
    '/system/features',
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

export async function fetchFeishuAuthorizeUrl(): Promise<string> {
  const response = await apiClient.get<ApiSuccessResponse<string>>(
    '/auth/feishu/authorize-url',
  );
  return response.data.data;
}

export async function feishuOAuthCallback(
  code: string,
  state: string,
): Promise<{
  access_token: string;
  role: string;
  username: string;
  display_name: string;
}> {
  const response = await apiClient.post<
    ApiSuccessResponse<{
      access_token: string;
      role: string;
      username: string;
      display_name: string;
    }>
  >('/auth/feishu/callback', { code, state });
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
