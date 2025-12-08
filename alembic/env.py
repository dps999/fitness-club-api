import asyncio

from sqlalchemy.engine import Connection

from alembic import context
from app.core.config import get_settings
from app.core.database import make_engine
from app.models import Base


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_online(url: str) -> None:
    engine = make_engine(url)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(run_migrations)
    finally:
        await engine.dispose()


def main() -> None:
    url = context.config.attributes.get("database_url") or str(get_settings().database_url)
    if context.is_offline_mode():
        context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
    else:
        asyncio.run(run_online(url))


main()
