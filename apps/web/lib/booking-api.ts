import { createConfiguredApi, type BreeroApi } from "@breero/api-client";
import { createMockBreeroApi } from "@breero/api-client/mock";
import type { AddressValidation, AvailabilitySlot, BookingCreateResponse, ServiceDetail } from "@breero/types";
import { serviceCatalog } from "./booking-catalog";

const futureSlots = (): AvailabilitySlot[] => Array.from({ length: 6 }, (_, index) => {
  const date = new Date(); date.setUTCDate(date.getUTCDate() + 1 + Math.floor(index / 2)); date.setUTCHours(index % 2 ? 13 : 9, 0, 0, 0);
  return { start: date.toISOString(), end: new Date(date.getTime() + 2 * 60 * 60 * 1000).toISOString(), remaining_capacity: index % 3 + 1 };
});

const mockAddress: AddressValidation = { serviceable: true, formatted_address: "1600 Pennsylvania Avenue NW, Washington, DC 20500", address_id: "address-demo", service_area_id: "washington-dc", legal_entity_code: "BREERO-US", timezone: "America/New_York", manual_dispatch_required: false };
const mockBooking: BookingCreateResponse = { id: "booking-demo", reference: "BR-240811", status: "TENTATIVE_HOLD", total_amount: "0.00", currency: "USD", window_start: futureSlots()[0]!.start, window_end: futureSlots()[0]!.end, payment_required: false, guest_confirmation_token: "mock-guest-confirmation-token-that-is-long-enough" };

export function bookingApi(): BreeroApi {
  if (process.env.NEXT_PUBLIC_API_MODE !== "mock") return createConfiguredApi({ NODE_ENV: process.env.NODE_ENV, NEXT_PUBLIC_API_MODE: process.env.NEXT_PUBLIC_API_MODE, NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_API_TIMEOUT_MS: process.env.NEXT_PUBLIC_API_TIMEOUT_MS, NEXT_PUBLIC_E2E_ALLOW_MOCK: process.env.NEXT_PUBLIC_E2E_ALLOW_MOCK });
  const api = createMockBreeroApi({ services: serviceCatalog as ServiceDetail[], address: mockAddress, slots: futureSlots(), bookings: [mockBooking], bookingCreateResponse: mockBooking, payments: [] });
  return {
    ...api,
    addresses: { validate: async (input, signal) => {
      if (signal?.aborted) throw signal.reason;
      if (/api failure/i.test(input.address)) throw new Error("Simulated API failure");
      if (/outside area/i.test(input.address)) return { ...mockAddress, serviceable: false, address_id: "manual-address-demo", service_area_id: null, legal_entity_code: null, manual_dispatch_required: true };
      return { ...mockAddress, formatted_address: input.address };
    } },
    availability: { search: async (input, signal) => input.service_id === "handyman" ? [] : api.availability.search(input, signal) },
  };
}
