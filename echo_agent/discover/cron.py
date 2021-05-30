import aiohttp
from arq import cron

from echo_agent.config import Config
from echo_agent.discover.scanner import AsyncScanner


async def scan_regularly(ctx):
    scanned_devices = await ctx['scanner'].scan()

    try:
        async with aiohttp.request(
                'POST',
                f'{ctx["config"].server_hostname}/api/devices/from_scan',
                json={
                    'devices': [device.serialize() for device in scanned_devices],
                    'token': ctx['config'].token,
                }
        ):
            pass
    except:  # noqa
        pass


async def startup(ctx):
    ctx['config'] = Config()
    ctx['scanner'] = AsyncScanner(ctx['config'].subnet)  # noqa


class WorkerSettings:
    cron_jobs = [cron(scan_regularly, hour=0)]  # noqa
    on_startup = startup
