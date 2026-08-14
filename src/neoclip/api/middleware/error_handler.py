"""ErrorHandlerMiddleware — global error handling."""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from neoclip.logger import error


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            error(f"Unhandled error: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})
