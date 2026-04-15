# db/multitenancy.py


from sqlalchemy import text
from contextvars import ContextVar
from typing import Optional
import logging
from session import db_manager

# Context variable to store current school schema
current_school_schema: ContextVar[Optional[str]] = ContextVar('current_school_schema', default=None)
logger = logging.getLogger(__name__)

class MultiTenantMiddleware:
    """
    Middleware to set database schema based on request
    Usage in FastAPI:
        app.add_middleware(MultiTenantMiddleware)
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract school identifier from request (header, subdomain, or path)
        headers = dict(scope.get("headers", []))
        school_code = None
        
        # Try header first
        if b"x-school-code" in headers:
            school_code = headers[b"x-school-code"].decode()
        # Fallback to subdomain
        elif b"host" in headers:
            host = headers[b"host"].decode()
            if "." in host:
                subdomain = host.split(".")[0]
                if subdomain != "api" and subdomain != "www":
                    school_code = subdomain
        
        if school_code:
            # Get schema name from global.schools table
            with db_manager.session() as session:
                result = session.execute(
                    text("SELECT database_schema FROM global.schools WHERE code = :code AND is_active = TRUE"),
                    {"code": school_code}
                ).fetchone()
                
                if result:
                    current_school_schema.set(result[0])
                    logger.info(f"Set database schema to {result[0]} for school {school_code}")
                else:
                    logger.warning(f"Invalid school code: {school_code}")
                    # Set to default schema or raise error
        
        await self.app(scope, receive, send)

def set_school_schema(school_code: str):
    """Manual schema setting for background tasks"""
    with db_manager.session() as session:
        result = session.execute(
            text("SELECT database_schema FROM global.schools WHERE code = :code AND is_active = TRUE"),
            {"code": school_code}
        ).fetchone()
        
        if result:
            current_school_schema.set(result[0])
            # Set search_path for current session
            session.execute(text(f"SET search_path TO {result[0]}, public, global"))
            return True
    return False

def get_current_schema() -> str:
    """Get current school schema"""
    return current_school_schema.get() or "public"