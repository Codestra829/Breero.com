import type { Metadata } from "next";
import { DM_Sans, Fraunces } from "next/font/google";
import "@breero/ui/styles.css";
import "./globals.css";
import "./marketplace.css";
import { AppShell } from "@/components/app-shell";

const sans = DM_Sans({ subsets: ["latin"], variable: "--font-br-sans", display: "swap" });
const display = Fraunces({ subsets: ["latin"], variable: "--font-br-display", display: "swap" });

export const metadata: Metadata = { title: { default: "BREERO — Home services, handled", template: "%s | BREERO" }, description: "Book trusted home-service professionals with clear prices and protected support." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" className={`${sans.variable} ${display.variable}`}><body><AppShell>{children}</AppShell></body></html>;
}
