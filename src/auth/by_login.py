import abc, dataclasses


@dataclasses.dataclass
class User:
    id: int
    login: str
    password: str


class BaseUserStorage(abc.ABC):

    @abc.abstractmethod
    async def add(self, user: User): ...

    @abc.abstractmethod
    async def get(self, **kwds) -> User | None: ...

    @abc.abstractmethod
    async def filter(
        self, limit: int = None, offset: int = None, /, **kwds
    ) -> list[User]: ...

    @abc.abstractmethod
    async def delete(self, **kwds): ...


class BaseHashManager(abc.ABC):
    @abc.abstractmethod
    def hash(self, password: str) -> str: ...

    @abc.abstractmethod
    def verify(self, password: str, hash: str) -> bool: ...


class UserExists(Exception): ...


class UserNotExists(Exception): ...


class Service:
    _hash_manager: BaseHashManager
    _users: BaseUserStorage

    def __init__(self, hash_manager: BaseHashManager, users: BaseUserStorage):
        self._hash_manager = hash_manager
        self._users = users

    async def create_user(self, login: str, password: str):
        user = await self._users.get(login=login)
        if user:
            raise UserExists(user)
        return await self._users.add(
            User(None, login, self._hash_manager.hash(password))
        )

    async def update_user(
        self, user_id: int, *, login: str = None, password: str = None
    ):
        user = await self._users.get(id=user_id)
        if not user:
            raise UserNotExists(f"user_id = {user_id}")
        if login:
            if await self._users.get(login=login) != None:
                raise UserExists()
            user.login = login
        if password:
            user.password = self._hash_manager.hash(password)
        await self._users.add(user)

    async def delete_user(self, user_id: int):
        await self._users.delete(id=user_id)

    async def get(self, **kwds) -> User | None:
        return await self._users.get(**kwds)

    async def get_all(self, limit: int = None, offset: int = None) -> list[User]:
        return await self._users.filter(limit, offset)

    async def verify(self, login: str, password: str) -> bool:
        user = await self._users.get(login=login)
        if not user:
            return False
        return self._hash_manager.verify(password, user.password)


# SQLAlchemy User Storage

import sqlalchemy, sqlalchemy.orm as orm


class Base(orm.DeclarativeBase):
    pass


class SQLAlchemyUser(Base):
    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    login: orm.Mapped[str]
    password: orm.Mapped[str]


class SQLAlchemyUserStorage(BaseUserStorage):

    def __init__(self, session: orm.sessionmaker[orm.Session]):
        self._session = session

    async def add(self, user: User):
        with self._session() as session:
            if user.id == None:
                session.add(SQLAlchemyUser(login=user.login, password=user.password))
            else:
                u = session.execute(
                    sqlalchemy.select(SQLAlchemyUser).where(
                        SQLAlchemyUser.id == user.id
                    )
                ).scalar_one_or_none()
                if not u:
                    raise UserNotExists(f"{user.id=}")
                u.login = user.login
                u.password = user.password
                session.add(u)
            session.commit()

    async def get(self, **kwds) -> User | None:
        stmt = sqlalchemy.select(SQLAlchemyUser)
        for k, v in kwds.items():
            stmt = stmt.where(getattr(SQLAlchemyUser, k) == v)
        with self._session() as session:
            user = session.execute(stmt).scalar_one_or_none()
            if user:
                return User(user.id, user.login, user.password)

    async def filter(
        self, limit: int = None, offset: int = None, /, **kwds
    ) -> list[User]:
        stmt = sqlalchemy.select(SQLAlchemyUser)
        for k, v in kwds.items():
            stmt = stmt.where(getattr(SQLAlchemyUser, k) == v)
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        with self._session() as session:
            return [
                User(user.id, user.login, user.password)
                for user in session.execute(stmt).scalars()
            ]

    async def delete(self, **kwds):
        stmt = sqlalchemy.delete(SQLAlchemyUser)
        for k, v in kwds.items():
            stmt = stmt.where(getattr(SQLAlchemyUser, k) == v)
        with self._session() as session:
            session.execute(stmt)
            session.commit()


def init_sqlalchemy(url: str = "sqlite://", echo: bool = True, create_all: bool = True):
    engine = sqlalchemy.create_engine(url, echo=echo)
    if create_all:
        Base.metadata.create_all(engine)
    return orm.sessionmaker(engine)


from passlib.hash import bcrypt


class BcryptHashManager(BaseHashManager):
    def hash(self, password: str) -> str:
        return bcrypt.hash(password)

    def verify(self, password: str, hash: str) -> bool:
        return bcrypt.verify(password, hash)
