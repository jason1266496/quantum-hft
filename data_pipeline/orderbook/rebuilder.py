"""Main Decimal book: dictionaries, bounded lazy heaps, and atomic events."""

import heapq
from decimal import Decimal

from .canonical import canonical_decimal, canonical_state_hash
from .continuity import classify_update
from .types import BookError, Event, Snapshot


class OrderBookRebuilder:
    def __init__(self, session_id, snapshot_source_id, replay_source_id):
        if any(type(value) is not str or not value for value in (
            session_id, snapshot_source_id, replay_source_id
        )):
            raise BookError("INVALID_IDENTITY", "session and source identities must be nonempty strings")
        self.session_id = session_id
        self.snapshot_source_id = snapshot_source_id
        self.replay_source_id = replay_source_id
        self.local_update_id = None
        self.applied_event_count = 0
        self.skipped_event_count = 0
        self.continuity_error_count = 0
        self.crossed_book_count = 0
        self.empty_side_count = 0
        self._snapshot_update_id = None
        self._loaded = False
        self._terminal = False
        self._bids = {}
        self._asks = {}
        self._bid_heap = []
        self._ask_heap = []
        self._bid_heap_prices = set()
        self._ask_heap_prices = set()

    def _identity(self, value, expected_source):
        if value.session_id != self.session_id:
            raise BookError("SESSION_MISMATCH", "input belongs to another registry session")
        if value.source_id != expected_source:
            raise BookError("SOURCE_MISMATCH", "input does not match the bound source")

    @staticmethod
    def _levels(levels):
        # Validate both sides before applying any update, including stale events.
        for price, quantity in levels:
            if type(price) is not Decimal or not price.is_finite() or price <= 0:
                raise BookError("INVALID_PRICE", "price must be a finite positive Decimal")
            if type(quantity) is not Decimal or not quantity.is_finite() or quantity < 0:
                raise BookError("INVALID_QUANTITY", "quantity must be a finite nonnegative Decimal")

    def load_snapshot(self, snapshot):
        if self._loaded:
            raise BookError("SNAPSHOT_ALREADY_LOADED", "create a new rebuilder for another snapshot")
        if not isinstance(snapshot, Snapshot):
            raise BookError("INVALID_SNAPSHOT", "expected immutable Snapshot")
        self._identity(snapshot, self.snapshot_source_id)
        if type(snapshot.last_update_id) is not int or snapshot.last_update_id < 0:
            raise BookError("INVALID_UPDATE_ID", "snapshot ID must be a nonnegative integer")
        self._levels(snapshot.bids)
        self._levels(snapshot.asks)
        bids, asks = {}, {}
        for levels, side in ((snapshot.bids, bids), (snapshot.asks, asks)):
            for price, quantity in levels:
                if quantity == 0:
                    side.pop(price, None)
                else:
                    side[price] = quantity
        self._bids, self._asks = bids, asks
        self._bid_heap = [price.copy_negate() for price in bids]
        self._ask_heap = list(asks)
        heapq.heapify(self._bid_heap)
        heapq.heapify(self._ask_heap)
        self._bid_heap_prices = set(bids)
        self._ask_heap_prices = set(asks)
        self._snapshot_update_id = snapshot.last_update_id
        self.local_update_id = snapshot.last_update_id
        self._loaded = True
        self._record_quality()

    def _require_loaded(self):
        if not self._loaded:
            raise BookError("SNAPSHOT_REQUIRED", "load the bound snapshot before using the book")

    def _update_side(self, updates, side, heap, heap_prices, bid):
        for price, quantity in updates:
            if quantity == 0:
                side.pop(price, None)
            else:
                side[price] = quantity
                # A deleted level can still have a lazy heap entry. Reuse it.
                if price not in heap_prices:
                    heapq.heappush(heap, price.copy_negate() if bid else price)
                    heap_prices.add(price)
        # Churn at prices away from the best quote must not grow heaps forever.
        if len(heap) > max(64, 2 * len(side) + 32):
            heap[:] = [price.copy_negate() if bid else price for price in side]
            heapq.heapify(heap)
            heap_prices.clear()
            heap_prices.update(side)

    def apply_event(self, event):
        self._require_loaded()
        if self._terminal:
            raise BookError("TERMINAL_STATE", "continuity failure terminated this book")
        if not isinstance(event, Event):
            raise BookError("INVALID_EVENT", "expected immutable Event")
        self._identity(event, self.replay_source_id)
        if type(event.record_index) is not int or event.record_index < 1:
            raise BookError("INVALID_RECORD_INDEX", "record index must be a positive integer")
        if type(event.event_time) is not int or event.event_time < 0:
            raise BookError("INVALID_EVENT_TIME", "exchange event time must be a nonnegative integer")
        self._levels(event.bids)
        self._levels(event.asks)
        classification, action = classify_update(
            self._snapshot_update_id, self.local_update_id, self.applied_event_count,
            event.first_update_id, event.final_update_id,
        )
        decision = {
            "record_index": event.record_index,
            "event_time": event.event_time,
            "U": event.first_update_id,
            "u": event.final_update_id,
            "previous_local_update_id": self.local_update_id,
            "classification": classification,
            "action": action,
        }
        if action == "STOP":
            self.continuity_error_count += 1
            self._terminal = True
        elif action == "SKIP":
            self.skipped_event_count += 1
        else:
            self._update_side(event.bids, self._bids, self._bid_heap, self._bid_heap_prices, True)
            self._update_side(event.asks, self._asks, self._ask_heap, self._ask_heap_prices, False)
            self.local_update_id = event.final_update_id
            self.applied_event_count += 1
            self._record_quality()
        return decision

    def _best(self, side, heap, heap_prices, bid):
        while heap:
            price = heap[0].copy_negate() if bid else heap[0]
            if price in side:
                return price
            heapq.heappop(heap)
            heap_prices.discard(price)
        return None

    def best_bid(self):
        self._require_loaded()
        return self._best(self._bids, self._bid_heap, self._bid_heap_prices, True)

    def best_ask(self):
        self._require_loaded()
        return self._best(self._asks, self._ask_heap, self._ask_heap_prices, False)

    @staticmethod
    def _top(side, n, reverse):
        if type(n) is not int or n < 0:
            raise BookError("INVALID_TOP_COUNT", "top count must be a nonnegative integer")
        return [(price, side[price]) for price in sorted(side, reverse=reverse)[:n]]

    def top_bids(self, n):
        self._require_loaded()
        return self._top(self._bids, n, True)

    def top_asks(self, n):
        self._require_loaded()
        return self._top(self._asks, n, False)

    def _quality(self):
        bid, ask = self.best_bid(), self.best_ask()
        return (bid is not None and ask is not None and bid >= ask,
                bid is None or ask is None)

    def _record_quality(self):
        crossed, empty = self._quality()
        self.crossed_book_count += int(crossed)
        self.empty_side_count += int(empty)

    def full_state(self):
        self._require_loaded()
        return {"local_update_id": self.local_update_id,
                "bids": dict(self._bids), "asks": dict(self._asks)}

    def canonical_state_hash(self):
        return canonical_state_hash(self.full_state())

    def state_summary(self):
        self._require_loaded()
        crossed, empty = self._quality()
        bid, ask = self.best_bid(), self.best_ask()
        return {
            "local_update_id": self.local_update_id,
            "bid_level_count": len(self._bids), "ask_level_count": len(self._asks),
            "best_bid": canonical_decimal(bid) if bid is not None else None,
            "best_ask": canonical_decimal(ask) if ask is not None else None,
            "top_bids": [[canonical_decimal(p), canonical_decimal(q)] for p, q in self.top_bids(5)],
            "top_asks": [[canonical_decimal(p), canonical_decimal(q)] for p, q in self.top_asks(5)],
            "crossed": crossed, "empty": empty,
            "applied_event_count": self.applied_event_count,
            "skipped_event_count": self.skipped_event_count,
            "continuity_error_count": self.continuity_error_count,
            "crossed_book_count": self.crossed_book_count,
            "empty_side_count": self.empty_side_count,
        }
