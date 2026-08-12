"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import type {
  AvailabilitySlot,
  ServiceDetail,
  ServiceQuestion,
} from "@breero/types";
import { ApiError } from "@breero/api-client";
import { bookingApi } from "../../lib/booking-api";
import { serviceCatalog as fallbackCatalog } from "../../lib/booking-catalog";
import { track } from "../../lib/analytics";
type Answers = Record<string, string | string[] | boolean>;
type State = {
  serviceId: string;
  address: string;
  addressId?: string;
  answers: Answers;
  slot?: AvailabilitySlot;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  bookingId?: string;
  bookingKey?: string;
  paymentId?: string;
  paymentKey?: string;
  paymentStatus?: string;
};
const empty: State = {
  serviceId: "",
  address: "",
  answers: {},
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
};
const labels = [
  "Service",
  "Address",
  "Questions",
  "Availability",
  "Details",
  "Review",
  "Payment",
  "Confirmation",
];
export function BookingWizard() {
  const query = useSearchParams();
  const api = useMemo(() => bookingApi(), []);
  const mockMode = process.env.NEXT_PUBLIC_API_MODE === "mock";
  const [step, setStep] = useState(0);
  const [state, setState] = useState<State>(empty);
  const [catalog, setCatalog] = useState<ServiceDetail[]>(
    mockMode ? fallbackCatalog : [],
  );
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const serviceCatalog = mockMode ? fallbackCatalog : catalog;
  const service = serviceCatalog.find((s) => s.id === state.serviceId);
  useEffect(() => {
    if (process.env.NEXT_PUBLIC_API_MODE === "mock") return;
    const controller = new AbortController();
    void api.services
      .list(controller.signal)
      .then((items) =>
        Promise.all(
          items.map((item) => api.services.detail(item.id, controller.signal)),
        ),
      )
      .then(setCatalog)
      .catch(() => setError("Services could not be loaded. Please retry."));
    return () => controller.abort();
  }, [api]);
  useEffect(() => {
    const saved = sessionStorage.getItem("breero-booking");
    if (saved)
      try {
        setState(JSON.parse(saved));
      } catch {}
    else {
      const id = query.get("service");
      if (id) setState((v) => ({ ...v, serviceId: id }));
    }
  }, [query]);
  useEffect(() => {
    sessionStorage.setItem("breero-booking", JSON.stringify(state));
  }, [state]);
  const next = () => {
    setError("");
    setStep((v) => Math.min(7, v + 1));
  };
  const back = () => {
    setError("");
    setStep((v) => Math.max(0, v - 1));
  };
  async function validateAddress() {
    if (!state.address.trim()) {
      setError("Enter the address where you need service.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await api.addresses.validate({ address: state.address });
      if (!result.serviceable || !result.address_id) {
        setError(
          "BREERO does not currently serve this address. Try another address or check back soon.",
        );
        return;
      }
      setState((v) => ({
        ...v,
        address: result.formatted_address,
        addressId: result.address_id!,
      }));
      next();
    } catch {
      setError("We couldn’t validate this address. Check it and try again.");
    } finally {
      setBusy(false);
    }
  }
  async function loadSlots() {
    if (!service || !state.addressId) return;
    setBusy(true);
    setError("");
    try {
      const from = new Date(),
        to = new Date();
      to.setDate(to.getDate() + 14);
      const found = await api.availability.search({
        service_id: service.id,
        address_id: state.addressId,
        date_from: from.toISOString().slice(0, 10),
        date_to: to.toISOString().slice(0, 10),
      });
      setSlots(found);
      if (!found.length)
        setError(
          "No appointments are available in the next two weeks. Try again for updated availability.",
        );
    } catch {
      setError("Availability could not be loaded. Please retry.");
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (step === 3) void loadSlots();
    // loadSlots intentionally reads the latest booking state when the step changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);
  async function submit() {
    if (!service || !state.addressId || !state.slot) return;
    setBusy(true);
    setError("");
    const key = state.bookingKey ?? crypto.randomUUID();
    if (!state.bookingKey) setState((v) => ({ ...v, bookingKey: key }));
    try {
      const booking = await api.bookings.create(
        {
          service_id: service.id,
          address_id: state.addressId,
          customer: {
            first_name: state.firstName,
            last_name: state.lastName,
            email: state.email,
            phone: state.phone,
          },
          window: { start: state.slot.start, end: state.slot.end },
          answers: Object.entries(state.answers).map(
            ([question_id, value]) => ({
              question_id,
              value: Array.isArray(value) ? value.join(",") : String(value),
            }),
          ),
        },
        key,
      );
      track({ name: "booking_submitted", serviceId: service.id });
      setState((v) => ({ ...v, bookingId: booking.id }));
      next();
    } catch (reason) {
      setError(
        reason instanceof ApiError &&
          ["timeout", "network"].includes(reason.kind)
          ? "We could not confirm whether your booking was received. Do not submit again yet—check your account or contact support with this browser session."
          : reason instanceof ApiError && reason.kind === "conflict"
            ? "That arrival window is no longer available. Go back and choose another time."
            : "Your booking wasn’t submitted. Nothing was charged—review the details and try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function pay() {
    if (!state.bookingId) return;
    setBusy(true);
    setError("");
    const key = state.paymentKey ?? crypto.randomUUID();
    if (!state.paymentKey) setState((v) => ({ ...v, paymentKey: key }));
    try {
      const p = await api.payments.createIntent(
        {
          booking_id: state.bookingId,
          amount_minor: Math.round(Number(service?.base_price ?? 0) * 100),
          currency: "EUR",
        },
        key,
      );
      track({ name: "payment_started", bookingId: state.bookingId });
      setState((v) => ({ ...v, paymentId: p.id, paymentStatus: p.status }));
      setStep(7);
    } catch {
      setError(
        "Payment could not be started. Your booking is saved but not confirmed.",
      );
    } finally {
      setBusy(false);
    }
  }
  function requiredDone() {
    return !service?.questions.some(
      (q) =>
        q.required &&
        (state.answers[q.id] === undefined || state.answers[q.id] === ""),
    );
  }
  return (
    <div className="wizard">
      <header className="wizard-head">
        <Link className="brand" href="/">
          BREERO
        </Link>
        <span>
          Step {step + 1} of 8 · {labels[step]}
        </span>
      </header>
      <div className="progress">
        <span style={{ width: `${((step + 1) / 8) * 100}%` }} />
      </div>
      <section className="wizard-body" aria-live="polite">
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {step === 0 && (
          <>
            <p className="eyebrow">Choose a service</p>
            <h1>What can we help with?</h1>
            <div className="choices">
              {serviceCatalog.map((s) => (
                <label className="choice" key={s.id}>
                  <input
                    type="radio"
                    name="service"
                    checked={state.serviceId === s.id}
                    onChange={() =>
                      setState((v) => ({ ...v, serviceId: s.id }))
                    }
                  />
                  <span>
                    <b>{s.name}</b>
                    <br />
                    <small>
                      From €{s.base_price} · {s.duration_minutes} min
                    </small>
                  </span>
                </label>
              ))}
            </div>
            <Actions next={next} disableNext={!state.serviceId} />
          </>
        )}
        {step === 1 && (
          <>
            <p className="eyebrow">Service address</p>
            <h1>Where do you need help?</h1>
            <p>
              BREERO asks the platform to determine serviceability and the
              responsible legal entity.
            </p>
            <div className="field">
              <label htmlFor="address">Full address</label>
              <input
                id="address"
                autoComplete="street-address"
                value={state.address}
                onChange={(e) =>
                  setState((v) => ({ ...v, address: e.target.value }))
                }
                placeholder="Street, city, postcode"
              />
            </div>
            <Actions back={back} next={validateAddress} busy={busy} />
          </>
        )}
        {step === 2 && (
          <>
            <p className="eyebrow">A few details</p>
            <h1>Help us prepare</h1>
            {service?.questions.length ? (
              service.questions.map((q) => (
                <Question
                  key={q.id}
                  question={q}
                  value={state.answers[q.id]}
                  set={(value) =>
                    setState((v) => ({
                      ...v,
                      answers: { ...v.answers, [q.id]: value },
                    }))
                  }
                />
              ))
            ) : (
              <p className="notice">
                No extra questions are required for this service.
              </p>
            )}
            <Actions back={back} next={next} disableNext={!requiredDone()} />
          </>
        )}
        {step === 3 && (
          <>
            <p className="eyebrow">Availability</p>
            <h1>Choose an arrival window</h1>
            {busy ? (
              <p className="loading">Checking available times…</p>
            ) : (
              <div className="slots">
                {slots.map((slot) => (
                  <label className="choice" key={slot.start}>
                    <input
                      type="radio"
                      name="slot"
                      checked={state.slot?.start === slot.start}
                      onChange={() => setState((v) => ({ ...v, slot }))}
                    />
                    <span>
                      <b>
                        {new Date(slot.start).toLocaleDateString(undefined, {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                        })}
                      </b>
                      <br />
                      {new Date(slot.start).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                      –
                      {new Date(slot.end).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </label>
                ))}
              </div>
            )}
            <button
              className="button-secondary"
              type="button"
              onClick={loadSlots}
            >
              Retry / check alternate dates
            </button>
            <Actions back={back} next={next} disableNext={!state.slot} />
          </>
        )}
        {step === 4 && (
          <>
            <p className="eyebrow">Your details</p>
            <h1>Who should we contact?</h1>
            {[
              ["firstName", "First name", "given-name"],
              ["lastName", "Last name", "family-name"],
              ["email", "Email", "email"],
              ["phone", "Phone", "tel"],
            ].map(([key, label, auto]) => (
              <div className="field" key={key}>
                <label htmlFor={key}>{label}</label>
                <input
                  id={key}
                  type={
                    key === "email" ? "email" : key === "phone" ? "tel" : "text"
                  }
                  autoComplete={auto}
                  value={String(state[key as keyof State] ?? "")}
                  onChange={(e) =>
                    setState((v) => ({ ...v, [key]: e.target.value }))
                  }
                />
              </div>
            ))}
            <Actions
              back={back}
              next={next}
              disableNext={
                !state.firstName ||
                !state.lastName ||
                !state.email.includes("@") ||
                !state.phone
              }
            />
          </>
        )}
        {step === 5 && (
          <>
            <p className="eyebrow">Review</p>
            <h1>Check your booking</h1>
            <div className="summary">
              <div>
                <b>Service</b>
                <span>{service?.name}</span>
              </div>
              <div>
                <b>Address</b>
                <span>{state.address}</span>
              </div>
              <div>
                <b>Time</b>
                <span>
                  {state.slot && new Date(state.slot.start).toLocaleString()}
                </span>
              </div>
              <div>
                <b>Starting total</b>
                <span>€{service?.base_price}</span>
              </div>
            </div>
            <p>
              <small>
                Additional work is never added without a separate quote and your
                approval.
              </small>
            </p>
            <Actions
              back={back}
              next={submit}
              busy={busy}
              nextLabel="Submit booking"
            />
          </>
        )}
        {step === 6 && (
          <>
            <p className="eyebrow">Secure payment</p>
            <h1>Complete payment</h1>
            <p>
              Your booking reference is <b>{state.bookingId}</b>. Payment
              confirmation comes from the backend/provider—not the browser
              redirect.
            </p>
            <div className="notice">
              Secure provider handoff · €{service?.base_price} EUR
            </div>
            <Actions
              back={back}
              next={pay}
              busy={busy}
              nextLabel="Continue to payment"
            />
          </>
        )}
        {step === 7 && (
          <>
            <p className="eyebrow">Status check</p>
            <h1>
              {state.paymentStatus === "failed"
                ? "Payment needs attention"
                : "We’re confirming your booking"}
            </h1>
            <p>
              {state.paymentStatus === "failed"
                ? "Your booking is saved, but payment failed. Retry payment or contact support."
                : "Payment is processing. We’ll show confirmed only after BREERO receives authoritative provider status."}
            </p>
            <p className="notice">
              Current status: {state.paymentStatus ?? "pending"}
            </p>
            <Link className="button" href="/">
              Return home
            </Link>
          </>
        )}
      </section>
    </div>
  );
}
function Actions({
  back,
  next,
  busy,
  disableNext,
  nextLabel = "Continue",
}: {
  back?: () => void;
  next: () => void | Promise<void>;
  busy?: boolean;
  disableNext?: boolean;
  nextLabel?: string;
}) {
  return (
    <div className="actions">
      {back ? (
        <button className="button-secondary" type="button" onClick={back}>
          Back
        </button>
      ) : (
        <span />
      )}
      <button
        className="button"
        type="button"
        onClick={next}
        disabled={busy || disableNext}
      >
        {busy ? "Please wait…" : nextLabel}
      </button>
    </div>
  );
}
function Question({
  question,
  value,
  set,
}: {
  question: ServiceQuestion;
  value: Answers[string];
  set: (v: Answers[string]) => void;
}) {
  const id = `q-${question.id}`;
  if (question.question_type === "single_choice")
    return (
      <fieldset className="field">
        <legend className="label">{question.label}</legend>
        {question.options?.map((o) => (
          <label className="choice" key={o.value}>
            <input
              type="radio"
              name={id}
              checked={value === o.value}
              onChange={() => set(o.value)}
            />
            {o.label}
          </label>
        ))}
      </fieldset>
    );
  if (question.question_type === "multi_choice")
    return (
      <fieldset className="field">
        <legend className="label">{question.label}</legend>
        {question.options?.map((o) => (
          <label className="choice" key={o.value}>
            <input
              type="checkbox"
              checked={Array.isArray(value) && value.includes(o.value)}
              onChange={(e) => {
                const a = Array.isArray(value) ? value : [];
                set(
                  e.target.checked
                    ? [...a, o.value]
                    : a.filter((x) => x !== o.value),
                );
              }}
            />
            {o.label}
          </label>
        ))}
      </fieldset>
    );
  if (question.question_type === "boolean")
    return (
      <label className="choice">
        <input
          type="checkbox"
          checked={value === true}
          onChange={(e) => set(e.target.checked)}
        />
        {question.label}
      </label>
    );
  return (
    <div className="field">
      <label htmlFor={id}>
        {question.label}
        {question.required ? " *" : ""}
      </label>
      {question.question_type === "textarea" ? (
        <textarea
          id={id}
          value={String(value ?? "")}
          onChange={(e) => set(e.target.value)}
        />
      ) : (
        <input
          id={id}
          type={question.question_type === "number" ? "number" : "text"}
          value={String(value ?? "")}
          onChange={(e) => set(e.target.value)}
        />
      )}
      <small>{question.help_text}</small>
    </div>
  );
}
