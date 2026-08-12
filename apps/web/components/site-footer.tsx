import { ShieldIcon } from "@breero/ui";
import Link from "next/link";

const groups = [
  { title: "Explore", links: [["Services", "/services"], ["How it works", "/how-it-works"], ["Service areas", "/areas"], ["Gift cards", "/gift-cards"]] },
  { title: "Support", links: [["Help centre", "/help"], ["Contact us", "/contact"], ["Manage booking", "/account/bookings"], ["Safety", "/safety"]] },
  { title: "Professionals", links: [["Join BREERO", "/professionals"], ["Partner sign in", "/partner"], ["Partner standards", "/standards"]] },
];

export function SiteFooter() {
  return <footer className="site-footer"><div className="footer__inner"><div className="footer__intro"><Link className="brand brand--light" href="/"><span className="brand__mark">B</span><span>BREERO</span></Link><p>Trusted help for the place you call home.</p><span className="footer__trust"><ShieldIcon size={18} />Every booking is BREERO protected</span></div><div className="footer__links">{groups.map((group) => <div key={group.title}><h2>{group.title}</h2>{group.links.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}</div>)}</div></div><div className="footer__legal"><span>© {new Date().getFullYear()} BREERO Ltd.</span><div><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link><Link href="/accessibility">Accessibility</Link></div></div></footer>;
}
