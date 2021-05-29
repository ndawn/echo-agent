import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
import logging
from typing import Optional, Union

from scapy.config import conf as scapy_config
from scapy.layers.l2 import ARP, Ether, srp1
from scapy.layers.inet import IP, TCP, sr1
from scapy.volatile import RandShort

from echo_agent.config import Config

config = Config()
logger = logging.getLogger()


@dataclass
class Device:
    ip: IPv4Address
    mac: str
    ports: []
    is_gateway: bool

    def serialize(self) -> dict[str, Union[str, list[int]]]:
        return {
            'ip': str(self.ip),
            'mac': self.mac,
            'ports': self.ports,
            'is_gateway': self.is_gateway,
        }


class AsyncScanner:
    network: IPv4Network
    devices: list[Device]
    _executor: ThreadPoolExecutor
    _gateway_address: Optional[str]
    _loop: asyncio.AbstractEventLoop
    _source_port: RandShort

    _executor_workers: int = 5
    _arp_timeout: Union[int, float] = 0.2
    _tcp_timeout: Union[int, float] = 2

    _tcp_scan_methods: dict[str, str, Optional[str]] = {
        'SYN': ('S', '_check_syn_ack', 'AR'),
        'SYN Stealth': ('S', '_check_syn_ack', 'R'),
        # 'XMAS': ('FPU', '_check_none', None),
        # 'FIN': ('F', '_check_none', None),
        # 'NULL': ('', '_check_none', None),
        # 'Window': ('S', '_check_window', None),
    }

    def __init__(self, network_cidr: str):
        self._executor = ThreadPoolExecutor(max_workers=self._executor_workers)
        self._loop = asyncio.get_event_loop()

        try:
            self._gateway_address = scapy_config.route.route('0.0.0.0')[2]
        except IndexError:
            self._gateway_address = None

        self.devices = []
        self.network = IPv4Network(network_cidr)

    async def scan(self) -> list[Device]:
        await self.arp_scan()
        await self.port_scan()
        return self.devices

    async def arp_scan(self):
        self.devices = []
        await self._arp_scan()

    async def port_scan(self):
        self._source_port = RandShort()
        await self._port_scan()

    async def _arp_scan(self):
        await asyncio.wait(
            fs={
                self._loop.run_in_executor(self._executor, self._arp_scan_single, address)
                for address in self.network
            },
            return_when=asyncio.ALL_COMPLETED,
        )

    def _arp_scan_single(self, address: IPv4Address):
        logger.info(f'ARP scanning {address}...')

        answer = srp1(
            Ether(dst='ff:ff:ff:ff:ff:ff') / ARP(pdst=str(address)),
            verbose=0,
            filter='arp and arp[7] = 2',
            timeout=self._arp_timeout,
            iface_hint=str(address),
        )

        if answer is not None:
            self.devices.append(
                Device(
                    ip=address,
                    mac=answer.src,
                    ports=[],
                    is_gateway=address == self._gateway_address,
                )
            )

    async def _port_scan(self):
        if not self.devices:
            return

        await asyncio.wait(
            fs={
                self._loop.run_in_executor(self._executor, self._port_scan_single, device)
                for device in self.devices
            },
            return_when=asyncio.ALL_COMPLETED,
        )

    def _port_scan_single(self, device: Device):
        device_ip_string = str(device.ip)

        for port_ in config.ports:  # noqa
            port = int(port_)

            logger.info(f'TCP SYN stealth scanning port {port} at {device_ip_string}...')

            answer = sr1(
                IP(dst=device_ip_string) / TCP(sport=self._source_port, dport=port, flags='S'),
                verbose=0,
                timeout=self._tcp_timeout,
                )

            if (answer is not None) and (answer.haslayer(TCP)) and (answer.getlayer(TCP).flags == 0x12):
                device.ports.append((config.ports[port], port))  # noqa

                sr1(
                    IP(dst=device_ip_string) / TCP(sport=self._source_port, dport=port, flags='R'),
                    verbose=0,
                    timeout=0,
                )
