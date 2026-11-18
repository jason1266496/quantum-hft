"""Independent top-five feature calculations from a canonical book state.

This module deliberately does not import the main builder or formula module.
A full canonical state and its explicitly identified top-five projection contain
the same information required by these two views. No state, future events, or
source files are consulted.
"""

from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext

from .schema import fields

_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999)
_ZERO = Decimal("0")
_ONE = Decimal("1")
_TWO = Decimal("2")
_BPS = Decimal("10000")
_VIEWS = ("aggregate_core_v1", "depth_top5_v1")
_METADATA = ("source_id", "session_id", "record_index", "event_time_ms",
             "first_update_id", "final_update_id", "local_update_id")


def _metadata(state, supplied):
    if not isinstance(supplied, dict):
        raise ValueError("INVALID_METADATA: expected a mapping")
    values = {}
    for key in _METADATA:
        if key not in supplied:
            raise ValueError(f"MISSING_METADATA: {key}")
        value = supplied[key]
        if key in ("source_id", "session_id"):
            if type(value) is not str or not value:
                raise ValueError(f"INVALID_METADATA: {key}")
        elif type(value) is not int or value < (1 if key == "record_index" else 0):
            raise ValueError(f"INVALID_METADATA: {key}")
        values[key] = value
    if values["first_update_id"] > values["final_update_id"]:
        raise ValueError("INVALID_UPDATE_ID_RANGE")
    if values["local_update_id"] != values["final_update_id"]:
        raise ValueError("EVENT_NOT_APPLIED: local ID differs from event final ID")
    if state.get("local_update_id") != values["local_update_id"]:
        raise ValueError("LOCAL_UPDATE_ID_MISMATCH")
    return values


def _decimal(text, reasons, kind):
    if text is None:
        reasons.add("MISSING_VALUE")
        return None
    if type(text) is not str:
        reasons.add("INVALID_NUMERIC_TYPE")
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        reasons.add("INVALID_NUMERIC_TYPE")
        return None
    if not value.is_finite():
        reasons.add("NON_FINITE_VALUE")
        return None
    if kind == "price" and value <= _ZERO:
        reasons.add("INVALID_PRICE")
        return None
    if kind == "quantity" and value < _ZERO:
        reasons.add("INVALID_QUANTITY")
        return None
    return value


def _sides(state):
    errors = set()
    output = []
    for side in ("bids", "asks"):
        levels = state.get(side)
        if type(levels) is not list:
            raise ValueError(f"INVALID_CANONICAL_SIDE: {side}")
        parsed = []
        for pair in levels[:5]:
            if type(pair) not in (list, tuple) or len(pair) != 2:
                raise ValueError(f"INVALID_CANONICAL_LEVEL: {side}")
            parsed.append((_decimal(pair[0], errors, "price"),
                           _decimal(pair[1], errors, "quantity")))
        output.append(parsed)
    if not output[0] or not output[1]:
        errors.add("EMPTY_SIDE")
    if len(output[0]) < 5 or len(output[1]) < 5:
        errors.add("INSUFFICIENT_TOP5_DEPTH")
    return output[0], output[1], errors


def _prefix_volume(levels, count):
    if len(levels) < count or any(levels[i][1] is None for i in range(count)):
        return None
    total = _ZERO
    for i in range(count):
        total += levels[i][1]
    return total


def _imbalance(bid, ask, errors, zero_code):
    if bid is None or ask is None:
        return None
    denominator = bid + ask
    if denominator == _ZERO:
        errors.add(zero_code)
        return None
    result = (bid - ask) / denominator
    if result < -_ONE or result > _ONE:
        errors.add("OBI_OUT_OF_RANGE" if zero_code == "ZERO_DEPTH_DENOMINATOR"
                   else "LEVEL_IMBALANCE_OUT_OF_RANGE")
    return result


def _common_quotes(bids, asks, errors):
    bid = bids[0][0] if bids else None
    ask = asks[0][0] if asks else None
    if bid is None or ask is None:
        return bid, ask, None, None, None
    if bid >= ask:
        errors.add("CROSSED_BOOK")
    mid = (bid + ask) / _TWO
    spread = ask - bid
    if mid <= _ZERO:
        errors.add("INVALID_MID_PRICE")
        spread_bps = None
    else:
        spread_bps = spread / mid * _BPS
    return bid, ask, mid, spread, spread_bps


def _finish(view, metadata, values, errors):
    row = {name: None for name in fields(view)}
    row.update(schema_version="1.0", feature_view=view, **metadata, **values)
    row["valid_feature_row"] = not (errors - {"ZERO_LEVEL_DENOMINATOR"})
    row["invalid_reason"] = ";".join(sorted(errors))
    return row


def reference_features(canonical_book_state, metadata):
    """Return both views without using FeatureBuilder or its arithmetic.

    Prices and quantities must use the Phase 2B canonical string-pair shape.
    Numeric quality errors produce retained invalid rows; malformed containers
    or event identities raise ValueError. Full-depth count metadata and optional
    projection markers are intentionally not used to infer unavailable levels.
    """
    if not isinstance(canonical_book_state, dict):
        raise ValueError("INVALID_CANONICAL_STATE: expected a mapping")
    with localcontext(_CONTEXT):
        identity = _metadata(canonical_book_state, metadata)
        bids, asks, initial_errors = _sides(canonical_book_state)
        quote_errors = set(initial_errors)
        bid, ask, mid, spread, spread_bps = _common_quotes(bids, asks, quote_errors)
        common = {"mid_price": mid, "spread": spread, "spread_bps": spread_bps}

        aggregate_errors = set(quote_errors)
        bid5, ask5 = _prefix_volume(bids, 5), _prefix_volume(asks, 5)
        if any(value is None for value in (bid, ask, bid5, ask5)):
            aggregate_errors.add("MISSING_VALUE")
        aggregate = dict(common, best_bid=bid, best_ask=ask,
                         bid_volume_5=bid5, ask_volume_5=ask5)
        aggregate["obi_5"] = _imbalance(
            bid5, ask5, aggregate_errors, "ZERO_DEPTH_DENOMINATOR")

        depth_errors = set(quote_errors)
        depth = dict(common)
        for index in range(1, 6):
            bp, bq = bids[index - 1] if len(bids) >= index else (None, None)
            ap, aq = asks[index - 1] if len(asks) >= index else (None, None)
            depth[f"bid_price_{index}"], depth[f"bid_quantity_{index}"] = bp, bq
            depth[f"ask_price_{index}"], depth[f"ask_quantity_{index}"] = ap, aq
            depth[f"cumulative_bid_quantity_{index}"] = _prefix_volume(bids, index)
            depth[f"cumulative_ask_quantity_{index}"] = _prefix_volume(asks, index)
            depth[f"bid_distance_bps_{index}"] = (
                (mid - bp) / mid * _BPS if mid is not None and mid > _ZERO
                and bp is not None else None)
            depth[f"ask_distance_bps_{index}"] = (
                (ap - mid) / mid * _BPS if mid is not None and mid > _ZERO
                and ap is not None else None)
            depth[f"level_imbalance_{index}"] = _imbalance(
                bq, aq, depth_errors, "ZERO_LEVEL_DENOMINATOR")
        for count in (1, 3, 5):
            depth[f"obi_{count}"] = _imbalance(
                _prefix_volume(bids, count), _prefix_volume(asks, count),
                depth_errors, "ZERO_DEPTH_DENOMINATOR")

        bq1 = bids[0][1] if bids else None
        aq1 = asks[0][1] if asks else None
        microprice = None
        if all(item is not None for item in (bid, ask, bq1, aq1)):
            denominator = bq1 + aq1
            if denominator == _ZERO:
                depth_errors.add("ZERO_MICROPRICE_DENOMINATOR")
            else:
                microprice = (ask * bq1 + bid * aq1) / denominator
                if microprice < bid or microprice > ask:
                    depth_errors.add("MICROPRICE_OUT_OF_SPREAD")
        depth["microprice"] = microprice
        depth["microprice_deviation_bps"] = (
            (microprice - mid) / mid * _BPS if microprice is not None
            and mid is not None and mid > _ZERO else None)
        return {
            _VIEWS[0]: _finish(_VIEWS[0], identity, aggregate, aggregate_errors),
            _VIEWS[1]: _finish(_VIEWS[1], identity, depth, depth_errors),
        }

