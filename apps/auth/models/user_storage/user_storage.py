from .user_storage_abc import User, UserStorageABC, StorageException
from . import sqlalchemy_model as sqlm
import sqlalchemy as sql


class UserStorage(UserStorageABC):

    @classmethod
    async def create_user(cls, user: User) -> User:
        with sqlm.sessionmaker() as session:
            db_user = await cls.get_user_by(login=user.login)
            if db_user:
                raise StorageException("user exists")
            db_user = sqlm.User(**user.model_dump())
            session.add(db_user)
            session.commit()
            return User.model_validate(db_user, from_attributes=True)

    @classmethod
    async def update_user(cls, user: User) -> User:
        with sqlm.sessionmaker() as session:
            db_user = session.execute(
                sql.select(sqlm.User).where(sqlm.User.id == user.id)
            ).scalar_one_or_none()
            if not db_user:
                raise StorageException("user not exists")
            dump = user.model_dump(exclude="id")
            for field in dump:
                db_user.__setattr__(field, dump[field])
            session.commit()
            return User.model_validate(db_user, from_attributes=True)

    @classmethod
    async def get_user_by(cls, **filter) -> User | None:
        stmt = sql.select(sqlm.User)
        for k, v in filter.items():
            stmt = stmt.where(getattr(sqlm.User, k) == v)
        with sqlm.sessionmaker() as session:
            db_user = session.execute(stmt).scalar_one_or_none()
            if db_user:
                return User.model_validate(db_user, from_attributes=True)


from config import cfg


def test_storage():
    UserStorage()


def create_root_user():

    async def __create_root_user__():
        from ..security import hash

        if not await UserStorage.get_user_by(login=cfg.account_app.root_login):
            await UserStorage.create_user(
                User(
                    login=cfg.account_app.root_login,
                    password=hash(cfg.account_app.root_password),
                    group="root",
                )
            )

    import asyncio

    asyncio.run(__create_root_user__())
