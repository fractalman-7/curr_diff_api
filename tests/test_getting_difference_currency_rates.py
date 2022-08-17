import pytest
from aiohttp import web

from app import routes
from app.context import AppContext
from app.utils import cbr

INCORRECT_PARAMS = [
    {"code": "USD", "from_date": "2010-01-01", "to_date": "2000-01-01"},
    {"code": "EUR", "from_date": "2010-01-01", "to_date": "01-01-2020"},
    {"from_date": "2000-01-01", "to_date": "2020-01-01"},
]

NO_DATA_PARAMS = [
    {"code": "AUD", "from_date": "1990-01-01", "to_date": "2010-01-01"},
    {"code": "AUD", "from_date": "2000-01-01", "to_date": "2090-01-01"},
    {"code": "XXX", "from_date": "1990-01-01", "to_date": "2090-01-01"},
]

CORRECT_PARAMS = [
    {"code": "USD", "from_date": "2010-01-01", "to_date": "2020-01-01"},
    {"code": "EUR", "from_date": "2000-01-01", "to_date": "2010-01-01"},
    {"code": "AUD", "from_date": "2000-01-01", "to_date": "2020-01-01"},
]
CORRECT_OUTPUT = [
    {"difference": "31.7206", "rate_from": "30.1851", "rate_to": "61.9057"},
    {"difference": "16.2605", "rate_from": "27.2000", "rate_to": "43.4605"},
    {"difference": "25.7535", "rate_from": "17.6300", "rate_to": "43.3835"},
]


@pytest.fixture
def client(loop, aiohttp_client):
    app = web.Application()

    context = AppContext(cbr_client=cbr.TestCBRClient())

    app.on_startup.append(context.on_startup)
    app.on_shutdown.append(context.on_shutdown)

    routes.setup_routes(app, context)

    return loop.run_until_complete(aiohttp_client(app))


@pytest.mark.asyncio
async def test_correct(client):
    for idx, params in enumerate(CORRECT_PARAMS):
        response = await client.get("/v1/currency_rate_diff", params=params)
        assert response.status == 200
        assert await response.json() == CORRECT_OUTPUT[idx]


@pytest.mark.asyncio
async def test_incorrect(client):
    for params in INCORRECT_PARAMS:
        response = await client.get("/v1/currency_rate_diff", params=params)
        assert response.status == 400
        assert response.reason == "Invalid parameters"


@pytest.mark.asyncio
async def test_no_data(client):
    for params in NO_DATA_PARAMS:
        response = await client.get(
            "/v1/currency_rate_diff",
            params=params,
        )
        assert response.status == 400
        assert response.reason == "No data"
