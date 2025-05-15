#  SSL-Checker

A web-based SSL/TLS certificate monitoring tool built with **FastAPI**, **PostgreSQL**, and **SendGrid**.  
It notifies users about expiring certificates and provides a web interface to manage monitored websites.

---

##  Requirements

- [Docker](https://www.docker.com/) or [Podman](https://podman.io/)
    - Must support **Linux containers**
- [Git](https://git-scm.com/)
- [SendGrid](https://sendgrid.com) account (for email notifications)

---

##  Getting Started (Docker + pgAdmin)

### 1. Clone the Repository

```bash
git clone http://192.168.100.68:3000/CristianTorre/SSL-Checker.git
cd SSL-Checker
```
### 2. Set Up Environment Vairables

- Copy .env.example to .env and update values as needed.

### 3. Run the Application

- Using Docker Desktop, Podman, or Docker Compose:

```bash
docker-compose up --build
```

### 4. Access the Services 

- SSL-Checker App: http://localhost:8000/
- pgAdmin: http://localhost:5050/
    - pgAdmin login:
        - **Email:** `admin@example.com`
        - **Password:** `admin`

- fastAPI Docs: http://localhost:8000/docs


### 5. Setting up pgAdmin

- If you prefer using an external PostgreSQL instance, change the DATABASE_URL in .env accordingly.

- Once in, rightclick on Servers -> Register -> Server
    - Choose a name -> Connection
        - **Host name/address:** `postgres`
        - **Port:** `5432`
        - **Username:** `ssl_user`
        - **Password:** `ssl_user123`
    - Save

### 6. Alembic Migrations

- Alembic will apply migrations by default every time you restart the containers, if you wish to create a migration:
 
 - Windows
    - Create migration only:
        ```bash
        bash migrate.sh "Add table"
        ```
    - Create and apply:
        ```bash
        bash migrate.sh "Add table" --apply
        ```
    - or
        ```bash
        bash migrate.sh "Add table" -a
        ```

 - Git Bash / WSL / Linux Terminal
    - Create migration only:
        ```bash
        ./migrate.sh "Add table"
        ```
    - Create and apply:
        ```bash
        ./migrate.sh "Add table" --apply
        ```
    - or
        ```bash
        ./migrate.sh "Add table" -a
        ```

### 7. Shutting down and cleaning up

- You can safely shutdown the containers by entering CTRL-C in the terminal window docker is running in.

- To stop and remove containers:
    ```bash
    docker-compose down
    ```
- To remove volumes (PostgreSQL data):
    ```bash
    docker-compose down -v
    ```
## Email Notifications

- Uses SendGrid to send SSL and TSL expiry notifications.
- Set your API key in the .env file.
- Emails are sent to the address associated with each website entry.

### Authentication

Default test credentials:

**Admin**
- User: `admin`
- Password: `admin123`

**User**
- User: `user`
- Password: `user123`

You can change the password for the two users created in the .env file you should have created earlier.
You can register new users via the web UI. Admin users can promote others after logging in.
