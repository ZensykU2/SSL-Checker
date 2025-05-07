FROM python:3.11-slim


RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./migrate.sh /migrate.sh
RUN chmod +x /migrate.sh

COPY ./start.sh /start.sh
RUN chmod +x /start.sh

COPY ./app /app
COPY ./alembic.ini /app/alembic.ini
COPY ./alembic /alembic

CMD ["/bin/bash", "/start.sh"]
