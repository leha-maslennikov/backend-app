from typing import Annotated
from pydantic import BaseModel

from fastapi import APIRouter, Form, status, Depends, HTTPException
from fastapi.responses import RedirectResponse, FileResponse

from .models import user_storage, security
from . import dependencies


app = APIRouter(prefix="/auth", tags=["Authentication"])


@app.get("/check")
async def auth_check(
    token: Annotated[security.UserToken | None, Depends(dependencies.get_user_token)],
):
    """NGINX subrequest authentication"""
    if token:
        return True
    raise HTTPException(status.HTTP_401_UNAUTHORIZED)


@app.get("/login")
async def login_form(
    token: Annotated[security.UserToken | None, Depends(dependencies.get_user_token)],
):
    """Страница для ввода логина и пароля"""
    if token:
        return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
    return FileResponse("public/login.html")


class LoginForm(BaseModel):
    login: str
    password: str


@app.post("/login")
async def login(
    token: Annotated[security.UserToken | None, Depends(dependencies.get_user_token)],
    login=Form(),
    password=Form(),
):
    """Аутентификация пользователя"""
    if token:
        return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
    user = await user_storage.UserStorage.get_user_by(login=login)
    if not user or not security.verify(secret=password, hash=user.password):
        return FileResponse("public/error_login.html")
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="token",
        value=security.UserToken(
            user_id=user.id, login=user.login, group=user.group
        ).encode(),
        secure=True,
        httponly=True,
    )
    return response


@app.get("/logout")
async def logout(
    token: Annotated[security.UserToken | None, Depends(dependencies.get_user_token)],
):
    response = RedirectResponse(url="/auth/login")
    if token:
        response.delete_cookie("token")
    return response
