import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime

def send_ssl_warning_email(to_email: str, website_url: str, expiry_date: datetime, remaining_days: int):
    sender = os.getenv("SENDER_EMAIL")
    
    if not sender:
        print("❌ Fehler: Absender-E-Mail-Adresse ist nicht gesetzt.")
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
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)

        print(f"📧 E-Mail an {to_email} gesendet (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Fehler beim Senden an {to_email}: {e}")
