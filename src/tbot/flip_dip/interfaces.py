from __future__ import annotations

from typing import Protocol, Sequence

from .models import Candle, Direction, FlipZone, StructureConfirmation


class FlipZoneDetector(Protocol):
    """Owner-specific Flip Zone detection. Must be calibrated, never guessed."""

    def detect(self, candles: Sequence[Candle]) -> list[FlipZone]:
        ...


class RejectionEvaluator(Protocol):
    """Returns an objective score only after calibration from approved examples."""

    def score(self, zone: FlipZone, candles: Sequence[Candle]) -> float:
        ...


class StructureDetector(Protocol):
    """Owner-specific CHoCH/BOS confirmation detector."""

    def confirm(
        self,
        candles: Sequence[Candle],
        *,
        direction: Direction,
        timeframe: str,
    ) -> StructureConfirmation:
        ...


class UnvalidatedRuleError(RuntimeError):
    pass


class UnvalidatedFlipZoneDetector:
    def detect(self, candles: Sequence[Candle]) -> list[FlipZone]:
        raise UnvalidatedRuleError(
            "Flip Zone detection is not calibrated. Provide owner-approved chart examples."
        )


class UnvalidatedRejectionEvaluator:
    def score(self, zone: FlipZone, candles: Sequence[Candle]) -> float:
        raise UnvalidatedRuleError(
            "Rejection quality is not calibrated. Provide healthy/weak rejection examples."
        )


class UnvalidatedStructureDetector:
    def confirm(
        self,
        candles: Sequence[Candle],
        *,
        direction: Direction,
        timeframe: str,
    ) -> StructureConfirmation:
        raise UnvalidatedRuleError(
            "CHoCH/BOS detection is not calibrated. Provide owner-approved structure examples."
        )
