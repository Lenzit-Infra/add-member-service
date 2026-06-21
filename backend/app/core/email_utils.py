# app/core/email_utils.py
import smtplib
from email.mime.text import MIMEText
from app.core import config


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Sends an email via SMTP using config.SMTP_*. Returns False (and logs)
    instead of raising if SMTP isn't configured yet, so auth flows degrade
    gracefully in dev rather than 500ing."""
    if not config.SMTP_HOST or not config.SMTP_USER or not config.SMTP_PASSWORD:
        print(f"EMAIL (SMTP not configured, not sent): to={to_email} subject={subject}\n{html_body}")
        return False

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = config.SMTP_FROM or config.SMTP_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(msg["From"], [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"EMAIL ERROR sending to {to_email}: {e}")
        return False
