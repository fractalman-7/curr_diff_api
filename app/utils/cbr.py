import abc
import datetime
import logging
import typing as tp
from decimal import Decimal
from xml.etree import ElementTree

import aiohttp


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
    def __init__(self, base_url: str = "https://www.cbr.ru"):
        self._session: tp.Optional[aiohttp.ClientSession] = None
        self._base_url = base_url
        self._currency_codes = []

    async def start(self):
        if self._session:
            await self._session.close()
        self._session = aiohttp.ClientSession(self._base_url)

    async def close(self):
        if self._session:
            await self._session.close()

    async def get_currency_codes(self) -> tp.Optional[tp.List[str]]:
        if self._currency_codes:
            return self._currency_codes

        async with self._session.get("/scripts/XML_valFull.asp") as response:
            if response.status != 200:
                logging.error(f"{response.url} returned {response.status} code")
                return None

            data = await response.text()

        tree = ElementTree.fromstring(data)
        for elem in tree.findall("Item/ISO_Char_Code"):
            code = elem.text
            if code is not None:
                self._currency_codes.append(code)

        return self._currency_codes

    async def get_currency_rate_relative_rub(
            self, code: str, for_date: datetime.date
    ) -> tp.Optional[Decimal]:
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

        return Decimal(elem.find("Value").text.replace(",", "."))


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
