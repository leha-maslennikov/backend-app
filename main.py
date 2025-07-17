import time
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Form, status, HTTPException, Cookie
from fastapi.responses import RedirectResponse, FileResponse

from src.auth import by_login, by_token

try:
    from config import conf
except:
    exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    hash_manager = by_login.BcryptHashManager()
    user_storage = by_login.SQLAlchemyUserStorage(
        by_login.init_sqlalchemy(conf.DB_URI, echo=False)
    )
    login_service = by_login.Service(hash_manager, user_storage)

    if not await login_service.verify(conf.ROOT_LOGIN, conf.ROOT_PASSWORD):
        await login_service.create_user(conf.ROOT_LOGIN, conf.ROOT_PASSWORD)

    token_storage = by_token.JWTStorage(
        conf.SECRET_KEY, by_token.init_sqlalchemy(conf.DB_URI, echo=False)
    )
    token_service = by_token.Service(token_storage)

    app.state.login_service = login_service
    app.state.token_service = token_service

    yield

    app.state.login_service = None
    app.state.token_service = None


app = FastAPI(lifespan=lifespan)


@app.get("/auth/check")
async def auth_check(token: str = Cookie(None)):
    """NGINX subrequest authentication"""
    if not token or not await app.state.token_service.verify_token(token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return True


@app.get("/auth/login")
async def login_form(token: str = Cookie(None)):
    """Страница для ввода логина и пароля"""
    if token and await app.state.token_service.verify_token(token):
        return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
    return FileResponse("public/login.html")


@app.post("/auth/login")
async def login(token: str = Cookie(None), login=Form(), password=Form()):
    """Аутентификация пользователя"""
    if token and await app.state.token_service.verify_token(token):
        return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
    if not await app.state.login_service.verify(login=login, password=password):
        return FileResponse("public/error_login.html")
    user = await app.state.login_service.get(login=login)
    token = await app.state.token_service.create_token(
        user.id, time.time() + 3600, "auth"
    )
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="token", value=token, secure=True, httponly=True)
    return response


@app.get("/auth/logout")
async def logout(token: str = Cookie(None)):
    response = RedirectResponse(url="/auth/login")
    if token:
        response.delete_cookie("token")
    return response


if __name__ == "__main__":
    try:
        uvicorn.run(
            app="main:app", host=conf.HOST, port=conf.PORT, workers=conf.WORKERS
        )
    except Exception as e:
        print(e)
