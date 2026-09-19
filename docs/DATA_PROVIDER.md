# Phase 0 Market Data

## Initial adapter: Twelve Data

The strategy engine is provider-neutral. The first concrete adapter uses Twelve Data for XAU/USD.

Why it fits Phase 0:
- XAU/USD is documented as Gold Spot / US Dollar.
- Required intervals are supported: 5min, 15min, 1h, 4h.
- Intraday commodity history is documented from January 9, 2020.
- API responses can be requested in UTC.

The provider is an adapter, not part of strategy logic. Replacing it later with OANDA, broker/MT5 data, or another feed must not require rewriting Flip & Dip rules.

## Environment

Set:

TWELVE_DATA_API_KEY=...

Do not commit the key.

## Internal normalization

External:
- symbol: XAU/USD
- intervals: 5min, 15min, 1h, 4h

Internal:
- symbol: XAUUSD
- intervals: 5M, 15M, 1H, 4H

All timestamps enter the strategy layer as timezone-aware UTC datetimes.

## Important data-quality rule

We must validate the chosen feed against the trader's chart/broker before trusting exact zone prices. Different XAUUSD feeds can differ slightly. Strategy calibration must use the same or sufficiently consistent feed that the trader uses for chart decisions.
