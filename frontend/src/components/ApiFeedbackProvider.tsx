import { useEffect, useRef, useState, type PropsWithChildren } from "react";
import { App } from "antd";

import { ApiFeedbackContext } from "../hooks/apiFeedbackContext";
import { ApiClientError, attachApiInterceptors } from "../services/api";

export function ApiFeedbackProvider({ children }: PropsWithChildren) {
  const [pendingRequests, setPendingRequests] = useState(0);
  const [lastError, setLastError] = useState<ApiClientError | null>(null);
  const { message } = App.useApp();
  const lastErrorRef = useRef<ApiClientError | null>(null);

  useEffect(() => {
    return attachApiInterceptors({
      onRequestStart: () => {
        setPendingRequests((current) => current + 1);
      },
      onRequestEnd: () => {
        setPendingRequests((current) => Math.max(0, current - 1));
      },
      onError: (error) => {
        setLastError(error);
      },
    });
  }, []);

  useEffect(() => {
    if (lastError && lastError !== lastErrorRef.current) {
      lastErrorRef.current = lastError;
      message.error(lastError.message);
    }
  }, [lastError, message]);

  return (
    <ApiFeedbackContext.Provider
      value={{
        pendingRequests,
        lastError,
        clearError: () => {
          setLastError(null);
        },
      }}
    >
      {children}
    </ApiFeedbackContext.Provider>
  );
}
