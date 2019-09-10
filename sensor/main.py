import asyncio
import json
from itertools import cycle

import requests
import sys

location = sys.argv[1]
assert location

BASE_URL = "http://flock.archive.house"


async def ping_mac(mac):
    print(f"  {mac} ping...")
    proc = await asyncio.create_subprocess_shell(
        f"hcitool name {mac}", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    print(f"  {mac} result: {stdout.strip()} {stderr}...")
    return stdout.strip(), stderr


async def post_scans(macs):
    data = {"location": location, "macs": macs}
    post_request = requests.post(f"{BASE_URL}/scans", data=json.dumps(data))
    return post_request.status_code


async def ping_macs(macs):
    ping_outputs = await asyncio.gather(*[ping_mac(x) for x in macs])
    found_macs = [mac for mac, (stdout, stderr) in zip(macs, ping_outputs) if len(stdout)]
    response_code = await post_scans(found_macs)
    print(f"Sent {len(found_macs)} macs, response code {response_code}")


def load_macs():
    mac_request = requests.get(f"{BASE_URL}/macs")
    macs = json.loads(mac_request.text)["macs"]
    print(f"GET {len(macs)} macs total")
    return macs


async def main():
    macs = load_macs()
    # Endless windows of 4 macs
    # Pinging than 4 concurrently never found results ¯\_(ツ)_/¯
    slices = []
    for x in range(len(macs) // 4 + 1):
        lower = x * 4
        upper = min(x * 4 + 4, len(macs))
        slices.append(slice(lower, upper))

    for x in cycle(slices):
        await ping_macs(macs[x])
        await asyncio.sleep(20)


asyncio.run(main())
