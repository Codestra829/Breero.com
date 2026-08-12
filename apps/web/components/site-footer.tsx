import { ShieldIcon } from "@breero/ui";
import Link from "next/link";
import { Logo } from "./brand/Logo";

const groups = [
  { title: "Services", links: [["All services", "/services"], ["Plumbing", "/services/plumbing"], ["Electrical", "/services/electrical"], ["Cleaning", "/services/cleaning"]] },
  { title: "Company", links: [["About", "/about"], ["How it works", "/how-it-works"], ["Careers", "/careers"], ["Press", "/press"]] },
  { title: "Support", links: [["Help centre", "/help"], ["Contact", "/contact"], ["FAQ", "/faq"], ["Trust & safety", "/trust"]] },
  { title: "Professionals", links: [["Partner information", "/partners"], ["Professional standards", "/trust"], ["Partner interest", "/partners#interest"]] },
];

export function SiteFooter() {
  return <footer className="site-footer"><div className="footer__inner"><div className="footer__intro"><Logo light/><p>Home services, without the hassle.</p><span className="footer__trust"><ShieldIcon size={18} />Clear booking. Professional support.</span></div><div className="footer__links">{groups.map((group) => <div key={group.title}><h2>{group.title}</h2>{group.links.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}</div>)}</div></div><div className="footer__legal"><span>© {new Date().getFullYear()} BREERO Ltd.</span><div><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link><Link href="/cookies">Cookies</Link><Link href="/accessibility">Accessibility</Link></div></div></footer>;
}
