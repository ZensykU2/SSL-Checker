FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./package.json ./package-lock.json ./
RUN npm install

COPY ./migrate.sh /migrate.sh
RUN chmod +x /migrate.sh

COPY ./start.sh /start.sh
RUN chmod +x /start.sh

RUN apt-get update && apt-get install -y dos2unix && dos2unix /start.sh

COPY ./app /app
COPY ./alembic.ini /app/alembic.ini
COPY ./alembic /alembic

CMD ["/bin/bash", "/start.sh"]
