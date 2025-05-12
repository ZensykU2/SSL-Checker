from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from app.database.database import Base
from datetime import datetime, timezone
from sqlalchemy.orm import relationship




class Website(Base):
    __tablename__ = "websites"
    __table_args__ = (
        UniqueConstraint('url', 'user_id', name='unique_user_website'),
    )

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True, nullable=False)
    email = Column(String, nullable=False)
    threshold_days = Column(Integer, nullable=False)
    next_warning = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", backref="websites")
    logs = relationship("CheckLog", back_populates="website", cascade="all, delete-orphan")


class CheckLog(Base):
    __tablename__ = "check_logs"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expiry_date = Column(DateTime, nullable=True)
    remaining_days = Column(Integer)
    email_sent = Column(Boolean, default=False)

    website = relationship("Website", back_populates="logs")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True, nullable=False)
    is_admin = Column(Boolean, default=False)