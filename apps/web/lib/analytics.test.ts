import { afterEach, describe, expect, it, vi } from "vitest";
import { configureAnalytics, track } from "./analytics";
import { configureErrorReporter, reportFrontendError } from "./error-reporting";

describe("platform adapters", () => {
  afterEach(() => { configureAnalytics({ track: () => undefined }); configureErrorReporter({ capture: () => undefined }); });
  it("emits typed funnel events without requiring a vendor", () => {
    const sink = vi.fn(); configureAnalytics({ track: sink });
    track({ name: "booking_started", serviceId: "service-1" });
    expect(sink).toHaveBeenCalledWith({ name: "booking_started", serviceId: "service-1" });
  });
  it("forwards sanitized reporting context", () => {
    const sink = vi.fn(); configureErrorReporter({ capture: sink });
    const error = new Error("failure"); reportFrontendError(error, { route: "/booking", requestId: "req-1" });
    expect(sink).toHaveBeenCalledWith(error, { route: "/booking", requestId: "req-1" });
  });
});
