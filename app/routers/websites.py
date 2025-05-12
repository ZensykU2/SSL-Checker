from fastapi import APIRouter, Request, Form, Depends, HTTPException, Cookie
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError
from app.database.database import get_db
from app.database.models import Website, CheckLog
from app.utilities.normalize_url import normalize_url
from app.utilities.ssl_utils import perform_single_ssl_check
from app.utilities.email_utils import send_ssl_warning_email
from app.routers.auth import get_current_user
from datetime import datetime, timezone
from app.database import models
from fastapi.templating import Jinja2Templates
from app.utilities.security import verify_token
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from starlette.status import HTTP_303_SEE_OTHER

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db), access_token: Optional[str] = Cookie(None)):
    if not access_token:
        return RedirectResponse(url="/login", status_code=303)

    try:
        payload = verify_token(access_token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401)

        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "is_admin": user.is_admin,
            "user_email": user.email
        })

    except JWTError:
        return RedirectResponse(url="/login", status_code=303)

@router.post("/submit")
async def submit_form(
    request: Request,
    url: str = Form(...),
    email: str = Form(...),
    threshold: int = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    normalized_url = normalize_url(url)

    existing_entry = db.query(Website).filter(
        and_(Website.url == normalized_url, Website.user_id == current_user.id)
    ).first()

    if existing_entry:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Du hast diese Website bereits hinzugefügt.",
            "user_email": current_user.email,
            "is_admin": current_user.is_admin
        })

    entry = Website(
        url=normalized_url,
        email=email,
        threshold_days=threshold,
        user_id=current_user.id
    )

    try:
        db.add(entry)
        db.commit()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "message": "Gespeichert!",
            "user_email": current_user.email,
            "is_admin": current_user.is_admin
        })
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Fehler beim Speichern der URL.",
            "user_email": current_user.email,
            "is_admin": current_user.is_admin
        })

@router.get("/my-websites", response_class=HTMLResponse)
async def my_websites(
    request: Request,
    search: Optional[str] = None, 
    page: int = 1,  
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(Website).filter(Website.user_id == current_user.id)
    
    if search:
        query = query.filter(Website.url.ilike(f"%{search}%"))

    per_page = 8

    total_count = query.count()
    total_pages = (total_count // per_page) + (1 if total_count % per_page > 0 else 0)
    
    page = max(1, min(page, total_pages))
    
    websites = query.offset((page - 1) * per_page).limit(per_page).all()

    return templates.TemplateResponse(
        "my_websites.html", 
        {
            "request": request, 
            "websites": websites,
            "is_admin": current_user.is_admin,
            "page": page,
            "total_pages": total_pages,
            "search": search,
        }
    )

@router.post("/my-websites/delete/{website_id}")
async def delete_my_website(website_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    website = db.query(Website).filter(Website.id == website_id, Website.user_id == current_user.id).first()
    if not website:
        raise HTTPException(status_code=403, detail="Nicht erlaubt.")
    db.query(CheckLog).filter(CheckLog.website_id == website_id).delete()
    db.delete(website)
    db.commit()
    return RedirectResponse(url="/my-websites", status_code=303)

@router.get("/websites", response_class=HTMLResponse)
async def websites(
    request: Request,
    search: Optional[str] = None, 
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(Website)
    
    if search:
        query = query.filter(Website.url.ilike(f"%{search}%"))
    
    per_page = 8

    total_count = query.count()
    total_pages = (total_count // per_page) + (1 if total_count % per_page > 0 else 0)
    
    page = max(1, min(page, total_pages))

    websites = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return templates.TemplateResponse(
        "websites.html", 
        {
            "request": request, 
            "websites": websites,
            "is_admin": current_user.is_admin,
            "page": page,
            "total_pages": total_pages,
            "search": search,  
        }
    )

@router.post("/delete/{website_id}")
async def delete_website(website_id: int, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == website_id).first()
    if website:
        db.delete(website)
        db.commit()
    return RedirectResponse(url="/websites", status_code=HTTP_303_SEE_OTHER)

@router.post("/send-email/{website_id}")
async def send_email(website_id: int, request: Request, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        return RedirectResponse(url="/websites?error=Website+nicht+gefunden", status_code=HTTP_303_SEE_OTHER)

    log_entry = perform_single_ssl_check(website, db)
    if not log_entry or not log_entry.expiry_date:
        return RedirectResponse(url="/websites?error=Kein+gültiges+SSL-Zertifikat+gefunden", status_code=HTTP_303_SEE_OTHER)

    expiry_date = log_entry.expiry_date
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    remaining_days = (expiry_date - datetime.now(timezone.utc)).days

    send_ssl_warning_email(website.email, website.url, expiry_date, remaining_days)

    log_entry.email_sent = True
    db.commit()

    return RedirectResponse(
        url=f"/websites?success=E-Mail+an+{website.email}+gesendet", status_code=HTTP_303_SEE_OTHER
    )