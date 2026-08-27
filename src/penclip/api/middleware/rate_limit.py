"""RateLimitMiddleware — V0.1 stub, token-bucket in V1.0."""

from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        return await call_next(request)
