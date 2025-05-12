
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from app.database import models
from app.server.tasks import check_certificates_loop
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.routers import auth, users, logs, websites, admin
from app.database.database import SessionLocal, engine
from app.database import models
from app.utilities.password_utils import hash_password

models.Base.metadata.create_all(bind=engine)

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
        print("Initialisiere Standardnutzer...")
        default_users = [
            {"username": "admin", "email": "admin@example.com", "password": "admin123", "is_admin": True},
            {"username": "user", "email": "user@example.com", "password": "user123", "is_admin": False},
        ]
        for user_data in default_users:
            user = models.User(
                username=user_data["username"],
                email=user_data["email"],
                password=hash_password(user_data["password"]),
                is_admin=user_data["is_admin"]
            )
            db.add(user)
        db.commit()
    db.close()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key="secret_key")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.exception_handler(HTTPException)
async def auth_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login", status_code=303)
    raise exc

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(logs.router)
app.include_router(websites.router)
app.include_router(admin.router)

check_certificates_loop()