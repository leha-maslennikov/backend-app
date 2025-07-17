import time
from fastapi import APIRouter, Form, status, HTTPException, Cookie
from fastapi.responses import RedirectResponse, FileResponse
from src.auth import by_login, by_token


def init_auth_app(login_service: by_login.Service, token_service: by_token.Service):
    app = APIRouter(prefix="/auth", tags=["Authentication"])

    @app.get("/check")
    async def auth_check(token: str = Cookie(None)):
        """NGINX subrequest authentication"""
        if not token or not await token_service.verify_token(token):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        return True

    @app.get("/login")
    async def login_form(token: str = Cookie(None)):
        """Страница для ввода логина и пароля"""
        if token and await token_service.verify_token(token):
            return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
        return FileResponse("public/login.html")

    @app.post("/login")
    async def login(token: str = Cookie(None), login=Form(), password=Form()):
        """Аутентификация пользователя"""
        if token and await token_service.verify_token(token):
            return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
        if not await login_service.verify(login=login, password=password):
            return FileResponse("public/error_login.html")
        user = await login_service.get(login=login)
        token = await token_service.create_token(user.id, time.time() + 3600, "auth")
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="token", value=token, secure=True, httponly=True)
        return response

    @app.get("/logout")
    async def logout(token: str = Cookie(None)):
        response = RedirectResponse(url="/auth/login")
        if token:
            response.delete_cookie("token")
        return response

    return app
