"""AuthMiddleware — V0.1 stub, full JWT/OAuth in V1.0."""

from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        return await call_next(request)
