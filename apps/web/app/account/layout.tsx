import type { ReactNode } from "react";
import { AccountFrame } from "@/components/account/account-frame";
import "./account.css";

export default function AccountLayout({ children }: { children: ReactNode }) {
  return <AccountFrame>{children}</AccountFrame>;
}
