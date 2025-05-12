from fastapi import APIRouter, Request, Depends, HTTPException, Query, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from app.database import models
from app.database.database import get_db
from app.database.models import CheckLog, Website
from app.routers.auth import get_current_user
from typing import List

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/logs", response_class=HTMLResponse)
async def logs(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Zugriff verweigert.")

    query = db.query(CheckLog).join(Website)

    if start:
        query = query.filter(CheckLog.checked_at >= datetime.fromisoformat(start))
    if end:
        query = query.filter(CheckLog.checked_at <= datetime.fromisoformat(end))
    if search:
        query = query.filter(func.lower(Website.url).like(f"%{search.lower()}%"))

    page_size = 8
    total_logs = query.count()
    total_pages = (total_logs + page_size - 1) // page_size
    

    logs = (
        query.order_by(CheckLog.checked_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs,
        "page": page,
        "total_pages": total_pages,
        "search": search,
        "start": start,
        "end": end,
        "is_admin": current_user.is_admin
    })

@router.post("/logs/delete/{log_id}")
async def delete_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(CheckLog).filter(CheckLog.id == log_id).first()
    if log:
        db.delete(log)
        db.commit()
        return RedirectResponse(url="/logs", status_code=303)
    raise HTTPException(status_code=404, detail="Log nicht gefunden")

@router.post("/logs/delete-multiple")
async def delete_multiple_logs(
    log_ids: str = Form(...),  
    db: Session = Depends(get_db)
):
    ids = [int(i) for i in log_ids.split(",") if i.strip().isdigit()]
    print(f"IDs als Integer: {ids}")

    try:
        if ids:
            logs = db.query(CheckLog).filter(CheckLog.id.in_(ids)).all()
            print(f"Logs gefunden: {len(logs)}")
            if logs:
                deleted = db.query(CheckLog).filter(CheckLog.id.in_(ids)).delete(synchronize_session=False)
                print(f"Anzahl der gelöschten Logs: {deleted}")
                db.commit()
            else:
                print("Keine Logs gefunden zum Löschen")
        else:
            print("Keine gültigen IDs gefunden")
    except Exception as e:
        db.rollback()  
        print(f"Fehler beim Löschen: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Löschen der Logs")

    return RedirectResponse(url="/logs", status_code=303)