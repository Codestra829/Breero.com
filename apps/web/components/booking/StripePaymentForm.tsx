"use client";

import { Elements, PaymentElement, useElements, useStripe } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import { useMemo, useState } from "react";

function PaymentForm({ onSubmitted }: { onSubmitted: () => void }) {
  const stripe = useStripe();
  const elements = useElements();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!stripe || !elements) return;
    setBusy(true);
    setError("");
    const result = await stripe.confirmPayment({ elements, redirect: "if_required" });
    setBusy(false);
    if (result.error) {
      setError(result.error.message ?? "Payment could not be confirmed. Try again.");
      return;
    }
    // Stripe.js completion is not authoritative; the parent now checks the backend.
    onSubmitted();
  }

  return (
    <form onSubmit={submit}>
      <PaymentElement />
      {error && <p className="error" role="alert">{error}</p>}
      <button className="button" disabled={!stripe || busy} type="submit">
        {busy ? "Confirming securely…" : "Pay securely"}
      </button>
    </form>
  );
}

export function StripePaymentForm({
  clientSecret,
  onSubmitted,
}: {
  clientSecret: string;
  onSubmitted: () => void;
}) {
  const key = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
  const stripe = useMemo(() => (key ? loadStripe(key) : null), [key]);
  if (!stripe) {
    return <p className="error" role="alert">Secure payment is not configured. Your booking remains saved.</p>;
  }
  return <Elements stripe={stripe} options={{ clientSecret }}><PaymentForm onSubmitted={onSubmitted} /></Elements>;
}
