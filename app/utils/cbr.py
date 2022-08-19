import abc
import datetime
import logging
import typing as tp
from decimal import Decimal
from xml.etree import ElementTree

import aiohttp

from app.utils import caching


class BaseCBRClient(abc.ABC):
    async def start(self):
        pass

    async def close(self):
        pass

    @abc.abstractmethod
    async def get_currency_codes(self) -> tp.Optional[tp.List[str]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_currency_rate_relative_rub(
            self, code: str, for_date: datetime.date
    ) -> tp.Optional[Decimal]:
        raise NotImplementedError


class CBRClient(BaseCBRClient):
    def __init__(
            self,
            base_url: str = "https://www.cbr.ru",
            cache: caching.BaseCache = caching.LRUCache(),
    ):
        self._cache = cache
        self._session: tp.Optional[aiohttp.ClientSession] = None
        self._base_url = base_url

    async def start(self):
        await self._cache.init()
        if self._session:
            await self._session.close()
        self._session = aiohttp.ClientSession(self._base_url)

    async def close(self):
        await self._cache.close()
        if self._session:
            await self._session.close()

    async def get_currency_codes(self) -> tp.Optional[tp.List[str]]:
        currency_codes = await self._cache.get("currency_codes")
        if currency_codes:
            return currency_codes
        async with self._session.get("/scripts/XML_valFull.asp") as response:
            if response.status != 200:
                logging.error(f"{response.url} returned {response.status} code")
                return None

            data = await response.text()

        tree = ElementTree.fromstring(data)
        for elem in tree.findall("Item/ISO_Char_Code"):
            code = elem.text
            if code is not None:
                currency_codes.append(code)

        await self._cache.put("currency_codes", currency_codes)
        return currency_codes

    async def get_currency_rate_relative_rub(
            self, code: str, for_date: datetime.date
    ) -> tp.Optional[Decimal]:
        cache_key = f"{code}:{for_date.isoformat()}"
        value = await self._cache.get(cache_key)
        if value:
            return Decimal(value)
        async with self._session.get(
                "/scripts/XML_daily.asp", params={"date_req": for_date.strftime("%d/%m/%Y")}
        ) as response:
            if response.status != 200:
                logging.error(f"{response.url} returned {response.status} code")
                return None

            data = await response.text()

        tree = ElementTree.fromstring(data)
        elem = tree.find(f"Valute[CharCode='{code}']")
        if elem is None:
            return None

        value = elem.find("Value").text.replace(",", ".")
        await self._cache.put(cache_key, float(value))
        return Decimal(value)


class TestCBRClient(BaseCBRClient):
    def __init__(self):
        self._currencies_rates = {
            "USD": {
                datetime.date(2000, 1, 1): Decimal("27.0000"),
                datetime.date(2010, 1, 1): Decimal("30.1851"),
                datetime.date(2020, 1, 1): Decimal("61.9057"),
            },
            "EUR": {
                datetime.date(2000, 1, 1): Decimal("27.2000"),
                datetime.date(2010, 1, 1): Decimal("43.4605"),
                datetime.date(2020, 1, 1): Decimal("69.3777"),
            },
            "AUD": {
                datetime.date(2000, 1, 1): Decimal("17.6300"),
                datetime.date(2010, 1, 1): Decimal("27.1304"),
                datetime.date(2020, 1, 1): Decimal("43.3835"),
            },
        }

    async def get_currency_codes(self) -> tp.Optional[tp.List[str]]:
        return list(self._currencies_rates.keys())

    async def get_currency_rate_relative_rub(
            self, code: str, for_date: datetime.date
    ) -> tp.Optional[Decimal]:
        rates = self._currencies_rates.get(code)
        if rates is None:
            return None
        return rates.get(for_date)
