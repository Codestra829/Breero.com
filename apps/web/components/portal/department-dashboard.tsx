"use client";

import { useCallback, useEffect } from "react";
import { Badge, Card, ErrorState, LoadingState, ShieldIcon } from "@breero/ui";
import type { Department, PortalContext } from "@breero/types";
import { useApiResource } from "@/lib/customer/use-api-resource";
import { canAccessDepartment, loadPortalContext } from "@/lib/portal";

export interface WorkspaceModule {
  title: string;
  description: string;
  permission: string;
  href?: string;
}

export interface DepartmentDashboardProps {
  department: Department | Department[];
  eyebrow: string;
  title: string;
  description: string;
  modules: WorkspaceModule[];
}

export function DepartmentDashboard({ department, eyebrow, title, description, modules }: DepartmentDashboardProps) {
  const load = useCallback((signal: AbortSignal): Promise<PortalContext> => loadPortalContext(signal), []);
  const { value: context, error, retry } = useApiResource(load);
  const allowedDepartments = Array.isArray(department) ? department : [department];
  const authorized = context ? allowedDepartments.some((item) => canAccessDepartment(context, item)) : false;

  useEffect(() => {
    if (context && !allowedDepartments.some((item) => canAccessDepartment(context, item))) {
      window.location.replace(context.dashboard_path);
    }
  }, [context, allowedDepartments]);

  if (error) return <div className="shell market-section"><ErrorState title="We couldn’t load your workspace" description={error.message} onRetry={retry}/></div>;
  if (!context) return <div className="shell market-section"><LoadingState label="Loading your authorized workspace"/></div>;
  if (!authorized) return <div className="shell market-section"><LoadingState label="Routing to your authorized workspace"/></div>;

  const available = modules.filter((module) => context.permissions.includes("*") || context.permissions.includes(module.permission));
  return <div className="marketplace-page"><section className="shell market-section"><p className="market-eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p><div className="hero-panel"><p><ShieldIcon size={18}/> Signed in as <strong>{context.user.full_name}</strong></p><p>{context.departments.join(" · ")} · {context.identity_mode === "keycloak" ? "Secure SSO" : "Local development identity"}</p></div></section><section className="shell market-section"><div className="section-heading"><div><p className="market-eyebrow">Authorized modules</p><h2>Your workspace</h2></div><Badge variant="brand">{available.length} modules</Badge></div>{available.length ? <div className="service-list">{available.map((module) => module.href ? <a className="service" href={module.href} key={module.permission}><strong>{module.title}</strong><p>{module.description}</p><span className="arrow">Open module →</span></a> : <Card className="service" key={module.permission}><strong>{module.title}</strong><p>{module.description}</p><span className="arrow">Access enabled</span></Card>)}</div> : <Card><h2>No modules assigned</h2><p>Your account is valid, but no department permissions are currently assigned. Contact an administrator.</p></Card>}</section></div>;
}
