import { ApiError } from "@breero/api-client";

const messages: Record<string, string> = {
  validation: "Some information needs your attention. Check the form and try again.",
  authentication: "Your session has expired. Sign in again to continue.",
  forbidden: "You do not have permission to view this information.",
  not_found: "We could not find that information.",
  conflict: "This information changed while you were working. Refresh and try again.",
  rate_limit: "Too many requests were made. Wait a moment and try again.",
  unavailable: "This service is temporarily unavailable. Try again shortly.",
  server: "We could not complete that request. Try again shortly.",
  network: "We could not reach BREERO. Check your connection and try again.",
  timeout: "The request took too long. Check your connection and try again.",
  cancelled: "The request was cancelled.",
  unknown: "We could not complete that request. Please try again.",
};

export function safeCustomerError(reason: unknown): Error {
  if (reason instanceof ApiError) return new Error(messages[reason.kind] ?? messages.unknown);
  return new Error("We could not complete that request. Please try again.");
}
