const defaultApiBaseUrl = "http://127.0.0.1:8000/api/v1";

export function getApiBaseUrl(): string {
  const value = import.meta.env.VITE_API_BASE_URL?.trim();
  return value && value.length > 0 ? value : defaultApiBaseUrl;
}
