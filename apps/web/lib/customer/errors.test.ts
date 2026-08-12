import { describe, expect, it } from "vitest";
import { ApiError } from "@breero/api-client";
import { safeCustomerError } from "./errors";

describe("safeCustomerError", () => {
  it("maps API failures to customer-safe messages", () => {
    const raw = new ApiError("database password leaked", "server", 500);
    expect(safeCustomerError(raw).message).toBe("We could not complete that request. Try again shortly.");
  });

  it("never renders arbitrary exception text", () => {
    expect(safeCustomerError(new Error("raw internal exception")).message).not.toContain("raw internal");
  });
});
