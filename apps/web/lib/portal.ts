"use client";

import type { PortalContext } from "@breero/types";
import { customerApi } from "./customer/api";

const ALLOWED_DASHBOARDS = new Set([
  "/account",
  "/provider",
  "/worker",
  "/ops",
  "/support",
  "/finance",
  "/quality",
  "/trust-safety",
  "/sales",
  "/marketing",
  "/admin",
]);

export async function loadPortalContext(signal?: AbortSignal): Promise<PortalContext> {
  const context = await customerApi.auth.context(signal);
  if (!ALLOWED_DASHBOARDS.has(context.dashboard_path)) {
    throw new Error("Account dashboard is not configured");
  }
  return context;
}

export async function routeToPortal(): Promise<never> {
  const context = await loadPortalContext();
  window.location.replace(context.dashboard_path);
  return new Promise<never>(() => undefined);
}

export function canAccessDepartment(context: PortalContext, department: string): boolean {
  return context.departments.includes(department as PortalContext["departments"][number]);
}
