from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
import logging
from math import ceil
from threading import Thread
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


class SubnetScanner:
    network: IPv4Network
    devices: list[Device]
    _gateway_address: Optional[str]
    _source_port: RandShort
    _threads: int

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

    def __init__(self, network_cidr: str, threads=5):
        try:
            self._gateway_address = scapy_config.route.route('0.0.0.0')[2]
        except IndexError:
            self._gateway_address = None

        self._threads = threads
        self.devices = []
        self.network = IPv4Network(network_cidr)

    def scan(self) -> list[Device]:
        self.arp_scan()
        self.port_scan()
        return self.devices

    def arp_scan(self):
        self.devices = []
        batches = []

        address_list = list(self.network)

        batch_size = ceil(len(address_list) / self._threads)

        for i in range(0, len(address_list), batch_size):
            batches.append(address_list[i:i + batch_size])

        pool = list(map(lambda batch: Thread(target=self._arp_scan_batch, args=(batch,)), batches))

        for thread in pool:
            thread.start()

        for thread in pool:
            thread.join()

    def _arp_scan_batch(self, batch: list[IPv4Address]):
        for address in batch:
            self._arp_scan_single(address)

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

    def port_scan(self):
        self._source_port = RandShort()

        if not self.devices:
            return

        batches = []

        batch_size = ceil(len(self.devices) / self._threads)

        for i in range(0, len(self.devices), batch_size):
            batches.append(self.devices[i:i + batch_size])

        pool = list(map(lambda batch: Thread(target=self._port_scan_batch, args=(batch,)), batches))

        for thread in pool:
            thread.start()

        for thread in pool:
            thread.join()

    def _port_scan_batch(self, batch: list[Device]):
        for device in batch:
            self._port_scan_single(device)

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
                device.ports.append((config.ports[str(port)], port))  # noqa

                sr1(
                    IP(dst=device_ip_string) / TCP(sport=self._source_port, dport=port, flags='R'),
                    verbose=0,
                    timeout=0,
                )
