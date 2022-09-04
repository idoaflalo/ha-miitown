import aiohttp
from aiohttp import ClientTimeout

DEFAULT_TIMEOUT = ClientTimeout(total=10)


async def get(session: aiohttp.ClientSession, url: str, headers: object):
    async with session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT) as response:
        return await response.json()


async def post(session: aiohttp.ClientSession, url: str, data: object, headers=None):
    async with session.post(url, json=data, headers=headers, timeout=DEFAULT_TIMEOUT) as response:
        return await response.json()
