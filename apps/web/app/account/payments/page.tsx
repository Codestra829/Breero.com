"use client";

import { useCallback } from "react";
import { Badge, Card, EmptyState, ErrorState, LoadingState, Price, ShieldIcon, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@breero/ui";
import type { CustomerPayment } from "@breero/types";
import { AccountPageHeader } from "@/components/account/page-header";
import { customerApi } from "@/lib/customer/api";
import { useApiResource } from "@/lib/customer/use-api-resource";

export default function PaymentsPage() {
  const load = useCallback(async (signal: AbortSignal) => (await customerApi.customer.payments(undefined, signal)).items, []);
  const { value: payments, error, retry } = useApiResource<CustomerPayment[]>(load);
  const total = payments?.filter((payment) => payment.status === "CAPTURED").reduce((sum, payment) => sum + payment.captured_amount_minor, 0) ?? 0;
  return <><AccountPageHeader eyebrow="Receipts & refunds" title="Payments" description="A customer-safe record of payments made through BREERO."/>{error ? <ErrorState title="Payments aren’t available" description={error.message} onRetry={retry}/> : !payments ? <LoadingState label="Loading payment history"/> : <div className="account-grid payment-summary"><Card className="account-col-4 metric-card"><span><ShieldIcon/></span><strong>{new Intl.NumberFormat("en-GB", { style: "currency", currency: payments[0]?.currency ?? "EUR" }).format(total / 100)}</strong><p>Completed payments shown</p></Card><Card className="account-col-8"><div className="safe-payment-note"><ShieldIcon/><div><strong>Your payment details stay private</strong><p>We show customer-safe transaction details only—never provider secrets, internal margin, or professional compensation.</p></div></div></Card><div className="account-col-12">{payments.length ? <Table><TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Purpose</TableHead><TableHead>Status</TableHead><TableHead>Amount</TableHead><TableHead>Refunded</TableHead></TableRow></TableHeader><TableBody>{payments.map((payment) => <TableRow key={payment.id}><TableCell>{new Date(payment.created_at).toLocaleDateString("en-GB", { dateStyle: "medium" })}</TableCell><TableCell>{payment.purpose.replaceAll("_", " ")}</TableCell><TableCell><Badge variant={payment.status === "CAPTURED" ? "success" : payment.status.includes("FAIL") ? "danger" : "neutral"}>{payment.status}</Badge></TableCell><TableCell><Price amount={payment.amount_minor / 100} currency={payment.currency}/></TableCell><TableCell><Price amount={payment.refunded_amount_minor / 100} currency={payment.currency}/></TableCell></TableRow>)}</TableBody></Table> : <EmptyState title="No payments yet" description="Completed charges and refunds will appear here."/>}</div></div>}</>;
}
