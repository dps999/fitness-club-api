from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api import bookings, classes, clients, memberships, trainers
from app.core.database import make_engine
from app.services.common import BusinessError


def create_app(database_url: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(database_url)
        application.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            yield
        finally:
            await engine.dispose()

    application = FastAPI(title="Fitness Club API", version="0.1.0", lifespan=lifespan)

    @application.exception_handler(BusinessError)
    async def handle_business_error(_request: Request, error: BusinessError) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail})

    @application.exception_handler(IntegrityError)
    async def handle_integrity_error(_request: Request, error: IntegrityError) -> JSONResponse:
        constraint = getattr(error.orig.__cause__, "constraint_name", None)
        match constraint:
            case "uq_clients_email":
                status, detail = 409, "A client with this email already exists"
            case "uq_bookings_class_client":
                status, detail = 409, "The client is already booked for this class"
            case "fk_memberships_client" | "fk_bookings_client":
                status, detail = 404, "Client not found"
            case "fk_classes_trainer":
                status, detail = 404, "Trainer not found"
            case "fk_bookings_class":
                status, detail = 404, "Class not found"
            case "ck_memberships_date_order":
                status, detail = 422, "start_date must be on or before end_date"
            case _:
                raise error
        return JSONResponse(status_code=status, content={"detail": detail})

    for router in (
        clients.router,
        memberships.router,
        trainers.router,
        classes.router,
        bookings.router,
    ):
        application.include_router(router, prefix="/api/v1")
    return application


app = create_app()
