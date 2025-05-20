from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class User(BaseModel):
    """Модель пользователя"""

    id: int | None = Field(default=None)
    login: str
    password: str | None = Field(default=None)
    group: str | None = Field(default=None)


class StorageException(Exception):
    """Ошибка, возникающая при работе хранилиша"""


class UserStorageABC(ABC):
    """Интерфейс для работы с хранилищем пользователей"""

    @classmethod
    @abstractmethod
    async def create_user(cls, user: User) -> User:
        """Создаёт пользователя, если его нет"""

    @classmethod
    @abstractmethod
    async def update_user(cls, user: User) -> User:
        """Обновляет данные пользователя"""

    @classmethod
    @abstractmethod
    async def get_user_by(cls, **filter) -> User | None:
        """Возвращает пользователя по заданному фильтру"""
