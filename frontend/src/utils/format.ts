export function formatApiBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/$/, "");
}
