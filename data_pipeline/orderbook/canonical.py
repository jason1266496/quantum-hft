"""Stable decimal-only book serialization, independent of insertion/context order."""

from decimal import Decimal
import hashlib
import json


def canonical_decimal(value):
    """Exact fixed-point string, avoiding context-rounding normalize/arithmetic."""
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("canonical values must be finite Decimal instances")
    if value.is_zero():
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def canonical_state(state):
    """Serialize the entire state in descending bid/ascending ask order."""
    local_id = state["local_update_id"]
    if type(local_id) is not int or local_id < 0:
        raise ValueError("local_update_id must be a nonnegative integer")
    sides = {}
    for side in ("bids", "asks"):
        book = state[side]
        if not isinstance(book, dict):
            raise ValueError("book sides must be dictionaries")
        for price, quantity in book.items():
            if not isinstance(price, Decimal) or not price.is_finite() or price <= 0:
                raise ValueError("stored prices must be positive finite Decimal")
            if not isinstance(quantity, Decimal) or not quantity.is_finite() or quantity <= 0:
                raise ValueError("stored quantities must be positive finite Decimal")
        sides[side] = [[canonical_decimal(price), canonical_decimal(book[price])]
                       for price in sorted(book, reverse=side == "bids")]
    return {
        "local_update_id": local_id,
        "bids": sides["bids"], "asks": sides["asks"],
        "bid_level_count": len(sides["bids"]),
        "ask_level_count": len(sides["asks"]),
        "best_bid": sides["bids"][0][0] if sides["bids"] else None,
        "best_ask": sides["asks"][0][0] if sides["asks"] else None,
    }


def canonical_bytes(state):
    return json.dumps(canonical_state(state), sort_keys=True, ensure_ascii=True,
                      allow_nan=False, separators=(",", ":")).encode("ascii")


def canonical_state_hash(state):
    return hashlib.sha256(canonical_bytes(state)).hexdigest()
