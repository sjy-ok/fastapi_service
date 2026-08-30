from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.middleware.request_context import RequestContextMiddleware


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(router)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/", include_in_schema=False)
    async def frontend() -> FileResponse:
        return FileResponse("app/static/index.html")

    register_exception_handlers(app)
    return app


app = create_app()
