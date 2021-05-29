from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from echo_agent.config import Config
from echo_agent.router import router


config = Config()


app = FastAPI()

app.include_router(router)

register_tortoise(
    app,
    db_url=config.db_url,  # noqa
)
