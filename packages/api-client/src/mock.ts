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
      mine: (s) => run("bookings", () => ({ items: scenario.bookings ?? [] }), s),
      getMine: (id, s) => run("bookings", () => scenario.bookings?.find((item) => item.id === id) ?? missing(`booking ${id}`), s),
    },
    payments: {
      createIntent: (_input, _key, s) => run("payments", () => scenario.payments?.[0] ?? missing("payment"), s),
      get: (id, s) => run("payments", () => scenario.payments?.find((item) => item.id === id) ?? missing(`payment ${id}`), s),
    },
    customer: {
      profile: (s) => run("customer", () => profile ?? missing("profile"), s),
      updateProfile: (input, s) => run("customer", () => profile = { ...(profile ?? missing("profile")), ...input }, s),
    },
    quotes: {
      list: (s) => run("quotes", () => scenario.quotes ?? [], s),
      get: (id, s) => run("quotes", () => scenario.quotes?.find((item) => item.id === id) ?? missing(`quote ${id}`), s),
      approve: (id, _key, s) => run("quotes", () => ({ ...(scenario.quotes?.find((item) => item.id === id) ?? missing(`quote ${id}`)), status: "APPROVED" }), s),
    },
  };
}
