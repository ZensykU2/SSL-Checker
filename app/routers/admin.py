from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models, password_utils
from app.database import get_db
from app.routers.auth import get_current_user

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/create-admin-form", response_class=HTMLResponse)
async def create_admin_form(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("create_admin.html", {"request": request, "is_admin": current_user.is_admin})

@router.post("/create-admin")
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
