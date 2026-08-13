import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const wizard = readFileSync(join(process.cwd(), "components/booking/BookingWizard.tsx"), "utf8");

describe("quote-only scheduling launch", () => {
  it("does not invoke Stripe or a guest payment API", () => {
    expect(wizard).not.toContain("StripePaymentForm");
    expect(wizard).not.toContain("prepareGuestPayment");
    expect(wizard).not.toContain("Continue to payment");
  });

  it("states the operator-confirmation and no-payment boundaries", () => {
    expect(wizard).toContain("No online payment is required or collected");
    expect(wizard).toContain("authorized operator confirmation");
    expect(wizard).toContain("PENDING_MANUAL_DISPATCH");
  });
});
