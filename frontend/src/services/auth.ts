import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';
import type { AuthRole, AuthSession } from './authSession';

export interface AuthenticatedUserProfile {
  username: string;
  role: AuthRole;
  display_name: string;
  must_change_password?: boolean;
}

interface AuthLoginResponse {
  access_token: string;
  token_type: 'bearer';
  expires_at: string;
  user: AuthenticatedUserProfile;
}

export interface LoginCredentials {
  username: string;
  password: string;
  role: AuthRole;
}

export interface EmployeeVerifyInput {
  employee_id: string;
  id_number: string;
  person_name: string;
}

export async function loginWithPassword(input: LoginCredentials): Promise<AuthSession> {
  const response = await apiClient.post<ApiSuccessResponse<AuthLoginResponse>>('/auth/login', input);
  const payload = response.data.data;

  return {
    accessToken: payload.access_token,
    expiresAt: payload.expires_at,
    username: payload.user.username,
    role: payload.user.role,
    displayName: payload.user.display_name,
    signedInAt: new Date().toISOString(),
    mustChangePassword: payload.user.must_change_password,
  };
}

export async function verifyEmployee(input: EmployeeVerifyInput): Promise<AuthSession> {
  const response = await apiClient.post<ApiSuccessResponse<AuthLoginResponse>>('/auth/employee-verify', input);
  const payload = response.data.data;

  return {
    accessToken: payload.access_token,
    expiresAt: payload.expires_at,
    username: payload.user.username,
    role: payload.user.role as AuthRole,
    displayName: payload.user.display_name,
    signedInAt: new Date().toISOString(),
    mustChangePassword: false,
  };
}

export async function fetchAuthenticatedUser(): Promise<AuthenticatedUserProfile> {
  const response = await apiClient.get<ApiSuccessResponse<AuthenticatedUserProfile>>('/auth/me');
  return response.data.data;
}
