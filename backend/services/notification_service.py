"""
NoblePort Notification Service

Email and SMS notifications for ops team alerts,
client payment reminders, and job status updates.
"""

import logging
from typing import Any

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles email and SMS notifications."""

    async def notify_ops_team(self, subject: str, message: str, job_data: dict[str, Any] | None = None):
        """
        Notify the ops team about a new job, payment, or scheduling event.
        """
        if settings.sendgrid_api_key:
            await self._send_email(
                to_emails=settings.ops_notification_emails,
                subject=f"[NoblePort Ops] {subject}",
                body=self._format_ops_email(message, job_data),
            )
        else:
            logger.info(f"OPS NOTIFICATION: {subject} - {message}")

    async def send_payment_reminder(
        self,
        client_email: str,
        client_phone: str | None,
        subject: str,
        message: str,
        checkout_url: str | None = None,
    ):
        """Send payment reminder via email and SMS."""
        body = message
        if checkout_url:
            body += f"\n\nPay now: {checkout_url}"

        if settings.sendgrid_api_key:
            await self._send_email(
                to_emails=[client_email],
                subject=subject,
                body=body,
            )

        if client_phone and settings.twilio_account_sid:
            await self._send_sms(
                to_number=client_phone,
                message=f"{subject}: {message[:140]}",
            )

        logger.info(f"Payment reminder sent to {client_email}: {subject}")

    async def send_proposal_ready(
        self, client_email: str, proposal_title: str, checkout_url: str
    ):
        """Notify client that their proposal is ready with a deposit link."""
        subject = f"Your Proposal is Ready: {proposal_title}"
        body = (
            f"Your proposal for {proposal_title} is ready.\n\n"
            f"To secure your spot on our schedule, complete your deposit here:\n"
            f"{checkout_url}\n\n"
            f"Thank you for choosing NoblePort."
        )

        if settings.sendgrid_api_key:
            await self._send_email(
                to_emails=[client_email],
                subject=subject,
                body=body,
            )

        logger.info(f"Proposal ready notification sent to {client_email}")

    async def _send_email(self, to_emails: list[str], subject: str, body: str):
        """Send email via SendGrid."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            sg = SendGridAPIClient(settings.sendgrid_api_key)
            for email in to_emails:
                message = Mail(
                    from_email=settings.notification_from_email,
                    to_emails=email,
                    subject=subject,
                    plain_text_content=body,
                )
                sg.send(message)
        except Exception as e:
            logger.error(f"Email send failed: {e}")

    async def _send_sms(self, to_number: str, message: str):
        """Send SMS via Twilio."""
        try:
            from twilio.rest import Client

            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            client.messages.create(
                body=message,
                from_=settings.twilio_from_number,
                to=to_number,
            )
        except Exception as e:
            logger.error(f"SMS send failed: {e}")

    @staticmethod
    def _format_ops_email(message: str, job_data: dict[str, Any] | None) -> str:
        lines = [message, ""]
        if job_data:
            lines.append("--- Job Details ---")
            for key, value in job_data.items():
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)
