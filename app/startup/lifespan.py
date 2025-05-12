from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.database import SessionLocal
from app.database import models
from app.utilities.password_utils import hash_password

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
