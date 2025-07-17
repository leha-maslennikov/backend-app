from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Token:
    user_id: int
    expires: int
    action: str
    token: str


class BaseTokenStorage(ABC):

    @abstractmethod
    async def create(self, user_id: int, expires: int, action: str) -> str: ...

    @abstractmethod
    async def get(self, token: str) -> Token | None: ...

    @abstractmethod
    async def revoke(self, user_id: int): ...


class Service:
    _tokens: BaseTokenStorage

    def __init__(self, tokens: BaseTokenStorage):
        self._tokens = tokens

    async def create_token(self, user_id: int, expires: int, action: str) -> str:
        return await self._tokens.create(user_id, expires, action)

    async def verify_token(self, token: str) -> Token | None:
        return await self._tokens.get(token)

    async def revoke(self, user_id: int):
        await self._tokens.revoke(user_id)


# JWT + SQLAlchemy Token Storage

import jwt, sqlalchemy, sqlalchemy.orm as orm, time


class Base(orm.DeclarativeBase):
    pass


class SQLAlchemyToken(Base):
    __tablename__ = "tokens"

    user_id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    version: orm.Mapped[int]


class JWTStorage(BaseTokenStorage):
    _key: str
    _session: orm.sessionmaker[orm.Session]

    def __init__(self, key: str, session: orm.sessionmaker[orm.Session]):
        self._key = key
        self._session = session

    async def create(self, user_id: int, expires: int, action: str) -> str:
        with self._session() as session:
            token = session.execute(
                sqlalchemy.select(SQLAlchemyToken).where(
                    SQLAlchemyToken.user_id == user_id
                )
            ).scalar_one_or_none()
            if token:
                version = token.version
            else:
                version = 1
                session.add(SQLAlchemyToken(user_id=user_id, version=version))
                session.commit()
        return jwt.encode(
            {
                "user_id": user_id,
                "expires": expires,
                "action": action,
                "version": version,
            },
            self._key,
            algorithm="HS256",
        )

    async def get(self, token: str) -> Token | None:
        jwt_token: dict = jwt.decode(token, self._key, algorithms=["HS256"])
        if jwt_token["expires"] <= time.time():
            return None
        with self._session() as session:
            token_version = session.execute(
                sqlalchemy.select(SQLAlchemyToken).where(
                    SQLAlchemyToken.user_id == jwt_token["user_id"]
                )
            ).scalar_one_or_none()
            if not token_version or (token_version.version != jwt_token["version"]):
                return None
        jwt_token["token"] = token
        jwt_token.pop("version")
        return Token(**jwt_token)

    async def revoke(self, user_id: int):
        with self._session() as session:
            token = session.execute(
                sqlalchemy.select(SQLAlchemyToken).where(
                    SQLAlchemyToken.user_id == user_id
                )
            ).scalar_one_or_none()
            if token:
                token.version += 1
                session.add(token)
                session.commit()


def init_sqlalchemy(url: str = "sqlite://", echo: bool = True, create_all: bool = True):
    engine = sqlalchemy.create_engine(url, echo=echo)
    if create_all:
        Base.metadata.create_all(engine)
        """with orm.Session(engine) as session:
            session.add(SQLAlchemyToken(user_id=0, version=1))
            session.commit()"""
    return orm.sessionmaker(engine)
