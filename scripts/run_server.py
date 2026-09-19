from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv

from tbot.api import create_app
from tbot.data.twelve_data import TwelveDataXauUsdProvider
from tbot.fallback_calendar import FallbackEconomicCalendarProvider
from tbot.finance_calendar import FinanceCalendarProvider
from tbot.fmp_calendar import FmpEconomicCalendarProvider
from tbot.xoomar_calendar import XoomarEconomicCalendarProvider


def main() -> None:
    load_dotenv()
    port = int(os.getenv("PORT", "8000"))

    market_data = None
    if os.getenv("TWELVE_DATA_API_KEY"):
        market_data = TwelveDataXauUsdProvider()

    providers = [
        XoomarEconomicCalendarProvider(),
        FinanceCalendarProvider(),
    ]
    if os.getenv("FMP_API_KEY"):
        providers.append(FmpEconomicCalendarProvider())
    calendar = FallbackEconomicCalendarProvider(providers)

    app = create_app(
        market_data=market_data,
        calendar=calendar,
    )
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
