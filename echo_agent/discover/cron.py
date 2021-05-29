import aiohttp
from arq import cron

from echo_agent.config import Config
from echo_agent.discover.scanner import AsyncScanner


async def scan_regularly(ctx):
    scanned_devices = await ctx['scanner'].scan()

    async with aiohttp.request(
            'POST',
            # f'{ctx["config"].server_hostname}/api/devices/from_scan',
            f'{ctx["config"].server_hostname}/devices/from_scan',
            json={
                'devices': [device.serialize() for device in scanned_devices],
                'token': ctx['config'].token,
            }
    ):
        pass


async def startup(ctx):
    ctx['config'] = Config()
    ctx['scanner'] = AsyncScanner(ctx['config'].subnet)  # noqa


class WorkerSettings:
    # cron_jobs = [cron(scan_regularly, minute=0)]
    cron_jobs = [cron(scan_regularly, second={0, 10, 20, 30, 40, 50})]
    on_startup = startup
