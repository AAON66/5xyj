import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';
import type { AuthRole, AuthSession } from './authSession';

export interface AuthenticatedUserProfile {
  username: string;
  role: AuthRole;
  display_name: string;
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
  };
}

export async function fetchAuthenticatedUser(): Promise<AuthenticatedUserProfile> {
  const response = await apiClient.get<ApiSuccessResponse<AuthenticatedUserProfile>>('/auth/me');
  return response.data.data;
}
