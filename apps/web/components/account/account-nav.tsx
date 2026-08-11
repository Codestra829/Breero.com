"use client";

import { usePathname } from "next/navigation";
import { CalendarIcon, ChevronDownIcon, HomeIcon, UserIcon } from "@breero/ui";

const links = [
  { href: "/account", label: "Overview", icon: <HomeIcon /> },
  { href: "/account/bookings", label: "Bookings", icon: <CalendarIcon /> },
  { href: "/account/quotes", label: "Quotes", icon: <QuoteIcon /> },
  { href: "/account/payments", label: "Payments", icon: <CardIcon /> },
  { href: "/account/profile", label: "Profile & settings", icon: <UserIcon /> },
];

export function AccountNav() {
  const pathname = usePathname();
  return <><aside className="account-nav"><p>My account</p><nav aria-label="Account navigation">{links.map((link) => { const active = link.href === "/account" ? pathname === link.href : pathname.startsWith(link.href); return <a key={link.href} href={link.href} aria-current={active ? "page" : undefined}>{link.icon}<span>{link.label}</span>{link.href === "/account/quotes" && <b aria-label="1 pending quote">1</b>}</a>; })}</nav><div className="account-nav__help"><strong>Need a hand?</strong><span>Our support team is here every day.</span><a href="/help">Get support</a></div></aside><div className="account-mobile-nav"><label htmlFor="account-section">Account section</label><span><select id="account-section" value={links.find((link) => link.href === "/account" ? pathname === link.href : pathname.startsWith(link.href))?.href ?? "/account"} onChange={(event) => window.location.assign(event.target.value)}>{links.map((link) => <option key={link.href} value={link.href}>{link.label}</option>)}</select><ChevronDownIcon /></span></div></>;
}

function QuoteIcon() { return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Z"/><path d="M9 8h6M9 12h6"/></svg>; }
function CardIcon() { return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/></svg>; }
