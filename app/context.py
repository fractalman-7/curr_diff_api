import typing as tp

from aiohttp import web


class AppContext:
    def __init__(self):
        pass

    async def on_startup(self, app: tp.Optional[web.Application] = None) -> tp.NoReturn:
        pass

    async def on_shutdown(
        self, app: tp.Optional[web.Application] = None
    ) -> tp.NoReturn:
        pass
