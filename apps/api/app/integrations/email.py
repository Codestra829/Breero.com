import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from app.config import settings
from app.integrations.payouts import IntegrationNotConfigured


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    text: str


class EmailGateway(Protocol):
    async def send(self, *, to: str, subject: str, text: str) -> str: ...


class FakeEmailGateway:
    def __init__(self): self.sent: list[dict] = []
    async def send(self, *, to: str, subject: str, text: str) -> str:
        self.sent.append({"to": to, "subject": subject, "text": text})
        return f"fake-email-{len(self.sent)}"


class ConsoleEmailGateway(FakeEmailGateway):
    async def send(self, **message: str) -> str:
        identifier = await super().send(**message)
        print(f"EMAIL {identifier} to={message['to']} subject={message['subject']}")
        return identifier


class SmtpEmailGateway:
    async def send(self, *, to: str, subject: str, text: str) -> str:
        if not settings.smtp_host or not settings.smtp_from_email:
            raise IntegrationNotConfigured("Email provider is not configured")
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = settings.smtp_from_email, to, subject
        message.set_content(text)
        def deliver():
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as client:
                client.starttls()
                if settings.smtp_username:
                    client.login(settings.smtp_username, settings.smtp_password)
                client.send_message(message)
        await asyncio.to_thread(deliver)
        return message["Message-ID"] or "smtp-accepted"


EMAIL_TEMPLATES = {
    "booking.confirmed": ("Booking confirmed", "Your BREERO booking is confirmed."),
    "technician.assigned": ("Technician assigned", "A technician has been assigned."),
    "quote.available": ("Quote available", "Your quote is ready for review."),
    "quote.approved": ("Quote approved", "Your quote has been approved."),
    "payment.receipt": ("Payment receipt", "Thank you. Your payment was received."),
    "password.reset": ("Reset your password", "Use the secure reset link supplied."),
    "email.verification": ("Verify your email", "Use the secure verification link supplied."),
    "job.completed": ("Job complete", "Your BREERO job has been completed."),
}


def render_email(event_type: str, context: dict | None = None) -> RenderedEmail:
    if event_type not in EMAIL_TEMPLATES:
        raise ValueError(f"Unsupported email event: {event_type}")
    subject, text = EMAIL_TEMPLATES[event_type]
    context = context or {}
    return RenderedEmail(subject.format_map(context), text.format_map(context))
