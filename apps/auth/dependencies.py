from typing import Annotated
from fastapi import Cookie, Request, Depends, HTTPException, status
from .models import security


async def get_user_token(
    token: str | None = Cookie(default=None),
) -> security.UserToken | None:
    """Возвращает токен, если он есть, иначе None"""
    if not token:
        return None
    try:
        return security.UserToken.decode(token)
    except Exception:
        return None


async def verify_user_token(
    token: Annotated[security.UserToken | None, Depends(get_user_token)],
) -> security.UserToken:
    """Проверка того, что пользователь авторизован, если да, то возвращает токен, иначе UnauthorizedEcxeption"""
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return token


async def verify_no_user_token(
    token: Annotated[security.UserToken | None, Depends(get_user_token)],
) -> security.UserToken:
    """Проверка того, что пользователь авторизован, если да, то возвращает токен, иначе UnauthorizedEcxeption"""
    if token:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    return token
