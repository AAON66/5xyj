import { createContext } from "react";

import type { ApiClientError } from "../services/api";

export interface ApiFeedbackState {
  pendingRequests: number;
  lastError: ApiClientError | null;
  clearError: () => void;
}

export const ApiFeedbackContext = createContext<ApiFeedbackState | null>(null);