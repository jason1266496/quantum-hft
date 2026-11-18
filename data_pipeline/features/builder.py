"""Bind each feature stream to one source/session and a completed event state."""

from decimal import Decimal, localcontext

from data_pipeline.orderbook.rebuilder import OrderBookRebuilder
from data_pipeline.orderbook.types import Event
from . import formulas
from .schema import SCHEMA_VERSION, VIEWS, fields


class FeatureBuilder:
    def __init__(self, source_id, session_id, source_kind):
        if any(type(value) is not str or not value for value in (source_id, session_id)):
            raise ValueError("INVALID_IDENTITY")
        if source_kind not in ("csv", "replay"):
            raise ValueError("INVALID_SOURCE_KIND")
        self.source_id, self.session_id, self.source_kind = source_id, session_id, source_kind
        self._book = None
        self._applied_count = 0
        self._record_index = 0

    def _identity(self, source_id, session_id):
        if source_id is not None and source_id != self.source_id:
            raise ValueError("SOURCE_MISMATCH")
        if session_id is not None and session_id != self.session_id:
            raise ValueError("SESSION_MISMATCH")

    @staticmethod
    def _row(view, metadata, values, reasons=()):
        row = dict.fromkeys(fields(view))
        row.update(metadata)
        row.update(values)
        row.update(schema_version=SCHEMA_VERSION, feature_view=view)
        all_reasons = set(filter(None, row.get("invalid_reason", "").split(";"))) | set(reasons)
        row["invalid_reason"] = ";".join(sorted(all_reasons))
        row["valid_feature_row"] = bool(row["valid_feature_row"]) and not (set(reasons) - {"ZERO_LEVEL_DENOMINATOR"})
        return row

    def from_csv(self, record):
        """Return aggregate only, preserving source update_id solely as an alias."""
        if self.source_kind != "csv":
            raise ValueError("CSV_SOURCE_REQUIRED")
        if not isinstance(record, dict):
            raise ValueError("INVALID_CSV_RECORD")
        self._identity(record.get("source_id"), record.get("session_id"))
        required = ("source_id", "session_id", "record_index", "event_time_ms",
                    "best_bid", "best_ask", "bid_volume_5", "ask_volume_5")
        reasons = {"MISSING_FIELD"} if any(record.get(key) is None for key in required) else set()
        metadata = {key: record.get(key) for key in ("source_id", "session_id", "record_index", "event_time_ms")}
        for key in ("record_index", "event_time_ms"):
            value = metadata[key]
            if value is not None and (type(value) is not int or value < (1 if key == "record_index" else 0)):
                reasons.add("INVALID_METADATA")
                metadata[key] = None
        update_id = record.get("update_id")
        if update_id is not None and (type(update_id) is not int or update_id < 0):
            reasons.add("INVALID_UPDATE_ID")
            update_id = None
        metadata.update(first_update_id=None, final_update_id=None, local_update_id=update_id)
        values = formulas.aggregate(*(record.get(key) for key in ("best_bid", "best_ask", "bid_volume_5", "ask_volume_5")))
        return self._row(VIEWS[0], metadata, values, reasons)

    def from_book(self, book, event):
        """Build both views after APPLY, rejecting snapshot/pre-apply/reused state."""
        if self.source_kind != "replay":
            raise ValueError("CSV_DEPTH_NOT_AVAILABLE")
        if not isinstance(book, OrderBookRebuilder) or not isinstance(event, Event):
            raise ValueError("INVALID_REPLAY_INPUT")
        self._identity(event.source_id, event.session_id)
        self._identity(book.replay_source_id, book.session_id)
        if self._book is not None and self._book is not book:
            raise ValueError("BOOK_INSTANCE_MISMATCH")
        if book.applied_event_count <= self._applied_count or book.local_update_id != event.final_update_id:
            raise ValueError("EVENT_NOT_APPLIED")
        if type(event.record_index) is not int or event.record_index <= self._record_index:
            raise ValueError("INVALID_RECORD_INDEX")
        ids = (event.first_update_id, event.final_update_id, book.local_update_id)
        if any(type(value) is not int or value < 0 for value in ids) or event.first_update_id > event.final_update_id:
            raise ValueError("INVALID_UPDATE_ID")
        if type(event.event_time) is not int or event.event_time < 0:
            raise ValueError("INVALID_EVENT_TIME")
        bids, asks = tuple(book.top_bids(5)), tuple(book.top_asks(5))
        depth_values = formulas.depth(bids, asks)
        with localcontext(formulas.calculation_context()):
            bq = sum((q for _, q in bids), Decimal(0)) if len(bids) == 5 else None
            aq = sum((q for _, q in asks), Decimal(0)) if len(asks) == 5 else None
        aggregate_values = formulas.aggregate(bids[0][0] if bids else None, asks[0][0] if asks else None, bq, aq)
        reasons = set()
        if len(bids) < 5 or len(asks) < 5:
            reasons.add("INSUFFICIENT_TOP5_DEPTH")
        if not bids or not asks:
            reasons.add("EMPTY_SIDE")
        metadata = {
            "source_id": self.source_id, "session_id": self.session_id,
            "record_index": event.record_index, "event_time_ms": event.event_time,
            "first_update_id": event.first_update_id, "final_update_id": event.final_update_id,
            "local_update_id": book.local_update_id,
        }
        rows = {VIEWS[0]: self._row(VIEWS[0], metadata, aggregate_values, reasons),
                VIEWS[1]: self._row(VIEWS[1], metadata, depth_values)}
        self._book, self._applied_count, self._record_index = book, book.applied_event_count, event.record_index
        return rows
