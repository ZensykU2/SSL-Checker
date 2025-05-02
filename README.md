#  SSL-Checker

A web-based SSL/TLS certificate monitoring tool built with **FastAPI**, **PostgreSQL**, and **SendGrid**.  
It notifies users about expiring certificates and provides a web interface to manage monitored websites.

---

##  Requirements

- Python 3.10+
- PostgreSQL (e.g. [Download Here](https://www.postgresql.org/download/))
- Git
- SendGrid account (for email notifications)

---

##  Project Setup

### 1. Clone the project

```bash
git clone http://192.168.100.68:3000/CristianTorre/SSL-Checker.git
cd SSL-Checker
python -m venv venv

# Activate it:

# Windows 
venv\Scripts\activate

# macOS/Linux: 
source venv/bin/activate

### 3. Install dependencies

pip install -r requirements.txt

## PostgreSQL Setup

### 1. Start PostgreSQL and access with your root user

psql -u (your root user) -f init_db.sql

## Environment Configuration

### 1. Create a .env file in the project root

use .env.example as a template

### Alembic (Database Migrations)

## 1. Initialize Alembic (once)

alembic init alembic

## 2. Configure alembic/env.py

Update the following:

- Add this at the top:

import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base
from app import models
load_dotenv()

- Set database URL from .env:
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

- Replace:
target_metadata = None

- With:
target_metadata = Base.metadata

## 3. Generate and apply initial migration

alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

## Seed Initial Users

### Create users

- Create admin and regular user by running:
python seed_users.py

## Run the App

uvicorn app.main:app --reload

App will be available at:
http://127.0.0.1:8000

## Email Notifications

- Uses SendGrid to send SSL and TSL expiry notifications.
- Set your API key in the .env file.
- Emails are sent to the address associated with each website entry.

## User Accounts

- Admin: admin | PW: admin123
- User: user | PW: user123

