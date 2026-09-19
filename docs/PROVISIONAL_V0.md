# Provisional Detector v0

These rules exist only to generate inspectable historical setups while owner chart examples are unavailable.

They are not the final definition of the trader's strategy.

## Flip Zone v0

Pivot-based support/resistance areas:

- SELL candidate starts from a confirmed pivot high.
- Zone uses the upper part of that pivot candle.
- Price must later trade above the zone.
- Price must then close back below the zone.
- BUY is the exact inverse using a confirmed pivot low.

Configurable:
- pivot-left candles
- pivot-right candles
- zone lookback
- zone padding

## Rejection v0

Score 0..1 from:
- 50% distance moved away from the zone
- 30% directional closes away from the zone
- 20% candle body efficiency versus total range

Default healthy threshold: 0.60.

## CHoCH/BOS v0

Uses confirmed pivot highs/lows on the required higher timeframe.

- bullish confirmation: latest close breaks above latest confirmed pivot high
- bearish confirmation: latest close breaks below latest confirmed pivot low

v0 reports confirmed breaks as BOS. Exact CHoCH versus BOS classification is deferred until trader swing interpretation is calibrated.

## Retest v0

A later candle must overlap the zone from the correct side:
- SELL reaches the zone while opening or closing below it
- BUY reaches the zone while opening or closing above it

## Important

Historical outputs from v0 are calibration material only. Profit or loss does not prove that the detector matches the trader's intended method.
