"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRightIcon, CloseIcon, IconButton, MenuIcon, ShieldIcon, UserIcon } from "@breero/ui";

const links = [
  { href: "/services", label: "Services" },
  { href: "/how-it-works", label: "How it works" },
  { href: "/help", label: "Help" },
];

export function SiteHeader() {
  const [open, setOpen] = useState(false); const pathname = usePathname();
  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [open]);
  return <header className="site-header"><div className="site-header__bar"><Link className="brand" href="/" aria-label="BREERO home"><span className="brand__mark">B</span><span>BREERO</span></Link><nav className="desktop-nav" aria-label="Main navigation">{links.map((link) => <Link key={link.href} href={link.href} aria-current={pathname === link.href ? "page" : undefined}>{link.label}</Link>)}</nav><div className="site-header__actions"><Link className="header-signin" href="/account"><UserIcon size={18} />Sign in</Link><Link className="br-button br-button--primary br-button--sm header-book" href="/services">Book a service <ArrowRightIcon size={17} /></Link><IconButton className="mobile-menu-button" label={open ? "Close menu" : "Open menu"} aria-expanded={open} aria-controls="mobile-navigation" onClick={() => setOpen(!open)}>{open ? <CloseIcon /> : <MenuIcon />}</IconButton></div></div>{open && <div id="mobile-navigation" className="mobile-nav"><nav aria-label="Mobile navigation">{links.map((link) => <Link key={link.href} href={link.href} aria-current={pathname === link.href ? "page" : undefined} onClick={() => setOpen(false)}>{link.label}<ArrowRightIcon size={18} /></Link>)}<Link href="/account" onClick={() => setOpen(false)}><UserIcon size={19} />Sign in</Link></nav><Link className="br-button br-button--primary br-button--lg br-button--full" href="/services" onClick={() => setOpen(false)}>Book a service <ArrowRightIcon /></Link><p><ShieldIcon size={17} />Vetted professionals. Protected bookings.</p></div>}</header>;
}
