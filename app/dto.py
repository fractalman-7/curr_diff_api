from __future__ import annotations

import dataclasses
import datetime
import typing as tp


@dataclasses.dataclass
class CurrencyRatesDifferenceParameters:
    currency_code: tp.Optional[str]
    from_date: tp.Optional[datetime.date]
    to_date: tp.Optional[datetime.date]

    @staticmethod
    def from_query(query: tp.Mapping[str]) -> CurrencyRatesDifferenceParameters:
        code = query.get("code")
        try:
            date_from = datetime.date.fromisoformat(query.get("from_date"))
            date_to = datetime.date.fromisoformat(query.get("to_date"))
        except (ValueError, TypeError):
            date_from = date_to = None

        return CurrencyRatesDifferenceParameters(code, date_from, date_to)


@dataclasses.dataclass
class CurrencyRatesDifference:
    rate_from: str
    rate_to: str
    difference: str

    def to_dict(self) -> tp.Dict:
        return dataclasses.asdict(self)
