"""Migration credentials are injected, not stored in alembic.ini."""

import os

from alembic import context
from sqlalchemy import create_engine

from uaw.infrastructure.db.models import Base

database_url = os.environ.get("UAW_DATABASE_URL")
if not database_url or not database_url.startswith("postgresql+psycopg://"):
    raise RuntimeError("UAW_DATABASE_URL must name a configured PostgreSQL database")

if context.is_offline_mode():
    raise RuntimeError("Offline SQL generation is not enabled for this initial migration")

engine = create_engine(database_url, echo=False, hide_parameters=True)
try:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
finally:
    engine.dispose()

