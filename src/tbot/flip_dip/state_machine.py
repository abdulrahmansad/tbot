from __future__ import annotations

from dataclasses import dataclass

from .config import FlipDipConfig
from .models import FlipZone, SetupState


_ALLOWED: dict[SetupState, set[SetupState]] = {
    SetupState.ZONE_CANDIDATE: {SetupState.ZONE_VALID, SetupState.EXPIRED},
    SetupState.ZONE_VALID: {SetupState.FLIP_OCCURRED, SetupState.EXPIRED},
    SetupState.FLIP_OCCURRED: {SetupState.RETURN_CONFIRMED, SetupState.EXPIRED},
    SetupState.RETURN_CONFIRMED: {SetupState.REJECTION_CONFIRMED, SetupState.EXPIRED},
    SetupState.REJECTION_CONFIRMED: {
        SetupState.HTF_STRUCTURE_CONFIRMED,
        SetupState.EXPIRED,
    },
    SetupState.HTF_STRUCTURE_CONFIRMED: {
        SetupState.WAITING_FOR_RETEST,
        SetupState.EXPIRED,
    },
    SetupState.WAITING_FOR_RETEST: {
        SetupState.PLAN_READY,
        SetupState.EXPIRED,
        SetupState.EXHAUSTED,
    },
    SetupState.PLAN_READY: {
        SetupState.PLAN_TRACKING,
        SetupState.INVALIDATED,
        SetupState.EXPIRED,
    },
    SetupState.PLAN_TRACKING: {
        SetupState.COMPLETED,
        SetupState.INVALIDATED,
        SetupState.EXPIRED,
    },
    SetupState.COMPLETED: {
        SetupState.WAITING_FOR_RETEST,
        SetupState.EXHAUSTED,
    },
    SetupState.INVALIDATED: {SetupState.EXHAUSTED},
    SetupState.EXPIRED: set(),
    SetupState.EXHAUSTED: set(),
}


@dataclass
class FlipDipStateMachine:
    config: FlipDipConfig

    def transition(self, zone: FlipZone, target: SetupState) -> FlipZone:
        allowed = _ALLOWED[zone.state]
        if target not in allowed:
            raise ValueError(f"Invalid transition: {zone.state.value} -> {target.value}")

        if target == SetupState.PLAN_READY:
            if zone.execution_count >= self.config.max_executions_per_zone:
                raise ValueError("Zone execution limit reached")

        zone.state = target
        return zone

    def record_completed_execution(self, zone: FlipZone) -> FlipZone:
        if zone.state not in {
            SetupState.PLAN_TRACKING,
            SetupState.COMPLETED,
            SetupState.INVALIDATED,
        }:
            raise ValueError("Execution can only be recorded for an active/finished plan")

        zone.execution_count += 1
        if zone.execution_count >= self.config.max_executions_per_zone:
            zone.state = SetupState.EXHAUSTED
        else:
            zone.state = SetupState.WAITING_FOR_RETEST
        return zone
