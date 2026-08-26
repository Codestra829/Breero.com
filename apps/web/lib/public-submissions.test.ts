import { describe, expect, it, vi } from "vitest";
import {
  endpointForSubmission,
  prepareSubmissionAttempt,
  stableSerialize,
  submissionErrorFromResponse,
} from "./public-submissions";

describe("public submission client", () => {
  it("serializes equivalent payloads consistently", () => {
    expect(stableSerialize({ b: 2, a: { d: 4, c: 3 } })).toBe(
      stableSerialize({ a: { c: 3, d: 4 }, b: 2 }),
    );
  });

  it("reuses one idempotency key for a same-payload retry", () => {
    const createKey = vi.fn()
      .mockReturnValueOnce("first-key")
      .mockReturnValueOnce("second-key");

    const first = prepareSubmissionAttempt(null, { email: "person@example.com", name: "Person" }, createKey);
    const retry = prepareSubmissionAttempt(first, { name: "Person", email: "person@example.com" }, createKey);

    expect(retry).toBe(first);
    expect(retry.idempotencyKey).toBe("first-key");
    expect(createKey).toHaveBeenCalledTimes(1);
  });

  it("rotates the idempotency key when the payload changes", () => {
    const createKey = vi.fn()
      .mockReturnValueOnce("first-key")
      .mockReturnValueOnce("second-key");

    const first = prepareSubmissionAttempt(null, { message: "Original" }, createKey);
    const changed = prepareSubmissionAttempt(first, { message: "Updated" }, createKey);

    expect(changed.idempotencyKey).toBe("second-key");
    expect(createKey).toHaveBeenCalledTimes(2);
  });

  it("preserves correlation and retry metadata from an API error", async () => {
    const response = new Response(
      JSON.stringify({ error: { code: "RATE_LIMITED", message: "Try again shortly" } }),
      {
        status: 429,
        headers: {
          "content-type": "application/json",
          "retry-after": "60",
          "x-correlation-id": "correlation-123",
        },
      },
    );

    const error = await submissionErrorFromResponse(response);

    expect(error.message).toBe("Try again shortly");
    expect(error.code).toBe("RATE_LIMITED");
    expect(error.retryAfterSeconds).toBe(60);
    expect(error.correlationId).toBe("correlation-123");
  });

  it("does not expose an upstream 500 message", async () => {
    const response = new Response(
      JSON.stringify({ message: "database password and stack detail" }),
      { status: 500, headers: { "content-type": "application/json" } },
    );

    const error = await submissionErrorFromResponse(response);

    expect(error.message).not.toContain("database password");
    expect(error.status).toBe(500);
  });

  it("maps every public form to a real proxy endpoint", () => {
    expect(endpointForSubmission("service")).toBe("service-requests");
    expect(endpointForSubmission("contact")).toBe("contact");
    expect(endpointForSubmission("provider")).toBe("provider-interest");
  });
});
