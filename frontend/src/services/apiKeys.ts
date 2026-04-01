import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';

export interface ApiKeyRead {
  id: string;
  name: string;
  key_prefix: string;
  owner_id: string;
  owner_username: string;
  owner_role: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreateResponse {
  id: string;
  name: string;
  key: string;
  key_prefix: string;
  owner_username: string;
  owner_role: string;
  created_at: string;
}

export interface ApiKeyListResponse {
  items: ApiKeyRead[];
  total: number;
}

export async function createApiKey(name: string, ownerId: string): Promise<ApiKeyCreateResponse> {
  const response = await apiClient.post<ApiSuccessResponse<ApiKeyCreateResponse>>('/api-keys/', {
    name,
    owner_id: ownerId,
  });
  return response.data.data;
}

export async function listApiKeys(): Promise<ApiKeyListResponse> {
  const response = await apiClient.get<ApiSuccessResponse<ApiKeyListResponse>>('/api-keys/');
  return response.data.data;
}

export async function revokeApiKey(keyId: string): Promise<void> {
  await apiClient.delete(`/api-keys/${keyId}`);
}
