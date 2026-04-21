# app/main.py 


from fastapi import FastAPI

from db.multitenancy import MultiTenantMiddleware
from app.api.router import router as api_router


def create_app() -> FastAPI:
    """
    Application factory.
    Keeps main clean and supports testing, scaling, and future configs.
    """

    app = FastAPI(
        title="School ERP",
        version="1.0.0",
    )

    # ---------------------------------
    # Middleware
    # ---------------------------------

    app.add_middleware(MultiTenantMiddleware)

    # ---------------------------------
    # Routers
    # ---------------------------------

    app.include_router(api_router)

    # ---------------------------------
    # Health check
    # ---------------------------------

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok"}

    return app


# ---------------------------------
# App instance
# ---------------------------------

app = create_app()