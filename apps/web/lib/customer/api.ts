"use client";

import { createConfiguredApi } from "@breero/api-client";
import { bookings, payments, profile, quotes } from "./data";

export const customerApi = createConfiguredApi(
  { NEXT_PUBLIC_API_MODE: process.env.NEXT_PUBLIC_API_MODE ?? "mock", NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL },
  {
    getAccessToken: () => window.localStorage.getItem("breero_access_token"),
    onUnauthorized: () => { window.location.assign("/account/session-expired"); },
    mock: { bookings, payments, profile, quotes, latencyMs: 450 },
  },
);
