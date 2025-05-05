from pydantic import BaseModel
from datetime import datetime

class CheckLogOut(BaseModel):
    checked_at: datetime
    expiry_date: datetime
    remaining_days: int
    email_sent: bool

    class Config:
        from_attributes = True

class User(BaseModel):
    id: int
    username: str
    is_admin: bool

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str
