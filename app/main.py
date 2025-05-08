from fastapi import FastAPI, Request, Form, Depends, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.status import HTTP_303_SEE_OTHER
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional
from datetime import datetime, timezone
from jose import JWTError
from sqlalchemy import func
from fastapi.responses import JSONResponse
from sqlalchemy import and_
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from app import models, password_utils, security
from app.password_utils import hash_password
from app.security import verify_token
from app.database import engine, SessionLocal
from app.models import Website, CheckLog
from app.normalize_url import normalize_url
from app.email_utils import send_ssl_warning_email
from app.tasks import check_certificates_loop


models.Base.metadata.create_all(bind=engine)


templates = Jinja2Templates(directory="app/templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    if db.query(models.User).count() == 0:
        print("No users found. Creating default users.")
        default_users = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",
                "is_admin": True
            },
            {
                "username": "user",
                "email": "user@example.com",
                "password": "user123",
                "is_admin": False
            }
        ]
        for user_data in default_users:
            hashed_pw = hash_password(user_data["password"])
            user = models.User(
                username=user_data["username"],
                email=user_data["email"],
                password=hashed_pw,
                is_admin=user_data["is_admin"]
            )
            db.add(user)
        db.commit()
    db.close()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key = "secret_key")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

def get_current_user(access_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        return RedirectResponse(url="/login", status_code=303)

    try:
        payload = verify_token(access_token)
        user_id = payload.get("user_id")
        if not user_id:
            return RedirectResponse(url="/login", status_code=303)

        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return RedirectResponse(url="/login", status_code=303)

        return user

    except JWTError:
        return RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login_for_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Benutzername existiert nicht."
        })

    if not password_utils.verify_password(form_data.password, user.password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Falsches Passwort."
        })

    access_token = security.create_access_token(data={"user_id": user.id})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=access_token)
    return response

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = templates.TemplateResponse("logout.html", {"request": request})
    response.delete_cookie("access_token")
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()

    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Ein Benutzer mit diesem Benutzernamen oder dieser E-Mail existiert bereits."
        })

    hashed_password = password_utils.hash_password(password)
    new_user = models.User(username=username, password=hashed_password, email=email)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

@app.get("/profile", response_class=HTMLResponse)
async def profile_form(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {"request": request, "user": current_user, "is_admin": current_user.is_admin})

@app.post("/profile", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Zugriff verweigert.")
    
    existing_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()

    if existing_user:
        return templates.TemplateResponse("/profile.html", {
            "request": request,
            "error": "Ein Benutzer mit diesem Benutzernamen oder dieser E-Mail existiert bereits.",
            "user": current_user,
            "is_admin": current_user.is_admin
        })

    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    user.username = username
    user.email = email
    if password:
        user.password = hash_password(password)
    db.commit()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "message": "Profil aktualisiert!", "is_admin": current_user.is_admin})

@app.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Nur Admins dürfen diese Seite sehen.")
    
    query = db.query(models.User)
    
    if role == "user":
        query = query.filter(models.User.is_admin == False)
    elif role == "admin":
        query = query.filter(models.User.is_admin == True)

    users = query.all()

    success_message = request.session.pop("success", None)
    
    return templates.TemplateResponse(
        "users.html", 
        {
            "request": request, 
            "users": users, 
            "current_user_id": current_user.id, 
            "is_admin": current_user.is_admin,
            "success": success_message,
        }
    )


@app.post("/users/toggle-admin/{user_id}")
async def toggle_admin(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        users = db.query(models.User).all()
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "users": users,
                "error": "Nur Admins dürfen Rollen ändern.",
            },
            status_code=403,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        users = db.query(models.User).all()
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "users": users,
                "error": "Benutzer nicht gefunden.",
                "is_admin": current_user.is_admin,
            },
            status_code=404,
        )

    if user.id == current_user.id and user.is_admin:
        users = db.query(models.User).all()
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "users": users,
                "error": "Du kannst dir selbst keine Adminrechte entziehen.",
                "is_admin": current_user.is_admin,
            },
            status_code=401,
        )

    user.is_admin = not user.is_admin
    db.commit()
    return RedirectResponse(url="/users", status_code=303)


@app.post("/users/delete/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()

    if not current_user.is_admin:
        users = db.query(models.User).all()
        return templates.TemplateResponse(
            "users.html", 
            {
                "request": request,
                "users": users,
                "error": "Nur Admins dürfen Benutzer löschen.",
            },
            status_code=403,
        )

    if not user_to_delete:
        users = db.query(models.User).all()
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "users": users,
                "error": "Benutzer nicht gefunden.",
                "is_admin": current_user.is_admin,
            },
            status_code=404,
        )

    if user_to_delete.id == current_user.id:
        users = db.query(models.User).all()
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "users": users,
                "error": "Du kannst dich nicht selbst löschen.",
                "is_admin": current_user.is_admin,
            },
            status_code=400,
        )

    db.delete(user_to_delete)
    db.commit()

    request.session["success"] = f"Benutzer '{user_to_delete.username}' wurde erfolgreich gelöscht."
    return RedirectResponse(url="/users", status_code=303)

@app.get("/create-admin-form", response_class=HTMLResponse)
async def create_admin_form(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("create_admin.html", {"request": request, "is_admin": current_user.is_admin})

@app.post("/create-admin")
async def create_admin(request: Request, username: str = Form(...), password: str = Form(...),email: str = Form(...),
                       current_user: models.User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Zugriff verweigert.")
    
    existing_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()

    if existing_user:
        return templates.TemplateResponse("/create_admin.html", {
            "request": request,
            "error": "Ein Benutzer mit diesem Benutzernamen oder dieser E-Mail existiert bereits.",
            "is_admin": current_user.is_admin
        })
    
    hashed_password = password_utils.hash_password(password)
    new_admin = models.User(username=username, password=hashed_password, email=email, is_admin=True)
    db.add(new_admin)
    db.commit()
    return templates.TemplateResponse("create_admin.html", {"request": request, "message": "Einen neuen Admin erfolgreich erstellt.", "is_admin": current_user.is_admin})

@app.get("/", response_class=HTMLResponse)
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

@app.post("/submit")
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

@app.get("/my-websites", response_class=HTMLResponse)
async def websites(
    request: Request,
    search: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(Website).filter(Website.user_id == current_user.id)
    
    if search:
        query = query.filter(Website.url.ilike(f"%{search}%"))
    
    websites = query.all()
    

    return templates.TemplateResponse(
        "my_websites.html", 
        {
            "request": request, 
            "websites": websites, 
            "is_admin": current_user.is_admin
        }
    )


@app.post("/my-websites/delete/{website_id}")
async def delete_my_website(website_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    website = db.query(Website).filter(Website.id == website_id, Website.user_id == current_user.id).first()
    if not website:
        raise HTTPException(status_code=403, detail="Nicht erlaubt.")
    db.query(CheckLog).filter(CheckLog.website_id == website_id).delete()
    db.delete(website)
    db.commit()
    return RedirectResponse(url="/my-websites", status_code=303)

@app.get("/websites", response_class=HTMLResponse)
async def websites(
    request: Request,
    search: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(Website)
    
    if search:
        query = query.filter(Website.url.ilike(f"%{search}%")) 
    
    websites = query.all()
    
    return templates.TemplateResponse(
        "websites.html", 
        {
            "request": request, 
            "websites": websites, 
            "is_admin": current_user.is_admin
        }
    )


@app.get("/logs", response_class=HTMLResponse)
async def logs(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Zugriff verweigert.")
    logs = db.query(CheckLog).join(Website).order_by(CheckLog.checked_at.desc()).all()
    return templates.TemplateResponse("logs.html", {"request": request, "logs": logs, "is_admin": current_user.is_admin})

@app.post("/delete/{website_id}")
async def delete_website(website_id: int, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == website_id).first()
    if website:
        db.delete(website)
        db.commit()
    return RedirectResponse(url="/websites", status_code=HTTP_303_SEE_OTHER)



@app.get("/logs/filter", response_class=HTMLResponse)
async def filter_logs(
    request: Request,
    start: Optional[str] = None,
    end: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(CheckLog).join(Website)

    if start:
        query = query.filter(CheckLog.checked_at >= datetime.fromisoformat(start))
    if end:
        query = query.filter(CheckLog.checked_at <= datetime.fromisoformat(end))
    if search:
        query = query.filter(func.lower(Website.url).like(f"%{search.lower()}%"))

    logs = query.order_by(CheckLog.checked_at.desc()).all()

    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs,
        "is_admin": current_user.is_admin
    })


@app.post("/logs/delete/{log_id}")
async def delete_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(CheckLog).filter(CheckLog.id == log_id).first()
    if log:
        db.delete(log)
        db.commit()
        return RedirectResponse(url="/logs", status_code=303)
    raise HTTPException(status_code=404, detail="Log nicht gefunden")

@app.post("/send-email/{website_id}")
async def send_email(website_id: int, request: Request, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        return RedirectResponse(url="/websites?error=Website+nicht+gefunden", status_code=HTTP_303_SEE_OTHER)

    latest_log = (
        db.query(CheckLog)
        .filter(CheckLog.website_id == website_id)
        .order_by(CheckLog.checked_at.desc())
        .first()
    )

    if not latest_log or not latest_log.expiry_date:
        return RedirectResponse(url="/websites?error=Kein+Ablaufdatum+gefunden", status_code=HTTP_303_SEE_OTHER)

    expiry_date = latest_log.expiry_date
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    remaining_days = (expiry_date - datetime.now(timezone.utc)).days
    send_ssl_warning_email(website.email, website.url, expiry_date, remaining_days)

    return RedirectResponse(
        url=f"/websites?success=E-Mail+an+{website.email}+gesendet", status_code=HTTP_303_SEE_OTHER
    )

check_certificates_loop()