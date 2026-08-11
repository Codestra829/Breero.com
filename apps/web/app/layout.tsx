import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./marketplace.css";
export const metadata: Metadata = { title: { default: "BREERO | Home services, simply booked", template: "%s | BREERO" }, description: "Book trusted home-service professionals with clear pricing and convenient time windows." };
export default function Layout({ children }: { children: ReactNode }) { return <html lang="en"><body>{children}</body></html>; }
