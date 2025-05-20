from fastapi import FastAPI

app = FastAPI()

import apps

app.include_router(apps.auth.app)


if __name__ == "__main__":
    from apps.auth.models.user_storage import (
        init_users_db,
        test_storage,
        create_root_user,
    )

    init_users_db()
    test_storage()
    create_root_user()

    import uvicorn
    from config import cfg

    try:
        uvicorn.run(app="main:app", host=cfg.host, port=cfg.port, workers=cfg.workers)
    except Exception as e:
        print(e)
