import typing as tp

from aiohttp import web

from app.utils import cbr


class AppContext:
    def __init__(self, cbr_client: cbr.BaseCBRClient):
        self.cbr_client = cbr_client

    async def on_startup(self, app: tp.Optional[web.Application] = None) -> tp.NoReturn:
        await self.cbr_client.start()

    async def on_shutdown(
            self, app: tp.Optional[web.Application] = None
    ) -> tp.NoReturn:
        await self.cbr_client.close()
