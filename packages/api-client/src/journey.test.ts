import { describe, expect, it } from "vitest";
import { createMockBreeroApi } from "./mock";

describe("mock booking journey", () => {
  it("supports the quote-only funnel through operator-confirmed scheduling", async () => {
    const api = createMockBreeroApi({
      services: [{ id: "svc", slug: "cleaning", name: "Cleaning", description: null, base_price: "89.00", duration_minutes: 120, questions: [] }],
      address: { serviceable: true, formatted_address: "1 Main St", address_id: "addr", service_area_id: "area", legal_entity_code: "BREERO_US", timezone: "America/New_York", manual_dispatch_required: false },
      slots: [{ start: "2026-08-12T09:00:00Z", end: "2026-08-12T11:00:00Z", remaining_capacity: 2 }],
      bookings: [{ id: "booking", reference: "BR-100", status: "TENTATIVE_HOLD", total_amount: "0.00", currency: "USD", window_start: "2026-08-12T09:00:00Z", window_end: "2026-08-12T11:00:00Z", payment_required: false }],
      bookingCreateResponse: { id: "booking", reference: "BR-100", status: "TENTATIVE_HOLD", total_amount: "0.00", currency: "USD", window_start: "2026-08-12T09:00:00Z", window_end: "2026-08-12T11:00:00Z", payment_required: false, guest_confirmation_token: "test-guest-token" },
      payments: [],
    });
    const service = (await api.services.list())[0]!;
    const address = await api.addresses.validate({ address: "1 Main St" });
    const slot = (await api.availability.search({ service_id: service.id, address_id: address.address_id!, date_from: "2026-08-12", date_to: "2026-08-12" }))[0]!;
    const booking = await api.bookings.create({ service_id: service.id, address_id: address.address_id!, customer: { first_name: "Ada", last_name: "Lovelace", email: "ada@example.com", phone: "+4912345" }, window: slot, answers: [] }, "booking-test-100");
    const confirmation = await api.bookings.guestConfirmation(booking.id, "test-guest-token");
    expect({ service: service.slug, serviceable: address.serviceable, booking: booking.status, paymentRequired: confirmation.payment_required }).toEqual({ service: "cleaning", serviceable: true, booking: "TENTATIVE_HOLD", paymentRequired: false });
  });
});
