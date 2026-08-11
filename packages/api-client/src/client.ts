import type {
  AddressValidation, AddressValidationRequest, AuthSession, AvailabilitySearchRequest,
  AvailabilitySlot, Booking, BookingCreateRequest, CustomerBookingList, CustomerProfile,
  LoginRequest, Payment, PaymentIntentRequest, Quote, RegisterRequest, ServiceDetail,
  ServiceQuestion, ServiceSummary, User, UUID,
} from "@breero/types";
import { ApiTransport, type Transport, type TransportOptions } from "./transport";

export interface BreeroApi {
  auth: { login(input: LoginRequest): Promise<AuthSession>; register(input: RegisterRequest): Promise<AuthSession>; me(signal?: AbortSignal): Promise<User> };
  services: { list(signal?: AbortSignal): Promise<ServiceSummary[]>; detail(id: UUID, signal?: AbortSignal): Promise<ServiceDetail>; questions(id: UUID, signal?: AbortSignal): Promise<ServiceQuestion[]> };
  addresses: { validate(input: AddressValidationRequest, signal?: AbortSignal): Promise<AddressValidation> };
  availability: { search(input: AvailabilitySearchRequest, signal?: AbortSignal): Promise<AvailabilitySlot[]> };
  bookings: { create(input: BookingCreateRequest, idempotencyKey: string, signal?: AbortSignal): Promise<Booking>; mine(signal?: AbortSignal): Promise<CustomerBookingList>; getMine(id: UUID, signal?: AbortSignal): Promise<Booking> };
  payments: { createIntent(input: PaymentIntentRequest, idempotencyKey: string, signal?: AbortSignal): Promise<Payment>; get(id: UUID, signal?: AbortSignal): Promise<Payment> };
  customer: { profile(signal?: AbortSignal): Promise<CustomerProfile>; updateProfile(input: Partial<CustomerProfile>, signal?: AbortSignal): Promise<CustomerProfile> };
  quotes: { list(signal?: AbortSignal): Promise<Quote[]>; get(id: UUID, signal?: AbortSignal): Promise<Quote>; approve(id: UUID, idempotencyKey: string, signal?: AbortSignal): Promise<Quote> };
}

const encoded = (value: string) => encodeURIComponent(value);
export function createBreeroApi(options: TransportOptions): BreeroApi {
  return createApiClient(new ApiTransport(options));
}

export function createApiClient(http: Transport): BreeroApi {
  return {
    auth: {
      login: (body) => http.request("/auth/login", { method: "POST", body, retry: false }),
      register: (body) => http.request("/auth/register", { method: "POST", body, retry: false }),
      me: (signal) => http.request("/auth/me", { signal }),
    },
    services: {
      list: (signal) => http.request("/services", { signal }),
      detail: (id, signal) => http.request(`/services/${encoded(id)}`, { signal }),
      questions: (id, signal) => http.request(`/services/${encoded(id)}/questions`, { signal }),
    },
    addresses: { validate: (body, signal) => http.request("/addresses/validate", { method: "POST", body, signal, retry: false }) },
    availability: { search: (body, signal) => http.request("/availability/search", { method: "POST", body, signal, retry: false }) },
    bookings: {
      create: (body, key, signal) => http.request("/bookings", { method: "POST", body, signal, retry: false, headers: { "Idempotency-Key": key } }),
      mine: (signal) => http.request("/customers/me/bookings", { signal }),
      getMine: (id, signal) => http.request(`/customers/me/bookings/${encoded(id)}`, { signal }),
    },
    payments: {
      createIntent: (body, key, signal) => http.request("payments/intents", { method: "POST", body, signal, retry: false, headers: { "Idempotency-Key": key } }),
      get: (id, signal) => http.request(`payments/${encoded(id)}`, { signal }),
    },
    // These endpoints are intentionally centralized while the backend contract is pending.
    customer: {
      profile: (signal) => http.request("customers/me/profile", { signal }),
      updateProfile: (body, signal) => http.request("customers/me/profile", { method: "PATCH", body, signal, retry: false }),
    },
    quotes: {
      list: (signal) => http.request("customers/me/quotes", { signal }),
      get: (id, signal) => http.request(`customers/me/quotes/${encoded(id)}`, { signal }),
      approve: (id, key, signal) => http.request(`customers/me/quotes/${encoded(id)}/approve`, { method: "POST", signal, retry: false, headers: { "Idempotency-Key": key } }),
    },
  };
}
