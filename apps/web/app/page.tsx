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
        <div><p className="market-eyebrow">How it works</p><h2>From “needs doing” to done.</h2><p>Tell us what you need. We validate the address, recommend a qualified provider, and confirm the appointment only after an operator verifies capacity.</p></div>
        <div className="steps"><div><b>Choose your service</b><p>Answer only the questions relevant to the work.</p></div><div><b>Request a time</b><p>Select a preferred time in the service-address time zone.</p></div><div><b>Schedule with confidence</b><p>All work requires a quote. No online payment is required or collected at this time.</p></div></div>
      </section>

      <section className="shell market-section split">
        <div className="quote"><p>Clear booking details, a defined arrival window, and support throughout the service visit.</p><small>Designed around customer confidence</small></div>
        <div><p className="market-eyebrow">Where we work</p><h2>Growing neighbourhood by neighbourhood.</h2><p>Enter your address during booking. BREERO securely asks the platform whether your exact location is covered—we never guess serviceability in the browser.</p><Link className="market-button" href="/booking">Check my address</Link></div>
      </section>

      <section className="shell market-section split">
        <div><p className="market-eyebrow">For professionals</p><h2>Do great work. We’ll help with the rest.</h2><p>Join a marketplace designed for dependable service businesses and skilled home professionals.</p><a className="market-button-secondary" href="mailto:partners@breero.com">Become a partner</a></div>
        <div className="faq"><h2>Questions, answered.</h2><details><summary>How are professionals selected?</summary><p>BREERO verifies service capability, ZIP coverage, licensing, insurance, working hours, and capacity before an operator confirms an appointment.</p></details><details><summary>When do I pay?</summary><p>Online payment is not required or collected at this time. All work requires a quote.</p></details><details><summary>Can I change my appointment request?</summary><p>Sign in to view your request and contact support to reschedule or cancel.</p></details></div>
      </section>
    </div>
  );
}
