import aiohttp

from .http_helper import get, post
from .const import BASE_URL, LOGIN_PATH, DEVICES_PATH, STATUS_PATH, REFRESH_TOKEN_INTERVAL
from .utils import format_devices, handle_response, AuthError


class MiitownApi:
    def __init__(self, session: aiohttp.ClientSession, authorization: dict = None):
        self._session = session
        self._authorization = authorization

    async def authentication(self, username, password) -> bool:
        login_body = {
            "username": username,
            "password": password,
            "rememberMe": False
        }
        login_response = await post(self._session, BASE_URL + LOGIN_PATH, login_body)
        handle_response(login_response)

        self._authorization = login_response["data"]
        return login_response["data"]

    async def fetch_devices(self) -> list[dict]:
        devices_response = await get(self._session, BASE_URL + DEVICES_PATH, {
            "token": self._get_token()
        })
        handle_response(devices_response)

        return devices_response["data"]

    async def fetch_devices_data(self, devices) -> list[dict]:
        devices_response = await get(self._session, BASE_URL + STATUS_PATH, {
            "token": self._get_token()
        })
        handle_response(devices_response)

        return format_devices(devices, devices_response["data"])

    def _get_token(self):
        if not self._authorization:
            raise AuthError()
        return self._authorization["token"]
