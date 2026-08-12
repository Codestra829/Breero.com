"use client";

import { useState } from "react";
import { Button, CheckIcon } from "@breero/ui";
import { customerApi } from "@/lib/customer/api";

export function QuoteApproval({ quoteId, amountMinor, currency }: { quoteId: string; amountMinor: number; currency: string }) {
  const [state, setState] = useState<"idle" | "approving" | "approved" | "payment" | "ready" | "error">("idle");
  async function approve() {
    setState("approving");
    try { await customerApi.quotes.approve(quoteId, crypto.randomUUID()); setState("approved"); }
    catch { setState("error"); }
  }
  async function preparePayment() {
    setState("payment");
    try {
      await customerApi.payments.createIntent({ quote_id: quoteId, payment_purpose: "ADDITIONAL_WORK", amount_minor: amountMinor, currency }, crypto.randomUUID());
      setState("ready");
    } catch { setState("error"); }
  }
  if (state === "approved" || state === "payment" || state === "ready") return <div className="approval-success" role="status"><span><CheckIcon size={28}/></span><h2>{state === "ready" ? "Payment authorization ready" : "Quote approved"}</h2><p>{state === "ready" ? "The payment has been created. Final confirmation remains authoritative on the server." : "Your approval is saved. Continue to prepare the secure additional-payment step."}</p>{state !== "ready" && <Button fullWidth loading={state === "payment"} onClick={preparePayment}>Continue to payment</Button>}<a href="/account/quotes">Return to quotes</a></div>;
  return <div><h2>Approve this work?</h2><p>No additional work begins until you approve. Payment confirmation is always checked with BREERO.</p>{state === "error" && <p className="auth-message auth-error" role="alert">We couldn’t complete that request. Nothing was charged.</p>}<Button fullWidth loading={state === "approving"} onClick={approve}>Approve quote</Button></div>;
}
