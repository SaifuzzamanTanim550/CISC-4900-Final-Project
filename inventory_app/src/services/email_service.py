import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def _parse_recipients(value):
    if not value:
        return []
    parts = [p.strip() for p in value.split(",")]
    return [p for p in parts if p]


def send_email(subject, body, to_list):
    smtp_user = os.getenv("GMAIL_SMTP_USER")
    smtp_password = os.getenv("GMAIL_SMTP_APP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM", smtp_user)

    if not smtp_user or not smtp_password:
        raise ValueError("Missing Gmail SMTP credentials in environment variables")

    if not to_list:
        raise ValueError("Recipient list is empty")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = ", ".join(to_list)
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)


def send_stock_out_email(subject, body):
    recipients = _parse_recipients(os.getenv("STOCK_OUT_EMAIL_TO"))
    send_email(subject=subject, body=body, to_list=recipients)


def send_low_stock_email(subject, body):
    recipients = _parse_recipients(os.getenv("LOW_STOCK_EMAIL_TO"))
    send_email(subject=subject, body=body, to_list=recipients)
