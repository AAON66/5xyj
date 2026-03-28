export type AuthRole = 'admin' | 'hr' | 'employee';

export interface AuthSession {
  accessToken: string;
  expiresAt: string;
  username: string;
  role: AuthRole;
  displayName: string;
  signedInAt: string;
  mustChangePassword?: boolean;
}

const AUTH_SESSION_KEY = 'social-security-auth-session';
export const AUTH_SESSION_EVENT = 'social-security-auth-session-changed';

function canUseLocalStorage(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function emitAuthSessionChanged(): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(AUTH_SESSION_EVENT));
  }
}

function isAuthSessionShape(value: unknown): value is AuthSession {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const candidate = value as Partial<AuthSession>;
  return (
    typeof candidate.accessToken === 'string' &&
    typeof candidate.expiresAt === 'string' &&
    typeof candidate.username === 'string' &&
    (candidate.role === 'admin' || candidate.role === 'hr' || candidate.role === 'employee') &&
    typeof candidate.displayName === 'string' &&
    typeof candidate.signedInAt === 'string'
  );
}

export function isAuthSessionExpired(session: AuthSession): boolean {
  const expiresAt = new Date(session.expiresAt).getTime();
  return !Number.isFinite(expiresAt) || expiresAt <= Date.now();
}

export function readAuthSession(): AuthSession | null {
  if (!canUseLocalStorage()) {
    return null;
  }

  const rawValue = window.localStorage.getItem(AUTH_SESSION_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue);
    if (!isAuthSessionShape(parsed) || isAuthSessionExpired(parsed)) {
      window.localStorage.removeItem(AUTH_SESSION_KEY);
      return null;
    }
    return parsed;
  } catch {
    window.localStorage.removeItem(AUTH_SESSION_KEY);
    return null;
  }
}

export function writeAuthSession(session: AuthSession): void {
  if (!canUseLocalStorage()) {
    return;
  }

  window.localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(session));
  emitAuthSessionChanged();
}

export function clearAuthSession(): void {
  if (!canUseLocalStorage()) {
    return;
  }

  window.localStorage.removeItem(AUTH_SESSION_KEY);
  emitAuthSessionChanged();
}
