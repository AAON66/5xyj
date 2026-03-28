import { useEffect, useMemo, useState, type PropsWithChildren } from 'react';

import { AuthContext, type AuthenticatedUser } from '../hooks/authContext';
import type { EmployeeVerifyInput, LoginCredentials } from '../services/auth';
import { fetchAuthenticatedUser, loginWithPassword, verifyEmployee as verifyEmployeeApi } from '../services/auth';
import { AUTH_SESSION_EVENT, clearAuthSession, readAuthSession, writeAuthSession, type AuthSession } from '../services/authSession';

function buildAuthenticatedUser(session: AuthSession | null): AuthenticatedUser | null {
  if (!session) {
    return null;
  }

  return {
    username: session.username,
    role: session.role,
    displayName: session.displayName,
    mustChangePassword: session.mustChangePassword,
  };
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<AuthSession | null>(() => readAuthSession());
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    const handleSessionChange = () => {
      setSession(readAuthSession());
    };

    window.addEventListener(AUTH_SESSION_EVENT, handleSessionChange);
    return () => {
      window.removeEventListener(AUTH_SESSION_EVENT, handleSessionChange);
    };
  }, []);

  useEffect(() => {
    let isActive = true;
    const restored = readAuthSession();

    if (!restored) {
      setSession(null);
      setIsInitializing(false);
      return () => {
        isActive = false;
      };
    }

    setSession(restored);

    fetchAuthenticatedUser()
      .then((user) => {
        if (!isActive) {
          return;
        }

        const nextSession: AuthSession = {
          ...restored,
          username: user.username,
          role: user.role,
          displayName: user.display_name,
          mustChangePassword: user.must_change_password,
        };
        writeAuthSession(nextSession);
        setSession(nextSession);
      })
      .catch(() => {
        if (!isActive) {
          return;
        }

        clearAuthSession();
        setSession(null);
      })
      .finally(() => {
        if (isActive) {
          setIsInitializing(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  async function login(credentials: LoginCredentials) {
    const nextSession = await loginWithPassword(credentials);
    writeAuthSession(nextSession);
    setSession(nextSession);
  }

  async function handleVerifyEmployee(input: EmployeeVerifyInput) {
    const nextSession = await verifyEmployeeApi(input);
    writeAuthSession(nextSession);
    setSession(nextSession);
  }

  function logout() {
    clearAuthSession();
    setSession(null);
  }

  const value = useMemo(
    () => ({
      session,
      user: buildAuthenticatedUser(session),
      isAuthenticated: Boolean(session),
      isInitializing,
      login,
      verifyEmployee: handleVerifyEmployee,
      logout,
    }),
    [isInitializing, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
