"use client";

import { useState } from "react";
import { Button, CheckIcon } from "@breero/ui";
import { customerApi } from "@/lib/customer/api";

export function QuoteApproval({ quoteId }: { quoteId: string; amountMinor?: number; currency?: string }) {
  const [state, setState] = useState<"idle" | "approving" | "approved" | "error">("idle");

  async function approve() {
    setState("approving");
    try {
      await customerApi.quotes.decide(quoteId, true);
      setState("approved");
    } catch {
      setState("error");
    }
  }

  if (state === "approved") {
    return <div className="approval-success" role="status"><span><CheckIcon size={28}/></span><h2>Quote approved</h2><p>Your approval is saved. No online payment is required or collected at this time.</p><a href="/account/quotes">Return to quotes</a></div>;
  }
  return <div><h2>Approve this work?</h2><p>No additional work begins until you approve. No online payment is required or collected at this time.</p>{state === "error" && <p className="auth-message auth-error" role="alert">We couldn’t complete that request. Nothing was charged.</p>}<Button fullWidth loading={state === "approving"} onClick={approve}>Approve quote</Button></div>;
}
