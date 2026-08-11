export type UUID = string;
export type ISODate = string;
export type ISODateTime = string;
export type MoneyAmount = string;

export type QuestionType =
  | "single_choice" | "multi_choice" | "boolean" | "short_text"
  | "long_text" | "number" | "date" | "media";

export interface QuestionOption { value: string; label: string; description?: string }
export interface ServiceQuestion {
  id: UUID; key: string; label: string; help_text: string | null;
  question_type: QuestionType; required: boolean;
  options: QuestionOption[] | null; validation: Record<string, unknown> | null; sort_order: number;
}
export interface ServiceSummary {
  id: UUID; slug: string; name: string; description: string | null;
  base_price: MoneyAmount; duration_minutes: number;
}
export interface ServiceDetail extends ServiceSummary { questions: ServiceQuestion[] }

export interface AddressValidationRequest {
  address: string; line1?: string; city?: string; postal_code?: string;
  country_code?: string; latitude?: number; longitude?: number;
}
export interface AddressValidation {
  serviceable: boolean; formatted_address: string; address_id: UUID | null;
  service_area_id: UUID | null; legal_entity_code: string | null;
}
export interface AvailabilitySearchRequest {
  service_id: UUID; address_id: UUID; date_from: ISODate; date_to: ISODate;
}
export interface AvailabilitySlot { start: ISODateTime; end: ISODateTime; remaining_capacity: number }

export interface CustomerInput { first_name: string; last_name: string; email: string; phone: string }
export interface BookingAnswerInput { question_id: UUID; value: string }
export interface BookingCreateRequest {
  service_id: UUID; customer: CustomerInput; address_id: UUID;
  window: { start: ISODateTime; end: ISODateTime }; answers: BookingAnswerInput[];
}
export interface Booking {
  id: UUID; reference: string; status: string; total_amount: MoneyAmount; currency: string;
  window_start: ISODateTime; window_end: ISODateTime; payment_required: boolean;
}
export interface CustomerBookingList { items: Booking[] }

export type UserRole = "customer" | "partner" | "technician" | "operations" | "finance" | "admin";
export interface User { id: UUID; email: string; full_name: string; role: UserRole; is_active: boolean }
export interface LoginRequest { email: string; password: string }
export interface RegisterRequest extends LoginRequest { full_name: string }
export interface AuthSession { access_token: string; token_type: "bearer"; expires_in: number; user: User }

export type PaymentStatus = "CREATED" | "REQUIRES_ACTION" | "PROCESSING" | "AUTHORIZED" | "CAPTURED" | "FAILED" | "CANCELLED" | "REFUNDED" | "PARTIALLY_REFUNDED";
export interface PaymentIntentRequest {
  booking_id: UUID; amount_minor: number; currency?: string;
  capture_method?: "automatic" | "manual"; metadata?: Record<string, string>;
}
export interface Payment {
  id: UUID; booking_id: UUID; provider: string; status: PaymentStatus;
  amount_minor: number; currency: string; captured_amount_minor: number;
  client_secret: string | null; failure_code: string | null;
  created_at: ISODateTime; updated_at: ISODateTime;
}

/** Frontend-ready contracts; quote/profile endpoints are documented as backend gaps. */
export interface QuoteLine { id: UUID; description: string; quantity: number; unit_amount_minor: number; total_amount_minor: number }
export interface Quote { id: UUID; booking_id: UUID; status: string; currency: string; total_amount_minor: number; expires_at: ISODateTime | null; terms: string | null; lines: QuoteLine[] }
export interface CustomerProfile { id: UUID; email: string; first_name: string; last_name: string; phone: string | null }
