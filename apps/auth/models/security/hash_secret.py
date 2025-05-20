from passlib.context import CryptContext
import logging

# Отключение предупреждения об ошибке чтения версии
logging.getLogger("passlib").setLevel(logging.ERROR)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(secret: str) -> str:
    """хэширование параметра secret"""
    return pwd_context.hash(secret)


def verify(secret: str, hash: str) -> bool:
    """проверка соответствует ли параметр secret параметру hash"""
    return pwd_context.verify(secret, hash)
