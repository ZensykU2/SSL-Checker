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
        print(" Fehler: SENDER_EMAIL not set.")
        return

    if not api_key:
        print("Error: SENDGRID_API_KEY not set.")
        return

    subject = f" SSL-Zertifikat läuft bald ab: {website_url}"
    formatted_expiry_date = expiry_date.strftime('%d.%m.%Y')

    content = f"""
Hallo,

Das SSL-Zertifikat für {website_url} läuft am {formatted_expiry_date} ab.
Dies sind nur noch {remaining_days} Tage.

Bitte erneuern Sie das Zertifikat rechtzeitig, um Warnmeldungen im Browser zu vermeiden.

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

        print(f"E-Mail to {to_email} sent (Status: {response.status_code})")

        if response.status_code != 202:
            print(" SendGrid-Error:")
            print("Body:", response.body)
            print("Headers:", response.headers)

    except Exception as e:
        print(f"Exception sending to {to_email}: {e}")
        if hasattr(e, 'body'):
            print("Exception from SendGrid:", e.body)
