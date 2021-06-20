from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from tortoise.contrib.fastapi import register_tortoise

from echo_agent.config import Config
from echo_agent.discover.run import scan_continuously
from echo_agent.router import limiter, router


config = Config()


app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    app.extra['cancel_discover_scheduling'] = scan_continuously()


@app.on_event('shutdown')
def cancel_periodic_scan():
    if 'cancel_discover_scheduling' in app.extra:
        app.extra['cancel_discover_scheduling'].set()
