"use client";

import { useCallback } from "react";
import { useParams } from "next/navigation";
import {
  Badge,
  Card,
  ErrorState,
  LoadingState,
  Price,
  ShieldIcon,
} from "@breero/ui";
import { customerApi } from "@/lib/customer/api";
import { useApiResource } from "@/lib/customer/use-api-resource";

export default function PaymentReceipt() {
  const id = String(useParams<{ id: string }>().id);
  const load = useCallback(
    async (signal: AbortSignal) => {
      return customerApi.customer.payment(id, signal);
    },
    [id],
  );
  const { value: payment, error, retry } = useApiResource(load);
  if (error)
    return (
      <ErrorState
        title="Receipt not available"
        description={error.message}
        onRetry={retry}
      />
    );
  if (!payment) return <LoadingState label="Loading receipt" />;
  return (
    <>
      <a className="account-back" href="/account/payments">
        ← Back to payments
      </a>
      <div className="detail-hero">
        <div>
          <Badge
            variant={payment.status === "captured" ? "success" : "neutral"}
          >
            {payment.status}
          </Badge>
          <h1>Payment receipt</h1>
          <p>Receipt {payment.id}</p>
        </div>
        <div className="detail-hero__amount">
          <small>Amount</small>
          <Price
            amount={payment.amount_minor / 100}
            currency={payment.currency}
          />
        </div>
      </div>
      <Card className="detail-section">
        <h2>Receipt details</h2>
        <div className="detail-list">
          <div className="detail-row">
            <div />
            <div>
              <small>Purpose</small>
              <strong>{payment.payment_purpose.replaceAll("_", " ")}</strong>
            </div>
          </div>
          <div className="detail-row">
            <div />
            <div>
              <small>Payment date</small>
              <strong>
                {new Date(payment.created_at).toLocaleDateString("en-GB", {
                  dateStyle: "long",
                })}
              </strong>
            </div>
          </div>
          <div className="detail-row">
            <div />
            <div>
              <small>Captured</small>
              <strong>
                <Price
                  amount={payment.captured_amount_minor / 100}
                  currency={payment.currency}
                />
              </strong>
            </div>
          </div>
          <div className="detail-row">
            <div />
            <div>
              <small>Refunded</small>
              <strong>
                <Price
                  amount={payment.refunded_amount_minor / 100}
                  currency={payment.currency}
                />
              </strong>
            </div>
          </div>
        </div>
        <p className="safe-payment-note">
          <ShieldIcon size={18} />
          This receipt excludes provider secrets, internal margin, and
          professional compensation.
        </p>
        <button
          className="br-button br-button--outline br-button--md"
          type="button"
          onClick={() => window.print()}
        >
          Print receipt
        </button>
      </Card>
    </>
  );
}
