"use client";

import { useState } from "react";
import { Button, CheckIcon, Checkbox, ShieldIcon } from "@breero/ui";
import { customerApi } from "@/lib/customer/api";

export function QuoteApproval({ quoteId, requiresPayment }: { quoteId: string; requiresPayment?: boolean }) {
  const [agreed,setAgreed]=useState(false);const [state,setState]=useState<"idle"|"loading"|"success"|"error">("idle");
  function approve(){setState("loading");void customerApi.quotes.approve(quoteId,crypto.randomUUID()).then(()=>setState("success")).catch(()=>setState("error"));}
  if(state==="success")return <div className="approval-success" role="status"><span><CheckIcon size={28}/></span><h2>Quote approved</h2><p>{requiresPayment?"Your approval is saved. Continue to the secure payment step to confirm the work.":"We’ve told your professional. Your booking details will update shortly."}</p>{requiresPayment&&<Button fullWidth>Continue to payment</Button>}<a href="/account/bookings">Return to bookings</a></div>;
  return <><h2>Ready to approve?</h2><p>Approving confirms the work and quoted total shown here.</p><Checkbox label="I’ve reviewed the work and terms" checked={agreed} onChange={(event)=>setAgreed(event.target.checked)}/>{state==="error"&&<p className="auth-message auth-error" role="alert">We couldn’t approve this quote. Nothing was charged. Please try again.</p>}<Button fullWidth size="lg" disabled={!agreed} loading={state==="loading"} onClick={approve}>Approve quote</Button><p className="safe-payment-note"><ShieldIcon size={17}/>Approval uses a unique request key, so retrying won’t approve twice.</p></>;
}
