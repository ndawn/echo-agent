import logging

import requests

from echo_agent.config import Config
from echo_agent.discover.scanner import SubnetScanner


config = Config()
logger = logging.getLogger('echo_agent_discover')


def perform_scan():
    logger.info('Starting device discover')

    scanned_devices = SubnetScanner(config.subnet).scan()  # noqa

    logger.info('Completed device discover')
    logger.info('Sending results to the server')

    try:
        request_data = {
            'devices': [device.serialize() for device in scanned_devices],
            'agent_token': config.token,  # noqa
        }

        logger.debug(f'{request_data=}')

        response = requests.post(
            f'http://{config.server_hostname}/api/devices/from_scan',  # noqa
            json=request_data,
        )

        logger.debug(f'{response.status_code=}')
        logger.debug(f'{response.text=}')
    except:  # noqa
        pass


if __name__ == '__main__':
    perform_scan()
