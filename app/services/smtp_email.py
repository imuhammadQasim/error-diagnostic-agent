import asyncio
import smtplib
from app.config.settings import get_settings

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

settings = get_settings()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def _send_email_sync(
    to_email: str,
    subject: str,
    html: str,
):
    msg = MIMEMultipart("alternative")

    msg["Subject"] = subject
    msg["From"] = settings.SMTP_GMAIL_USERNAME
    msg["To"] = to_email

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()

        server.login(
            settings.SMTP_GMAIL_USERNAME,
            settings.SMTP_GMAIL_APP_PASSWORD,
        )

        server.sendmail(
            settings.SMTP_GMAIL_USERNAME,
            to_email,
            msg.as_string(),
        )

        server.quit()


async def send_email(
    to_email: str,
    subject: str,
    html: str,
):
    await asyncio.to_thread(
        _send_email_sync,
        to_email,
        subject,
        html,
    )