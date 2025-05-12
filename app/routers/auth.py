from starlette.status import HTTP_303_SEE_OTHER
from fastapi import APIRouter, Request, Depends, Form, Cookie, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError

from app import models, password_utils, security
from app.database import get_db

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router = APIRouter()


def get_current_user(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> models.User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = security.verify_token(access_token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        return user

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
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

@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = templates.TemplateResponse("logout.html", {"request": request})
    response.delete_cookie("access_token")
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
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
