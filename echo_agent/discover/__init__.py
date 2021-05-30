import asyncio

import requests

from echo_agent.config import Config
from echo_agent.discover.scanner import AsyncScanner


config = Config()


def perform_scan():
    scanned_devices = asyncio.run(AsyncScanner(config.subnet).scan())  # noqa

    try:
        requests.post(
            f'{config.server_hostname}/api/devices/from_scan',  # noqa
            json={
                'devices': [device.serialize() for device in scanned_devices],
                'token': config.token,  # noqa
            },
        )
    except:  # noqa
        pass


if __name__ == '__main__':
    perform_scan()
