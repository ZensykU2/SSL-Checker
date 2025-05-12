from fastapi import FastAPI, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.handlers.exception_handlers import auth_exception_handler
from app.routers import auth, users, logs, websites, admin
from app.server.tasks import check_certificates_loop
from app.database import models
from app.database.database import engine

def init_app(app: FastAPI):

    models.Base.metadata.create_all(bind=engine)

    app.add_middleware(SessionMiddleware, secret_key="secret_key")

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    app.add_exception_handler(HTTPException, auth_exception_handler)

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(logs.router)
    app.include_router(websites.router)
    app.include_router(admin.router)

    check_certificates_loop()
