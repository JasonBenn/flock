import asyncio
import json
import os
import re
from datetime import datetime
from json import JSONDecodeError
from random import shuffle
from typing import List
from typing import Tuple

import attr
import backoff
import pytz
import requests
import sentry_sdk

# Init location, Sentry
RASPBERRY_PI_LOCATION_DIRPATH = "/home/pi/.config/flock"
location = os.listdir(RASPBERRY_PI_LOCATION_DIRPATH)[0]
sentry_sdk.init("https://c3f1f286f7964d6b8761fee94f1fc73d@sentry.io/1758125", environment=f"sensor_{location}")
BASE_URL = "https://flock.archive.house"
RSSI_REGEX = re.compile("RSSI return value: (-?\d+)\n")

session = requests.Session()


MacAddress = str
PersonName = str


@attr.s
class ScanResult:
    scanned_at: datetime = attr.ib()
    rssi: int = attr.ib()
    mac: str = attr.ib()


async def scan_mac(mac_tup: Tuple[MacAddress, PersonName]) -> ScanResult:
    mac, name = mac_tup
    print(f"  {mac} ping...", flush=True)
    scanned_at = datetime.now(pytz.UTC)
    proc = await asyncio.create_subprocess_shell(
        f"sudo hcitool cc {mac} && hcitool rssi {mac} && sudo hcitool dc {mac}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    match = RSSI_REGEX.match(stdout.decode("utf-8"))
    rssi = None
    if match:
        rssi = int(match.group(1))
        print(f"    ✅ {mac} ({name}): {rssi}", flush=True)
    else:
        print(f"    ❌ {mac} ({name}): {stdout} ({stderr})", flush=True)
    return ScanResult(scanned_at=scanned_at, rssi=rssi, mac=mac)


@backoff.on_exception(backoff.expo, (requests.exceptions.ConnectionError, JSONDecodeError), max_tries=8)
async def post_scans(scan_results: List[ScanResult]) -> int:
    data = json.dumps({"location": location, "scan_results": [attr.asdict(x) for x in scan_results]}, default=str)
    return session.post(f"{BASE_URL}/scans", data).status_code


def reboot():
    os.system("sudo shutdown -r now")


async def scan_macs(mac_tups: List[Tuple[MacAddress, PersonName]]):
    scan_results = await asyncio.gather(*[scan_mac(x) for x in mac_tups])
    try:
        response_code = await post_scans(scan_results)
    except requests.exceptions.ConnectionError:
        return reboot()
    print(f"Sent {scan_results}, response code {response_code}", flush=True)


def load_macs():
    try:
        mac_request = get_macs()
    except requests.exceptions.ConnectionError:
        return reboot()
    macs = json.loads(mac_request.text)
    print(f"GET {len(macs)} macs total", flush=True)
    return macs


@backoff.on_exception(backoff.expo, (requests.exceptions.ConnectionError, JSONDecodeError), max_tries=8)
def get_macs():
    return session.get(f"{BASE_URL}/macs")


async def main():
    while True:
        macs = load_macs()
        mac_tups = list(macs.items())
        shuffle(mac_tups)
        for x in mac_tups:
            await scan_macs([x])
            await asyncio.sleep(2)


asyncio.run(main())
