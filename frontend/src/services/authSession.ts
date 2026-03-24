export type AuthRole = 'admin' | 'hr';

export interface AuthSession {
  accessToken: string;
  expiresAt: string;
  username: string;
  role: AuthRole;
  displayName: string;
  signedInAt: string;
}

const AUTH_SESSION_KEY = 'social-security-auth-session';
export const AUTH_SESSION_EVENT = 'social-security-auth-session-changed';

function canUseSessionStorage(): boolean {
  return typeof window !== 'undefined' && typeof window.sessionStorage !== 'undefined';
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
    (candidate.role === 'admin' || candidate.role === 'hr') &&
    typeof candidate.displayName === 'string' &&
    typeof candidate.signedInAt === 'string'
  );
}

export function isAuthSessionExpired(session: AuthSession): boolean {
  const expiresAt = new Date(session.expiresAt).getTime();
  return !Number.isFinite(expiresAt) || expiresAt <= Date.now();
}

export function readAuthSession(): AuthSession | null {
  if (!canUseSessionStorage()) {
    return null;
  }

  const rawValue = window.sessionStorage.getItem(AUTH_SESSION_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue);
    if (!isAuthSessionShape(parsed) || isAuthSessionExpired(parsed)) {
      window.sessionStorage.removeItem(AUTH_SESSION_KEY);
      return null;
    }
    return parsed;
  } catch {
    window.sessionStorage.removeItem(AUTH_SESSION_KEY);
    return null;
  }
}

export function writeAuthSession(session: AuthSession): void {
  if (!canUseSessionStorage()) {
    return;
  }

  window.sessionStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(session));
  emitAuthSessionChanged();
}

export function clearAuthSession(): void {
  if (!canUseSessionStorage()) {
    return;
  }

  window.sessionStorage.removeItem(AUTH_SESSION_KEY);
  emitAuthSessionChanged();
}
