import { useContext } from "react";

import { ApiFeedbackContext, type ApiFeedbackState } from "./apiFeedbackContext";

export function useApiFeedback(): ApiFeedbackState {
  const context = useContext(ApiFeedbackContext);
  if (!context) {
    throw new Error("useApiFeedback must be used within ApiFeedbackProvider.");
  }
  return context;
}