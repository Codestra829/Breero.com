import { readFileSync } from "node:fs";

const document = JSON.parse(readFileSync(new URL("../apps/api/openapi.json", import.meta.url), "utf8"));
const required = {
  "/api/v1/auth/login": ["post"],
  "/api/v1/auth/register": ["post"],
  "/api/v1/auth/refresh": ["post"],
  "/api/v1/auth/logout": ["post"],
  "/api/v1/auth/logout-all": ["post"],
  "/api/v1/auth/password/forgot": ["post"],
  "/api/v1/auth/password/reset": ["post"],
  "/api/v1/auth/email/verify": ["post"],
  "/api/v1/services": ["get"],
  "/api/v1/services/{service_id}": ["get"],
  "/api/v1/services/{service_id}/questions": ["get"],
  "/api/v1/addresses/validate": ["post"],
  "/api/v1/availability/search": ["post"],
  "/api/v1/bookings": ["post"],
  "/api/v1/payments/intents": ["post"],
  "/api/v1/payments/{payment_id}": ["get"],
  "/api/v1/customer/profile": ["get", "patch"],
  "/api/v1/customer/addresses": ["get", "post"],
  "/api/v1/customer/addresses/{address_id}": ["patch", "delete"],
  "/api/v1/customer/bookings": ["get"],
  "/api/v1/customer/bookings/{booking_id}": ["get"],
  "/api/v1/customer/quotes": ["get"],
  "/api/v1/customer/quotes/{quote_id}": ["get"],
  "/api/v1/customer/quotes/{quote_id}/decision": ["post"],
  "/api/v1/customer/payments": ["get"],
};

const missing = [];
for (const [path, methods] of Object.entries(required)) {
  for (const method of methods) if (!document.paths?.[path]?.[method]) missing.push(`${method.toUpperCase()} ${path}`);
}
if (missing.length) {
  console.error(`Frontend API contract is missing:\n${missing.join("\n")}`);
  process.exit(1);
}

const purposes = document.components?.schemas?.PaymentPurpose?.enum ?? [];
for (const purpose of ["BOOKING_DIAGNOSTIC", "QUOTE_ADDITIONAL_WORK"]) {
  if (!purposes.includes(purpose)) {
    console.error(`Frontend API contract is missing payment purpose ${purpose}`);
    process.exit(1);
  }
}

console.log(`Frontend API contract verified: ${Object.keys(required).length} paths and payment purposes.`);
