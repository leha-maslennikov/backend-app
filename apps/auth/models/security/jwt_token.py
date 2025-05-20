import jwt
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from config import cfg

SECRET_KEY = cfg.account_app.SECRET_KEY
ALGORITHM = cfg.account_app.ALGORITHM


class BaseToken(BaseModel):

    def encode(self) -> str:
        """преобразование токена к строке"""
        return jwt.encode(
            algorithm=ALGORITHM, key=SECRET_KEY, payload=self.model_dump()
        )

    @classmethod
    def decode(cls, token: str):
        """преобразование строки в токен"""
        return cls.model_validate(
            jwt.decode(algorithms=[ALGORITHM], key=SECRET_KEY, jwt=token)
        )


class UserToken(BaseToken):
    user_id: int
    login: str
    group: str
