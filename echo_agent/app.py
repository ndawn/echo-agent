from crontab import CronTab
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from echo_agent.config import Config
from echo_agent.router import router


config = Config()


app = FastAPI()

app.include_router(router)

register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={'models': ['echo_agent.models']},
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[f'http://{config.server_hostname}', f'https://{config.server_hostname}'],  # noqa
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def ensure_periodic_scan():
    with CronTab(tabfile='/etc/crontab') as cron:
        cron.remove_all(comment='echo_agent_discover')
        job = cron.new('python -m echo_agent.discover.run')
        job.set_comment('echo_agent_discover')
        job.every(5).minutes()
