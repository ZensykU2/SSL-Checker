import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()


def send_ssl_warning_email(to_email: str, website_url: str, expiry_date: datetime, remaining_days: int):
    sender = os.getenv("SENDER_EMAIL")
    api_key = os.getenv("SENDGRID_API_KEY")

    if not sender:
        print("❌ Fehler: SENDER_EMAIL ist nicht gesetzt.")
        return

    if not api_key:
        print("❌ Fehler: SENDGRID_API_KEY ist nicht gesetzt.")
        return

    subject = f"⚠️ SSL-Zertifikat läuft bald ab: {website_url}"
    formatted_expiry_date = expiry_date.strftime('%d.%m.%Y')

    content = f"""
Hallo,

Das SSL-Zertifikat für {website_url} läuft am {formatted_expiry_date} ab.
Das sind nur noch {remaining_days} Tage!

Bitte erneuern Sie das Zertifikat rechtzeitig, um Warnmeldungen im Browser zu vermeiden.

Viele Grüße,
Dein SSL-Wächter
    """

    message = Mail(
        from_email=sender,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)

        print(f"📧 E-Mail an {to_email} gesendet (Status: {response.status_code})")

        # Debug-Antwort
        if response.status_code != 202:
            print("⚠️ SendGrid-Fehlerantwort:")
            print("Body:", response.body)
            print("Headers:", response.headers)

    except Exception as e:
        print(f"❌ Ausnahme beim Senden an {to_email}: {e}")
        if hasattr(e, 'body'):
            print("📄 Fehlerantwort von SendGrid:", e.body)
