import type { BreeroApi } from "./client";
import type { AddressValidation, AuthSession, AvailabilitySlot, Booking, CustomerProfile, Payment, Quote, ServiceDetail, ServiceSummary, User } from "@breero/types";

export interface MockScenario {
  services?: ServiceDetail[]; address?: AddressValidation; slots?: AvailabilitySlot[];
  session?: AuthSession; bookings?: Booking[]; payments?: Payment[]; quotes?: Quote[]; profile?: CustomerProfile;
  latencyMs?: number; fail?: Partial<Record<keyof BreeroApi, Error>>;
}
const wait = (ms: number, signal?: AbortSignal) => new Promise<void>((resolve, reject) => {
  if (signal?.aborted) return reject(signal.reason);
  const id = setTimeout(resolve, ms);
  signal?.addEventListener("abort", () => { clearTimeout(id); reject(signal.reason); }, { once: true });
});
const missing = (name: string): never => { throw new Error(`Mock scenario is missing ${name}`); };

export function createMockBreeroApi(scenario: MockScenario = {}): BreeroApi {
  let profile = scenario.profile;
  const run = async <T>(domain: keyof BreeroApi, value: () => T, signal?: AbortSignal): Promise<T> => {
    await wait(scenario.latencyMs ?? 0, signal);
    if (scenario.fail?.[domain]) throw scenario.fail[domain];
    return value();
  };
  return {
    auth: {
      login: () => run("auth", () => scenario.session ?? missing("session")),
      register: () => run("auth", () => scenario.session ?? missing("session")),
      refresh: () => run("auth", () => scenario.session ?? missing("session")),
      logout: () => run("auth", () => undefined),
      logoutAll: (s) => run("auth", () => undefined, s),
      forgotPassword: () => run("auth", () => ({ message: "If the account exists, reset instructions have been sent" })),
      resetPassword: () => run("auth", () => ({ message: "Password reset" })),
      changePassword: () => run("auth", () => ({ message: "Password changed; active sessions revoked" })),
      verifyEmail: () => run("auth", () => ({ message: "Email verified" })),
      resendVerification: (s) => run("auth", () => ({ message: "Verification sent if required" }), s),
      me: (s) => run<User>("auth", () => scenario.session?.user ?? missing("session.user"), s),
    },
    services: {
      list: (s) => run<ServiceSummary[]>("services", () => scenario.services ?? [], s),
      detail: (id, s) => run("services", () => scenario.services?.find((item) => item.id === id) ?? missing(`service ${id}`), s),
      questions: (id, s) => run("services", () => scenario.services?.find((item) => item.id === id)?.questions ?? missing(`service ${id}`), s),
    },
    addresses: { validate: (_input, s) => run("addresses", () => scenario.address ?? missing("address"), s) },
    availability: { search: (_input, s) => run("availability", () => scenario.slots ?? [], s) },
    bookings: {
      create: (_input, _key, s) => run("bookings", () => scenario.bookings?.[0] ?? missing("booking"), s),
      mine: (_params, s) => run("bookings", () => ({ items: scenario.bookings ?? [], total: scenario.bookings?.length ?? 0, page: 1, page_size: 20 }), s),
      getMine: (id, s) => run("bookings", () => scenario.bookings?.find((item) => item.id === id) ?? missing(`booking ${id}`), s),
    },
    payments: {
      createIntent: (_input, _key, s) => run("payments", () => scenario.payments?.[0] ?? missing("payment"), s),
      get: (id, s) => run("payments", () => scenario.payments?.find((item) => item.id === id) ?? missing(`payment ${id}`), s),
    },
    customer: {
      profile: (s) => run("customer", () => profile ?? missing("profile"), s),
      updateProfile: (input, s) => run("customer", () => profile = { ...(profile ?? missing("profile")), ...input }, s),
      addresses: (s) => run("customer", () => [], s),
      addAddress: (input, s) => run("customer", () => ({ id: "mock-address", ...input }), s),
      updateAddress: (id, input, s) => run("customer", () => ({ id, ...input }), s),
      deleteAddress: (_id, s) => run("customer", () => undefined, s),
      payments: (_params, s) => run("customer", () => {
        const items = (scenario.payments ?? []).map((payment) => ({
          id: payment.id, purpose: payment.payment_purpose ?? "BOOKING_DIAGNOSTIC", status: payment.status,
          amount_minor: payment.amount_minor, captured_amount_minor: payment.captured_amount_minor,
          refunded_amount_minor: payment.status === "refunded" ? payment.amount_minor : 0,
          currency: payment.currency, created_at: payment.created_at,
        }));
        return { items, total: items.length, page: 1, page_size: 20 };
      }, s),
    },
    quotes: {
      list: (_params, s) => run("quotes", () => ({ items: scenario.quotes ?? [], total: scenario.quotes?.length ?? 0, page: 1, page_size: 20 }), s),
      get: (id, s) => run("quotes", () => scenario.quotes?.find((item) => item.id === id) ?? missing(`quote ${id}`), s),
      decide: (id, approve, s) => run("quotes", () => ({ ...(scenario.quotes?.find((item) => item.id === id) ?? missing(`quote ${id}`)), status: approve ? "APPROVED" : "DECLINED" }), s),
      approve: (id, _key, s) => run("quotes", () => ({ ...(scenario.quotes?.find((item) => item.id === id) ?? missing(`quote ${id}`)), status: "APPROVED" }), s),
    },
  };
}
