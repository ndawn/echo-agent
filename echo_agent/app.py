from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
import uvicorn

from echo_agent.config import Config
from echo_agent.discover.run import scan_continuously
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
    app.extra['cancel_discover_scheduling'] = scan_continuously()


@app.on_event('shutdown')
def cancel_periodic_scan():
    if 'cancel_discover_scheduling' in app.extra:
        app.extra['cancel_discover_scheduling'].set()


if __name__ == '__main__':
    if config.insecure:  # noqa
        ssl_config = {}
    else:
        ssl_config = {
            'ssl_keyfile': './ssl/key.pem',
            'ssl_certfile': './ssl/cert.pem',
        }

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=11007,
        **ssl_config,
    )
