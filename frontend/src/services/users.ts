import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';

export interface UserItem {
  id: string;
  username: string;
  role: 'admin' | 'hr';
  display_name: string;
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateUserInput {
  username: string;
  password: string;
  role: 'admin' | 'hr';
  display_name: string;
}

export interface UpdateUserInput {
  username?: string;
  role?: 'admin' | 'hr';
  display_name?: string;
  is_active?: boolean;
}

export async function fetchUsers(): Promise<UserItem[]> {
  const resp = await apiClient.get<ApiSuccessResponse<UserItem[]>>('/users/');
  return resp.data.data;
}

export async function createUser(input: CreateUserInput): Promise<UserItem> {
  const resp = await apiClient.post<ApiSuccessResponse<UserItem>>('/users/', input);
  return resp.data.data;
}

export async function updateUser(id: string, input: UpdateUserInput): Promise<UserItem> {
  const resp = await apiClient.put<ApiSuccessResponse<UserItem>>(`/users/${id}`, input);
  return resp.data.data;
}

export async function resetUserPassword(id: string, newPassword: string): Promise<void> {
  await apiClient.put(`/users/${id}/password`, { new_password: newPassword });
}
