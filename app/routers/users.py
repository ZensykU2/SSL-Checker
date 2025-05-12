from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import models
from app.database.database import get_db
from app.utilities.password_utils import hash_password
from app.routers.auth import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile_form(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {"request": request, "user": current_user, "is_admin": current_user.is_admin})

@router.post("/profile", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    
    existing_user = db.query(models.User).filter(
        ((models.User.username == username) | (models.User.email == email)) &
        (models.User.id != current_user.id)
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

@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    page: int = 1,
    role: Optional[str] = None,
    search: Optional[str] = None,
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

    if search:
        query = query.filter(models.User.username.ilike(f"%{search}%"))

    
    total_users = query.count()

    per_page = 8

    total_pages = (total_users // per_page) + (1 if total_users % per_page > 0 else 0)
    
    page = max(1, min(page, total_pages))

    
    users = query.offset((page - 1) * per_page).limit(per_page).all()

    success_message = request.session.pop("success", None)
    
    return templates.TemplateResponse(
        "users.html", 
        {
            "request": request, 
            "users": users, 
            "current_user_id": current_user.id, 
            "is_admin": current_user.is_admin,
            "success": success_message,
            "page": page,
            "total_pages": total_pages,
            "role": role,
            "search": search 
        }
    )

@router.post("/users/toggle-admin/{user_id}")
async def toggle_admin(
    request: Request,
    user_id: int,
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.User)

    total_users = query.count()

    per_page = 8

    total_pages = (total_users // per_page) + (1 if total_users % per_page > 0 else 0)
    
    page = max(1, min(page, total_pages))

    
    users = query.offset((page - 1) * per_page).limit(per_page).all()
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
                "total_pages": total_pages,
            },
            status_code=401,
        )

    user.is_admin = not user.is_admin
    db.commit()
    return RedirectResponse(url="/users", status_code=303)

@router.post("/users/delete/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()

    total_users = db.query(models.User).count()
    
    per_page = 8
    total_pages = (total_users // per_page) + (1 if total_users % per_page > 0 else 0)

    page = int(request.query_params.get('page', 1))

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
                "total_pages": total_pages,
            },
            status_code=400,
        )

    db.delete(user_to_delete)
    db.commit()

    request.session["success"] = f"Benutzer '{user_to_delete.username}' wurde erfolgreich gelöscht."
    return RedirectResponse(url=f"/users?page={page}&total_pages={total_pages}", status_code=303)




