import os
from typing import cast


def env_param(name: str, default=None, required: bool = False):
    val = os.environ.get(name)
    if val:
        if isinstance(default, int):
            val = int(val)
        return val
    if (default == None) and required:
        raise Exception(f"{name} is required")
    return default


class Config:
    PORT: int = env_param("PORT", 80)
    HOST: str = env_param("HOST", "0.0.0.0")
    WORKERS: int | None = env_param("WORKERS")

    # не менее 32 символов
    SECRET_KEY: str = env_param("SECRET_KEY", required=True)

    DB_URI: str = env_param("DB_URI", required=True)
    ROOT_LOGIN: str = env_param("ROOT_LOGIN", required=True)
    ROOT_PASSWORD: str = env_param("ROOT_PASSWORD", required=True)


conf = Config
