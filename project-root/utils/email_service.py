import smtplib
from email.mime.text import MIMEText

from core.config import settings


def send_email(to_email: str, subject: str, body: str) -> None:
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], message.as_string())


def send_order_confirmation_email(to_email: str, order_id: int, total: float) -> None:
    send_email(
        to_email,
        f"Order #{order_id} confirmed",
        f"Your order #{order_id} for ${total:.2f} has been confirmed.",
    )


def send_payment_status_email(to_email: str, order_id: int, success: bool) -> None:
    status_text = "successful" if success else "failed"
    send_email(
        to_email,
        f"Payment {status_text} for order #{order_id}",
        f"Your payment for order #{order_id} was {status_text}.",
    )


def send_shipping_update_email(to_email: str, order_id: int, order_status: str) -> None:
    send_email(
        to_email,
        f"Order #{order_id} update",
        f"Your order #{order_id} status is now: {order_status}.",
    )
