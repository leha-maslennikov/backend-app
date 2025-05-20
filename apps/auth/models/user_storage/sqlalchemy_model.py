from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import create_engine


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=True)
    group: Mapped[str] = mapped_column(nullable=True)


from config import cfg

engine = create_engine(url=cfg.account_app.db_uri, echo=False)
sessionmaker = sessionmaker(engine)


def init_users_db():
    """Инициализация структуры базы данных"""
    Base.metadata.create_all(engine)
