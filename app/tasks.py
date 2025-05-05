import time
import threading
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Website, CheckLog
from .ssl_checker import get_ssl_expiry_date
from .email_utils import send_ssl_warning_email

def check_certificates_loop(interval_seconds: int = 21600):
    def loop():
        while True:
            print("Starting certificate verification...")
            db: Session = SessionLocal()
            try:
                websites = db.query(Website).all()
                for site in websites:
                    expiry_date = get_ssl_expiry_date(site.url)
                    if not expiry_date:
                        print(f"No SSL-Data for {site.url}")
                        continue

                    now_utc = datetime.now(timezone.utc)
                    remaining_days = (expiry_date - now_utc).days
                    email_sent = False

                    next_warning = site.next_warning
                    if next_warning is not None and next_warning.tzinfo is None:
                        next_warning = next_warning.replace(tzinfo=timezone.utc)

                    if remaining_days <= site.threshold_days:
                        if next_warning is None or now_utc >= next_warning:
                            send_ssl_warning_email(
                                to_email=site.email,
                                website_url=site.url,
                                expiry_date=expiry_date,
                                remaining_days=remaining_days
                            )
                            email_sent = True

                            next_intervals = [
                                int(site.threshold_days / 2),
                                int(site.threshold_days / 4),
                                1
                            ]
                            next_interval_days = next(
                                (i for i in next_intervals if i < remaining_days),
                                None
                            )

                            if next_interval_days:
                                site.next_warning = expiry_date - timedelta(days=next_interval_days)
                                site.next_warning = site.next_warning.replace(tzinfo=timezone.utc)
                            else:
                                site.next_warning = None

                            db.commit()
                    else:
                        print(f"{site.url} is OK ({remaining_days} days)")

                    log_entry = CheckLog(
                        website_id=site.id,
                        expiry_date=expiry_date,
                        remaining_days=remaining_days,
                        email_sent=email_sent
                    )
                    db.add(log_entry)
                    db.commit()

            finally:
                db.close()

            print("⏳ Waiting for next refresh...")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
