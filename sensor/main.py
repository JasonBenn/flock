import asyncio
import re
import json
import os
from random import shuffle
from typing import Optional, Tuple, List

import requests
import sentry_sdk

# Init location, Sentry
RASPBERRY_PI_LOCATION_DIRPATH = "/home/pi/.config/flock"
location = os.listdir(RASPBERRY_PI_LOCATION_DIRPATH)[0]
sentry_sdk.init("https://c3f1f286f7964d6b8761fee94f1fc73d@sentry.io/1758125", environment=f"sensor_{location}")
BASE_URL = "https://flock.archive.house"
RSSI_REGEX = re.compile("RSSI return value: (-?\d+)\n")
stdout = b"RSSI return value: -1\n"

session = requests.Session()


MacAddress = str
PersonName = str


async def ping_mac(mac_tup: Tuple[MacAddress, PersonName]) -> Optional[int]:
    mac, name = mac_tup
    print(f"  {mac} ping...", flush=True)
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
    return rssi


async def post_scans(macs):
    data = {"location": location, "macs": macs}
    response_code = None
    try:
        post_request = session.post(f"{BASE_URL}/scans", data=json.dumps(data))
        response_code = post_request.status_code
    except requests.exceptions.ConnectionError as e:
        print(f"Fail 1... {e}", flush=True)
        try:
            post_request = session.post(f"{BASE_URL}/scans", data=json.dumps(data))
            response_code = post_request.status_code
        except requests.exceptions.ConnectionError as e:
            print(f"Fail 1... {e}", flush=True)
            try:
                post_request = session.post(f"{BASE_URL}/scans", data=json.dumps(data))
                response_code = post_request.status_code
            except requests.exceptions.ConnectionError as e:
                print(f"Fail 1... {e}", flush=True)
                try:
                    post_request = session.post(f"{BASE_URL}/scans", data=json.dumps(data))
                    response_code = post_request.status_code
                except requests.exceptions.ConnectionError as e:
                    print(f"🙄 Giving up! {e}", flush=True)
    return response_code


async def ping_macs(mac_tups: List[Tuple[MacAddress, PersonName]]):
    ping_outputs = await asyncio.gather(*[ping_mac(x) for x in mac_tups])
    macs = [x[0] for x in mac_tups]
    found_macs = {mac: rssi for mac, rssi in zip(macs, ping_outputs) if rssi}
    response_code = await post_scans(found_macs)
    print(f"Sent {found_macs}, response code {response_code}", flush=True)


def load_macs():
    mac_request = session.get(f"{BASE_URL}/macs")
    macs = json.loads(mac_request.text)
    print(f"GET {len(macs)} macs total", flush=True)
    return macs


async def main():
    while True:
        macs = load_macs()
        mac_tups = list(macs.items())
        shuffle(mac_tups)
        for x in mac_tups:
            await ping_macs([x])
            await asyncio.sleep(2)


asyncio.run(main())
