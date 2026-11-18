"""Immutable input values; no source access, clocks, or market calculations."""

from dataclasses import dataclass
from decimal import Decimal


class BookError(ValueError):
    """A reconstruction contract violation with a stable machine-readable code."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f"{code}: {message}")


def _immutable_levels(levels):
    if type(levels) is not tuple or any(
        type(level) is not tuple or len(level) != 2 for level in levels
    ):
        raise BookError("INVALID_LEVEL_STRUCTURE", "levels must be tuples of price/quantity tuples")


@dataclass(frozen=True)
class Snapshot:
    source_id: str
    session_id: str
    last_update_id: int
    bids: tuple[tuple[Decimal, Decimal], ...]
    asks: tuple[tuple[Decimal, Decimal], ...]

    def __post_init__(self):
        _immutable_levels(self.bids)
        _immutable_levels(self.asks)


@dataclass(frozen=True)
class Event:
    source_id: str
    session_id: str
    record_index: int
    event_time: int
    first_update_id: int
    final_update_id: int
    bids: tuple[tuple[Decimal, Decimal], ...]
    asks: tuple[tuple[Decimal, Decimal], ...]

    def __post_init__(self):
        _immutable_levels(self.bids)
        _immutable_levels(self.asks)

    @classmethod
    def from_record(cls, record):
        """Preserve ReplayAdapter Decimal values without coercion or timestamps."""
        if not isinstance(record, dict):
            raise BookError("INVALID_EVENT_RECORD", "expected a ReplayAdapter record mapping")
        if "local_timestamp_us" in record:
            raise BookError("FORBIDDEN_TIMESTAMP", "local_timestamp_us must not enter book inputs")
        fields = ("source_id", "session_id", "record_index", "eventTime",
                  "firstUpdateId", "finalUpdateId", "bids", "asks")
        if any(field not in record for field in fields):
            raise BookError("INVALID_EVENT_RECORD", "missing required ReplayAdapter field")
        return cls(*(record[field] for field in fields))
