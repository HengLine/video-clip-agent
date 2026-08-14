"""LoggingMiddleware — request/response logging."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from neoclip.logger import debug


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed = (time.time() - start) * 1000
        debug(f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.1f}ms)")
        return response
