import os
from collections.abc import AsyncIterator

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url

from alembic import command
from app.core.database import make_engine
from app.main import create_app


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.fail("Set TEST_DATABASE_URL to a dedicated PostgreSQL test database", pytrace=False)
    parsed = make_url(url)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or not parsed.database
        or not parsed.database.endswith("_test")
    ):
        pytest.fail(
            "TEST_DATABASE_URL must use asyncpg and a database ending in _test", pytrace=False
        )
    config = Config("alembic.ini")
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    return url


@pytest.fixture
async def api(test_database_url: str) -> AsyncIterator[AsyncClient]:
    application = create_app(test_database_url)
    engine = make_engine(test_database_url)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text("TRUNCATE bookings, memberships, classes, clients, trainers RESTART IDENTITY")
            )
    finally:
        await engine.dispose()

    async with (
        application.router.lifespan_context(application),
        AsyncClient(
            transport=ASGITransport(app=application), base_url="http://test/api/v1/"
        ) as api,
    ):
        yield api
