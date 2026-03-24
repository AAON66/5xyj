import { createContext } from 'react';

import type { LoginCredentials } from '../services/auth';
import type { AuthRole, AuthSession } from '../services/authSession';

export interface AuthenticatedUser {
  username: string;
  role: AuthRole;
  displayName: string;
}

export interface AuthContextValue {
  session: AuthSession | null;
  user: AuthenticatedUser | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
