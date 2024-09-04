import requests
import os

EMAIL_API_KEY = os.getenv("EMAIL_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")

def send_email(to_email: str, subject: str, content: str):
    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "Content-Type": "application/json",
            "api-key": EMAIL_API_KEY
        },
        json={
            "sender": {"name": "SaaS App", "email": EMAIL_SENDER},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": content,
        }
    )
    return response
