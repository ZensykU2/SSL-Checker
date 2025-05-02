from app.database import SessionLocal
from app.models import User
from passlib.hash import bcrypt

def create_initial_users():
    db = SessionLocal()

    admin = User(
        username="admin",
        email="admin@email.com",
        password=bcrypt.hash("admin123"),
        is_admin=True
    )

    user = User(
        username="user",
        email="user@email.com",
        password=bcrypt.hash("user123"),
        is_admin=False
    )

    db.add(admin)
    db.add(user)
    db.commit()
    db.close()

if __name__ == "__main__":
    create_initial_users()
