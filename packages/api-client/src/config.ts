export interface PublicApiConfig { apiBaseUrl: string; mode: "live" | "mock"; timeoutMs: number }

export function readPublicApiConfig(env: Record<string, string | undefined>): PublicApiConfig {
  const apiBaseUrl = env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
  const mode = env.NEXT_PUBLIC_API_MODE === "mock" ? "mock" : "live";
  const timeoutMs = Number(env.NEXT_PUBLIC_API_TIMEOUT_MS ?? "12000");
  if (!/^https?:\/\//.test(apiBaseUrl)) throw new Error("NEXT_PUBLIC_API_BASE_URL must be an absolute HTTP(S) URL");
  if (!Number.isFinite(timeoutMs) || timeoutMs < 1000 || timeoutMs > 60000) throw new Error("NEXT_PUBLIC_API_TIMEOUT_MS must be between 1000 and 60000");
  return { apiBaseUrl, mode, timeoutMs };
}
