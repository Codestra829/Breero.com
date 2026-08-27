"use client";

import { useEffect, useState } from "react";
import { Button, Card, Checkbox, FormField, Input, Select } from "@breero/ui";
import type { AccessAssignmentInput, AccessCatalog, AccessRole, Department, PortalContext, TenantScope } from "@breero/types";
import { customerApi } from "@/lib/customer/api";
import { loadPortalContext } from "@/lib/portal";

const initialAssignment: AccessAssignmentInput = {
  role: "support",
  department: "customer_support",
  tenant_scope: "brand",
  vendor_id: null,
  is_primary: true,
};

const label = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export function AccessAssignmentForm() {
  const [catalog, setCatalog] = useState<AccessCatalog | null>(null);
  const [context, setContext] = useState<PortalContext | null>(null);
  const [userId, setUserId] = useState("");
  const [assignments, setAssignments] = useState<AccessAssignmentInput[]>([initialAssignment]);
  const [state, setState] = useState<"loading" | "idle" | "saving" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([loadPortalContext(controller.signal), customerApi.auth.accessCatalog(controller.signal)])
      .then(([portal, accessCatalog]) => {
        if (!portal.permissions.includes("*") && !portal.permissions.includes("admin.access.manage")) {
          throw new Error("Your account is not authorized to manage access");
        }
        setContext(portal);
        setCatalog(accessCatalog);
        setState("idle");
      })
      .catch((error) => {
        if (!controller.signal.aborted) {
          setMessage(error instanceof Error ? error.message : "Access controls could not be loaded");
          setState("error");
        }
      });
    return () => controller.abort();
  }, []);

  function updateAssignment(index: number, patch: Partial<AccessAssignmentInput>) {
    setAssignments((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item));
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("saving");
    setMessage("");
    try {
      if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(userId)) {
        throw new Error("Enter a valid user UUID");
      }
      if (!assignments.length) throw new Error("Add at least one access assignment");
      if (assignments.filter((item) => item.is_primary).length > 1) throw new Error("Choose only one primary workspace");
      for (const item of assignments) {
        if (item.tenant_scope === "vendor" && !item.vendor_id) throw new Error("Vendor-scoped access requires a vendor UUID");
        if (item.tenant_scope !== "vendor" && item.vendor_id) throw new Error("Vendor UUID is only valid for vendor-scoped access");
      }
      const result = await customerApi.auth.replaceUserAccess(userId, { brand_key: "breero", assignments });
      setMessage(`Access updated for ${result.user.email}. Primary dashboard: ${result.dashboard_path}`);
      setState("success");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Access could not be updated");
      setState("error");
    }
  }

  if (state === "loading") return <Card><p role="status">Loading access controls…</p></Card>;
  if (!catalog || !context) return <Card><p role="alert">{message || "Access controls are unavailable."}</p></Card>;

  return <Card><h2>Department access</h2><p>Replace a user’s BREERO role and department assignments. Credentials remain owned by the configured identity provider.</p><form onSubmit={submit}><FormField label="User UUID" htmlFor="access-user-id" required hint="Use the BREERO user ID, not the Keycloak subject."><Input id="access-user-id" value={userId} onChange={(event) => setUserId(event.target.value.trim())} required /></FormField>{assignments.map((assignment, index) => <Card key={`${index}-${assignment.role}-${assignment.department}`}><FormField label="Role" htmlFor={`role-${index}`} required><Select id={`role-${index}`} value={assignment.role} onChange={(event) => updateAssignment(index, { role: event.target.value as AccessRole })}>{catalog.roles.map((role) => <option value={role} key={role}>{label(role)}</option>)}</Select></FormField><FormField label="Department" htmlFor={`department-${index}`} required><Select id={`department-${index}`} value={assignment.department} onChange={(event) => updateAssignment(index, { department: event.target.value as Department })}>{catalog.departments.map((department) => <option value={department} key={department}>{label(department)}</option>)}</Select></FormField><FormField label="Tenant scope" htmlFor={`scope-${index}`} required><Select id={`scope-${index}`} value={assignment.tenant_scope} onChange={(event) => updateAssignment(index, { tenant_scope: event.target.value as TenantScope, vendor_id: event.target.value === "vendor" ? assignment.vendor_id : null })}>{catalog.tenant_scopes.map((scope) => <option value={scope} key={scope}>{label(scope)}</option>)}</Select></FormField>{assignment.tenant_scope === "vendor" && <FormField label="Vendor UUID" htmlFor={`vendor-${index}`} required><Input id={`vendor-${index}`} value={assignment.vendor_id ?? ""} onChange={(event) => updateAssignment(index, { vendor_id: event.target.value.trim() || null })} required /></FormField>}<Checkbox label="Primary workspace" checked={assignment.is_primary ?? false} onChange={(event) => updateAssignment(index, { is_primary: event.target.checked })}/><Button type="button" variant="ghost" onClick={() => setAssignments((current) => current.filter((_, itemIndex) => itemIndex !== index))} disabled={assignments.length === 1}>Remove assignment</Button></Card>)}<div className="actions"><Button type="button" variant="outline" onClick={() => setAssignments((current) => [...current, { ...initialAssignment, is_primary: false }])}>Add assignment</Button><Button type="submit" loading={state === "saving"}>Save access</Button></div>{message && <p role={state === "error" ? "alert" : "status"}>{message}</p>}</form></Card>;
}
