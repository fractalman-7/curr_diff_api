import typing as tp

from aiohttp import web

from app.api.v1 import ping
from app.context import AppContext


def wrap_handler(
    handler: tp.Callable[[web.Request, AppContext], tp.Awaitable[web.Response]],
    context: AppContext,
) -> tp.Callable[[web.Request], tp.Awaitable[web.Response]]:
    async def wrapper(request: web.Request) -> web.Response:
        return await handler(request, context)

    return wrapper


def setup_routes(app: web.Application, context: AppContext) -> tp.NoReturn:
    app.router.add_get(
        "/v1/ping",
        wrap_handler(ping.handle, context),
    )
