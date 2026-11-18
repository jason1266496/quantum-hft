"""Independent dict-and-sort reference reconstruction; no main/heap helpers."""

from decimal import Decimal

from .canonical import canonical_decimal, canonical_state_hash
from .types import BookError, Event, Snapshot


class ReferenceOrderBookRebuilder:
    """Simple correctness reference with separately implemented update semantics."""

    def __init__(self, session_id, snapshot_source_id, replay_source_id):
        for value in (session_id, snapshot_source_id, replay_source_id):
            if not isinstance(value, str) or not value:
                raise BookError("INVALID_IDENTITY", "source and session IDs must be nonempty strings")
        self.session_id = session_id
        self.snapshot_source_id = snapshot_source_id
        self.replay_source_id = replay_source_id
        self.local_update_id = None
        self.applied_event_count = 0
        self.skipped_event_count = 0
        self.continuity_error_count = 0
        self.crossed_book_count = 0
        self.empty_side_count = 0
        self._bids = {}
        self._asks = {}
        self._terminal = False

    def _require_loaded(self):
        if self.local_update_id is None:
            raise BookError("SNAPSHOT_REQUIRED", "load a snapshot before reading or applying events")

    def _identity(self, item, expected_source):
        if item.session_id != self.session_id:
            raise BookError("SESSION_MISMATCH", "cannot combine distinct sessions")
        if item.source_id != expected_source:
            raise BookError("SOURCE_MISMATCH", "source does not match this pair")

    @staticmethod
    def _integer(value, code, minimum=0):
        if type(value) is not int or value < minimum:
            raise BookError(code, "metadata must be an integer within its domain")

    @staticmethod
    def _check_levels(levels):
        # Deliberately not shared with the production rebuilder or continuity.
        if type(levels) is not tuple:
            raise BookError("INVALID_LEVEL", "levels must be immutable tuples")
        for update in levels:
            if type(update) is not tuple or len(update) != 2:
                raise BookError("INVALID_LEVEL", "each update must contain price and quantity")
            price, quantity = update
            if not isinstance(price, Decimal) or not price.is_finite() or price <= 0:
                raise BookError("INVALID_PRICE", "price must be a positive finite Decimal")
            if not isinstance(quantity, Decimal) or not quantity.is_finite() or quantity < 0:
                raise BookError("INVALID_QUANTITY", "quantity must be a nonnegative finite Decimal")

    def load_snapshot(self, snapshot):
        if self.local_update_id is not None:
            raise BookError("SNAPSHOT_ALREADY_LOADED", "snapshot reloading is not allowed")
        if not isinstance(snapshot, Snapshot):
            raise BookError("INVALID_SNAPSHOT", "Snapshot data structure is required")
        self._identity(snapshot, self.snapshot_source_id)
        self._integer(snapshot.last_update_id, "INVALID_UPDATE_ID")
        self._check_levels(snapshot.bids)
        self._check_levels(snapshot.asks)
        bids, asks = {}, {}
        for destination, rows in ((bids, snapshot.bids), (asks, snapshot.asks)):
            for price, quantity in rows:
                if quantity == 0:
                    destination.pop(price, None)
                else:
                    destination[price] = quantity
        self._bids, self._asks = bids, asks
        self.local_update_id = snapshot.last_update_id
        self._record_quality()

    def apply_event(self, event):
        self._require_loaded()
        if self._terminal:
            raise BookError("TERMINAL_STATE", "reconstruction stopped after a continuity failure")
        if not isinstance(event, Event):
            raise BookError("INVALID_EVENT", "Event data structure is required")
        self._identity(event, self.replay_source_id)
        self._integer(event.record_index, "INVALID_RECORD_INDEX", 1)
        self._integer(event.event_time, "INVALID_EVENT_TIME")
        self._integer(event.first_update_id, "INVALID_UPDATE_ID")
        self._integer(event.final_update_id, "INVALID_UPDATE_ID")
        if event.first_update_id > event.final_update_id:
            raise BookError("INVALID_UPDATE_ID", "first update ID exceeds final update ID")
        self._check_levels(event.bids)
        self._check_levels(event.asks)
        previous = self.local_update_id
        first, final = event.first_update_id, event.final_update_id
        if final <= previous:
            classification = "STALE_BEFORE_SNAPSHOT" if self.applied_event_count == 0 else "STALE_OR_DUPLICATE"
            action = "SKIP"
        elif first > previous + 1:
            classification = "FIRST_EVENT_BRIDGE_FAILURE" if self.applied_event_count == 0 else "UPDATE_ID_GAP"
            action = "STOP"
        else:
            classification = "CONTIGUOUS" if first == previous + 1 else "OVERLAPPING_CONTIGUOUS"
            action = "APPLY"
        decision = {
            "record_index": event.record_index, "event_time": event.event_time,
            "U": first, "u": final, "previous_local_update_id": previous,
            "classification": classification, "action": action,
        }
        if action == "STOP":
            self.continuity_error_count += 1
            self._terminal = True
        elif action == "SKIP":
            self.skipped_event_count += 1
        else:
            for book, updates in ((self._bids, event.bids), (self._asks, event.asks)):
                for price, quantity in updates:
                    if quantity == 0:
                        if price in book:
                            del book[price]
                    else:
                        book[price] = quantity
            self.local_update_id = final
            self.applied_event_count += 1
            self._record_quality()
        return decision

    def best_bid(self):
        self._require_loaded()
        prices = sorted(self._bids, reverse=True)
        return prices[0] if prices else None

    def best_ask(self):
        self._require_loaded()
        prices = sorted(self._asks)
        return prices[0] if prices else None

    def top_bids(self, n):
        self._require_loaded()
        if type(n) is not int or n < 0:
            raise BookError("INVALID_DEPTH", "depth must be a nonnegative integer")
        return [(price, self._bids[price]) for price in sorted(self._bids, reverse=True)[:n]]

    def top_asks(self, n):
        self._require_loaded()
        if type(n) is not int or n < 0:
            raise BookError("INVALID_DEPTH", "depth must be a nonnegative integer")
        return [(price, self._asks[price]) for price in sorted(self._asks)[:n]]

    def _record_quality(self):
        bid, ask = self.best_bid(), self.best_ask()
        if bid is None or ask is None:
            self.empty_side_count += 1
        elif bid >= ask:
            self.crossed_book_count += 1

    def full_state(self):
        self._require_loaded()
        return {"local_update_id": self.local_update_id,
                "bids": dict(self._bids), "asks": dict(self._asks)}

    def canonical_state_hash(self):
        return canonical_state_hash(self.full_state())

    def state_summary(self):
        self._require_loaded()
        bid, ask = self.best_bid(), self.best_ask()
        encode = lambda value: canonical_decimal(value) if value is not None else None
        return {
            "local_update_id": self.local_update_id,
            "bid_level_count": len(self._bids), "ask_level_count": len(self._asks),
            "best_bid": encode(bid), "best_ask": encode(ask),
            "top_bids": [[encode(p), encode(q)] for p, q in self.top_bids(5)],
            "top_asks": [[encode(p), encode(q)] for p, q in self.top_asks(5)],
            "crossed": bid is not None and ask is not None and bid >= ask,
            "empty": bid is None or ask is None,
            "applied_event_count": self.applied_event_count,
            "skipped_event_count": self.skipped_event_count,
            "continuity_error_count": self.continuity_error_count,
            "crossed_book_count": self.crossed_book_count,
            "empty_side_count": self.empty_side_count,
        }
