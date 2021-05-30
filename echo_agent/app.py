from crontab import CronTab
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
    modules={'models': ['echo_agent.models']},
)


@app.on_event('startup')
def ensure_periodic_scan():
    with CronTab('root') as cron:
        cron.remove_all(comment='echo_agent_discover')
        job = cron.new('python -m echo_agent.discover')
        job.set_comment('echo_agent_discover')
        job.every(5).minutes()
