import os
import asyncio
import re
import json
from itertools import cycle
from typing import Optional

import requests

RASPBERRY_PI_LOCATION_DIRPATH = "/home/pi/.config/flock"
location = os.listdir(RASPBERRY_PI_LOCATION_DIRPATH)[0]

BASE_URL = "https://flock.archive.house"
RSSI_REGEX = re.compile("RSSI return value: (-?\d+)\n")

stdout = b'RSSI return value: -1\n'

async def ping_mac(mac: str) -> Optional[int]:
    print(f"  {mac} ping...")
    proc = await asyncio.create_subprocess_shell(
        f"sudo hcitool cc {mac} && hcitool rssi {mac} && sudo hcitool dc {mac}", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    match = RSSI_REGEX.match(stdout.decode('utf-8'))
    rssi = None
    if match:
        rssi = int(match.group(1))
        print(f"    ✅ {mac}: {rssi}")
    else:
        print(f"    ❌ {mac}: {stdout} ({stderr})")
    return rssi


async def post_scans(macs):
    data = {"location": location, "macs": macs}
    print(json.dumps(data))

    post_request = requests.post(f"{BASE_URL}/scans", data=json.dumps(data))
    return post_request.status_code


async def ping_macs(macs):
    ping_outputs = await asyncio.gather(*[ping_mac(x) for x in macs])
    found_macs = {mac: rssi for mac, rssi in zip(macs, ping_outputs) if rssi}
    response_code = await post_scans(found_macs)
    print(f"Sent {found_macs}, response code {response_code}")


def load_macs():
    mac_request = requests.get(f"{BASE_URL}/macs")
    macs = json.loads(mac_request.text)["macs"]
    print(f"GET {len(macs)} macs total")
    return macs


async def main():
    while True:
        macs = load_macs()
        # Pinging than 4 concurrently never found results ¯\_(ツ)_/¯
        slices = []
        for x in range(len(macs) // 4 + 1):
            lower = x * 4
            upper = min(x * 4 + 4, len(macs))
            slices.append(slice(lower, upper))

        for x in slices:
            await ping_macs(macs[x])
            await asyncio.sleep(20)


asyncio.run(main())
