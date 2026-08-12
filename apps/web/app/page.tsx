import type { Metadata } from "next";
import Link from "next/link";
import { serviceCatalog } from "@/lib/booking-catalog";

export const metadata: Metadata = {
  title: "Trusted home services, simply booked",
  description: "Discover trusted home-service professionals, clear starting prices, and convenient booking with BREERO.",
};

export default function HomePage() {
  return (
    <div className="marketplace-page">
      <section className="shell market-hero">
        <div>
          <p className="market-eyebrow">Home care, handled</p>
          <h1>One less thing on your list.</h1>
          <p>Book trusted professionals for cleaning, repairs, and everyday home projects—with clear next steps from start to finish.</p>
          <Link className="market-button" href="/services">Find a service</Link>
        </div>
        <div className="hero-panel">
          <h2>What does your home need?</h2>
          <p>Choose a service, check your address, and see available times in minutes.</p>
          <Link className="market-button-secondary" href="/booking">Start booking</Link>
          <p><small>Clear pricing · Trusted professionals · Support when you need it</small></p>
        </div>
      </section>

      <section className="shell market-section" aria-labelledby="popular-services">
        <p className="market-eyebrow">Popular services</p>
        <h2 id="popular-services">Good help, without the hunt.</h2>
        <div className="service-list">
          {serviceCatalog.slice(0, 6).map((service) => (
            <Link className="service" href={`/services/${service.slug}`} key={service.id}>
              <strong>{service.name}</strong><p>{service.description}</p>
              <span>From €{service.base_price}</span><span className="arrow">Explore →</span>
            </Link>
          ))}
        </div>
      </section>

      <section id="how-it-works" className="shell market-section split">
        <div><p className="market-eyebrow">How it works</p><h2>From “needs doing” to done.</h2><p>Tell us what you need. We confirm serviceability and availability with BREERO, then keep you informed through payment and confirmation.</p></div>
        <div className="steps"><div><b>Choose your service</b><p>Answer only the questions relevant to the work.</p></div><div><b>Pick a time</b><p>See live availability for your validated address.</p></div><div><b>Book with confidence</b><p>Review everything before payment and track authoritative status.</p></div></div>
      </section>

      <section className="shell market-section split">
        <div className="quote"><p>Clear booking details, a defined arrival window, and support throughout the service visit.</p><small>Designed around customer confidence</small></div>
        <div><p className="market-eyebrow">Where we work</p><h2>Growing neighbourhood by neighbourhood.</h2><p>Enter your address during booking. BREERO securely asks the platform whether your exact location is covered—we never guess serviceability in the browser.</p><Link className="market-button" href="/booking">Check my address</Link></div>
      </section>

      <section className="shell market-section split">
        <div><p className="market-eyebrow">For professionals</p><h2>Do great work. We’ll help with the rest.</h2><p>Join a marketplace designed for dependable service businesses and skilled home professionals.</p><a className="market-button-secondary" href="mailto:partners@breero.com">Become a partner</a></div>
        <div className="faq"><h2>Questions, answered.</h2><details><summary>How are professionals selected?</summary><p>BREERO verifies partner details and qualifications appropriate to each service.</p></details><details><summary>When do I pay?</summary><p>You review the booking before entering the secure payment handoff. A redirect alone never marks a booking paid.</p></details><details><summary>Can I change my booking?</summary><p>Sign in to view your booking and contact support for changes.</p></details></div>
      </section>
    </div>
  );
}
