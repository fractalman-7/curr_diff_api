import asyncio

from aiohttp import web

from app import dto
from app.context import AppContext


async def handle(request: web.Request, context: AppContext) -> web.Response:
    params = dto.CurrencyRatesDifferenceParameters.from_query(request.rel_url.query)
    if (
            params.currency_code is None
            or params.to_date is None
            or params.from_date is None
            or params.to_date < params.from_date
    ):
        return web.HTTPBadRequest(reason="Invalid parameters")
    rate_from, rate_to = await asyncio.gather(
        context.cbr_client.get_currency_rate_relative_rub(
            params.currency_code, params.from_date
        ),
        context.cbr_client.get_currency_rate_relative_rub(
            params.currency_code, params.to_date
        ),
    )
    if rate_from is None or rate_to is None:
        return web.HTTPBadRequest(reason="No data")
    return web.json_response(
        dto.CurrencyRatesDifference(
            str(rate_from), str(rate_to), str(abs(rate_from - rate_to))
        ).to_dict()
    )
