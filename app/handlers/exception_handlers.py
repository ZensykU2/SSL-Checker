from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse

async def auth_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login", status_code=303)
    raise exc
