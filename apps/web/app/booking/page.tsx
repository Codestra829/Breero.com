import type { Metadata } from "next"; import { Suspense } from "react"; import { BookingWizard } from "../../components/booking/BookingWizard";
export const metadata:Metadata={title:"Book a home service",description:"Choose a BREERO service, validate your address, find a time, and review your booking."};
export default function BookingPage(){return <div className="booking-shell"><Suspense fallback={<div className="market-loading">Preparing your booking…</div>}><BookingWizard/></Suspense></div>}
