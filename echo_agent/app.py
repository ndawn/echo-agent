from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import schedule
from tortoise.contrib.fastapi import register_tortoise

from echo_agent.config import Config
from echo_agent.discover.run import perform_scan, scan_continuously
from echo_agent.router import router


config = Config()


app = FastAPI()

app.include_router(router)

register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={'models': ['echo_agent.models']},
    generate_schemas=True,
    add_exception_handlers=True,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f'http://{config.server_hostname}',  # noqa
        f'https://{config.server_hostname}',  # noqa
        config.server_hostname,  # noqa
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def setup_periodic_scan():
    schedule.every().hour.do(perform_scan)
    app.extra['stop_discover'] = scan_continuously()


@app.on_event('shutdown')
def cancel_periodic_scan():
    if 'stop_discover' in app.extra:
        app.extra['stop_discover'].set()
