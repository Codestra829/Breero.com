"use client";

import { FormEvent, useEffect, useState } from "react";

type FormKind = "service" | "contact" | "provider";
type Service = { id: string; slug: string; name: string; is_active?: boolean };

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://api.breero.com/api/v1";

function value(data: FormData, key: string) {
  return String(data.get(key) ?? "").trim();
}

export function PublicIntakeForm({ kind }: { kind: FormKind }) {
  const [services, setServices] = useState<Service[]>([]);
  const [catalogError, setCatalogError] = useState(false);
  const [state, setState] = useState<"idle" | "sending" | "accepted" | "error">("idle");

  useEffect(() => {
    if (kind !== "service") return;
    const controller = new AbortController();
    fetch(`${apiBase}/services`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("catalog unavailable");
        return response.json() as Promise<Service[]>;
      })
      .then((items) => setServices(items.filter((item) => item.is_active !== false)))
      .catch((error: unknown) => {
        if ((error as { name?: string }).name !== "AbortError") setCatalogError(true);
      });
    return () => controller.abort();
  }, [kind]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    setState("sending");
    const data = new FormData(form);
    const shared = {
      source_url: window.location.href,
      company: value(data, "company"),
    };
    const payload =
      kind === "service"
        ? {
            ...shared,
            name: value(data, "name"),
            email: value(data, "email"),
            phone: value(data, "phone"),
            service_slug: value(data, "service_slug"),
            service_description: value(data, "message"),
            address_line1: value(data, "address_line1"),
            city: value(data, "city"),
            state: "TX",
            postal_code: value(data, "postal_code"),
            requested_timing: value(data, "requested_timing") || undefined,
            contact_preference: value(data, "contact_preference"),
          }
        : kind === "contact"
          ? {
              ...shared,
              name: value(data, "name"),
              email: value(data, "email"),
              phone: value(data, "phone") || undefined,
              category: value(data, "category"),
              subject: value(data, "subject"),
              message: value(data, "message"),
            }
          : {
              ...shared,
              business_name: value(data, "business_name"),
              contact_name: value(data, "contact_name"),
              email: value(data, "email"),
              phone: value(data, "phone"),
              business_website: value(data, "business_website") || undefined,
              service_categories: [value(data, "service_category")],
              city: value(data, "city"),
              state: "TX",
              postal_code: value(data, "postal_code"),
              license_details: value(data, "license_details") || undefined,
              notes: value(data, "message") || undefined,
            };
    const endpoint =
      kind === "service" ? "service-requests" : kind === "contact" ? "contact" : "provider-interest";
    try {
      const response = await fetch(`${apiBase}/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error("submission failed");
      setState("accepted");
      form.reset();
    } catch {
      setState("error");
    }
  }

  return (
    <form className="mk-intake" onSubmit={submit} aria-busy={state === "sending"}>
      <div className="mk-intake__honeypot" aria-hidden="true">
        <label>Company website<input name="company" tabIndex={-1} autoComplete="off" /></label>
      </div>
      {kind === "provider" ? (
        <>
          <label>Business name<input name="business_name" required minLength={2} /></label>
          <label>Contact name<input name="contact_name" required minLength={2} autoComplete="name" /></label>
        </>
      ) : <label>Name<input name="name" required minLength={2} autoComplete="name" /></label>}
      <label>Email<input name="email" type="email" required autoComplete="email" /></label>
      <label>Phone<input name="phone" type="tel" required={kind !== "contact"} autoComplete="tel" /></label>
      {kind === "service" && (
        <>
          <label>Service<select name="service_slug" required disabled={!services.length}>{services.length ? services.map((service) => <option key={service.id} value={service.slug}>{service.name}</option>) : <option>Loading live services…</option>}</select></label>
          {catalogError && <p role="alert">Live services are unavailable right now. Please try again shortly.</p>}
          <label>Street address<input name="address_line1" required autoComplete="street-address" /></label>
          <label>City<input name="city" required autoComplete="address-level2" /></label>
          <label>ZIP code<input name="postal_code" required pattern="[0-9]{5}(-[0-9]{4})?" autoComplete="postal-code" /></label>
          <label>Preferred timing<input name="requested_timing" maxLength={200} placeholder="For example: weekday morning" /></label>
          <label>Contact preference<select name="contact_preference"><option value="email">Email</option><option value="phone">Phone</option><option value="text">Text</option></select></label>
        </>
      )}
      {kind === "contact" && (
        <>
          <label>Category<select name="category"><option value="booking_help">Booking help</option><option value="service_issue">Service issue</option><option value="billing">Billing</option><option value="general">General</option><option value="business">Business</option></select></label>
          <label>Subject<input name="subject" required minLength={3} /></label>
          <label>Message<textarea name="message" required minLength={5} maxLength={4000} /></label>
        </>
      )}
      {kind === "provider" && (
        <>
          <label>Website <span>(optional)</span><input name="business_website" type="url" /></label>
          <label>Primary service<select name="service_category">{["plumbing","electrical","handyman","heating","cooling","appliance-repair","cleaning","locksmith","painting","carpentry","moving-help","home-maintenance"].map((slug) => <option key={slug} value={slug}>{slug.replaceAll("-", " ")}</option>)}</select></label>
          <label>City<input name="city" required autoComplete="address-level2" /></label>
          <label>ZIP code<input name="postal_code" required pattern="[0-9]{5}(-[0-9]{4})?" autoComplete="postal-code" /></label>
          <label>License information <span>(when applicable)</span><input name="license_details" maxLength={1000} /></label>
        </>
      )}
      {(kind === "service" || kind === "provider") && <label>{kind === "service" ? "What do you need help with?" : "Anything else we should know?"}<textarea name="message" required={kind === "service"} minLength={kind === "service" ? 5 : undefined} maxLength={4000} /></label>}
      <p className="mk-intake__disclosure">BREERO coordinates requests with independent service providers. Providers remain responsible for final estimates, scope, pricing, licensing, permits, insurance, workmanship and service performance.</p>
      <button className="mk-button mk-button--primary" type="submit" disabled={state === "sending" || (kind === "service" && !services.length)}>{state === "sending" ? "Sending…" : kind === "provider" ? "Submit interest" : "Send request"}</button>
      <div aria-live="polite">{state === "accepted" && <p className="mk-intake__success">Your request was accepted. This does not yet confirm availability or provider assignment.</p>}{state === "error" && <p role="alert">We could not accept the request. Please retry or email support@breero.com.</p>}</div>
    </form>
  );
}
