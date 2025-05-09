from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Website, CheckLog
from app.ssl_checker import get_ssl_expiry_date

def perform_single_ssl_check(website: Website, db: Session) -> CheckLog | None:
    expiry_date = get_ssl_expiry_date(website.url)
    if not expiry_date:
        return None

    now_utc = datetime.now(timezone.utc)
    remaining_days = (expiry_date - now_utc).days

    log_entry = CheckLog(
        website_id=website.id,
        expiry_date=expiry_date,
        remaining_days=remaining_days,
        email_sent=False  
    )
    db.add(log_entry)
    db.commit()
    return log_entry
