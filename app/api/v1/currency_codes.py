from aiohttp import web

from app.context import AppContext


async def handle(request: web.Request, context: AppContext) -> web.Response:
    currency_codes = await context.cbr_client.get_currency_codes()
    return web.json_response({"codes": currency_codes})
