import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

from app import models  # Hier wird die Base importiert
from app.database import SQLALCHEMY_DATABASE_URL  # Deine Datenbankverbindung

# App-Pfad hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# .env laden
from dotenv import load_dotenv
load_dotenv()

# Alembic Config laden
config = context.config
fileConfig(config.config_file_name)

# Datenbank-URL setzen
config.set_main_option('sqlalchemy.url', SQLALCHEMY_DATABASE_URL)

# Ziel-Metadaten für Alembic
target_metadata = models.Base.metadata  # Models Base verwenden


def run_migrations_offline() -> None:
    """Führe Migrationen im Offline-Modus aus.

    Dies konfiguriert den Kontext mit nur einer URL und nicht einem Engine-Objekt,
    aber ein Engine-Objekt ist auch hier akzeptabel.
    Durch das Überspringen der Engine-Erstellung benötigen wir nicht einmal ein DBAPI.

    Calls to context.execute() hier geben den gegebenen String an das Skriptausgabe aus.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Führe Migrationen im Online-Modus aus.

    Hier müssen wir einen Engine erstellen und eine Verbindung mit dem Kontext herstellen.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# Hier wird entschieden, ob im Offline- oder Online-Modus migriert werden soll
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
