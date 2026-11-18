"""Current-state Decimal arithmetic with explicit, caller-independent precision."""

from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext

from .schema import AGGREGATE_VALUES, DEPTH_VALUES


def calculation_context():
    return Context(prec=50, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999)


def _value(value, kind, reasons):
    if value is None:
        reasons.add("MISSING_VALUE")
        return None
    if type(value) is not Decimal:
        reasons.add("INVALID_NUMERIC_TYPE")
        return None
    if not value.is_finite():
        reasons.add("NON_FINITE_VALUE")
        return None
    if (kind == "price" and value <= 0) or (kind == "quantity" and value < 0):
        reasons.add("INVALID_PRICE" if kind == "price" else "INVALID_QUANTITY")
        return None
    return value


def _finish(row, reasons):
    row["valid_feature_row"] = not (reasons - {"ZERO_LEVEL_DENOMINATOR"})
    row["invalid_reason"] = ";".join(sorted(reasons))
    return row


def _imbalance(bid, ask, reasons, zero_code):
    if bid is None or ask is None:
        return None
    denominator = bid + ask
    if denominator == 0:
        reasons.add(zero_code)
        return None
    result = (bid - ask) / denominator
    if not Decimal(-1) <= result <= Decimal(1):
        reasons.add("LEVEL_IMBALANCE_OUT_OF_RANGE" if zero_code == "ZERO_LEVEL_DENOMINATOR" else "OBI_OUT_OF_RANGE")
    return result


def _quotes(bid, ask, reasons):
    mid = spread = bps = None
    if bid is not None and ask is not None:
        mid = (bid + ask) / Decimal(2)
        spread = ask - bid
        if bid >= ask:
            reasons.add("CROSSED_BOOK")
        if mid <= 0:
            reasons.add("INVALID_MID_PRICE")
        else:
            bps = spread / mid * Decimal(10000)
    return mid, spread, bps


def aggregate(best_bid, best_ask, bid_volume_5, ask_volume_5):
    """Compute aggregate fields; invalid data is retained as an invalid row."""
    row = dict.fromkeys(AGGREGATE_VALUES)
    reasons = set()
    with localcontext(calculation_context()):
        bid = _value(best_bid, "price", reasons)
        ask = _value(best_ask, "price", reasons)
        bq = _value(bid_volume_5, "quantity", reasons)
        aq = _value(ask_volume_5, "quantity", reasons)
        row.update(best_bid=bid, best_ask=ask, bid_volume_5=bq, ask_volume_5=aq)
        try:
            row["mid_price"], row["spread"], row["spread_bps"] = _quotes(bid, ask, reasons)
            row["obi_5"] = _imbalance(bq, aq, reasons, "ZERO_DEPTH_DENOMINATOR")
        except DecimalException:
            reasons.add("DECIMAL_ARITHMETIC_ERROR")
    return _finish(row, reasons)


def depth(bids, asks):
    """Derive top-five fields only from supplied current levels, without filling."""
    row = dict.fromkeys(DEPTH_VALUES)
    reasons = set()
    if not isinstance(bids, (tuple, list)) or not isinstance(asks, (tuple, list)):
        return _finish(row, {"INVALID_LEVEL_STRUCTURE"})
    if not bids or not asks:
        reasons.add("EMPTY_SIDE")
    if len(bids) < 5 or len(asks) < 5:
        reasons.add("INSUFFICIENT_TOP5_DEPTH")
    if len(bids) > 5 or len(asks) > 5:
        reasons.add("EXCESS_TOP5_DEPTH")
    with localcontext(calculation_context()):
        for side, levels in (("bid", bids), ("ask", asks)):
            previous = None
            for i, level in enumerate(levels[:5], 1):
                if not isinstance(level, (tuple, list)) or len(level) != 2:
                    reasons.add("INVALID_LEVEL_STRUCTURE")
                    continue
                p = _value(level[0], "price", reasons)
                q = _value(level[1], "quantity", reasons)
                row[f"{side}_price_{i}"] = p
                row[f"{side}_quantity_{i}"] = q
                if p is not None and previous is not None and ((side == "bid" and p >= previous) or (side == "ask" and p <= previous)):
                    reasons.add("UNSORTED_DEPTH")
                previous = p
        try:
            row["mid_price"], row["spread"], row["spread_bps"] = _quotes(row["bid_price_1"], row["ask_price_1"], reasons)
            for side in ("bid", "ask"):
                for i in range(1, 6):
                    quantities = [row[f"{side}_quantity_{j}"] for j in range(1, i + 1)]
                    if all(q is not None for q in quantities):
                        row[f"cumulative_{side}_quantity_{i}"] = sum(quantities, Decimal(0))
                    price, mid = row[f"{side}_price_{i}"], row["mid_price"]
                    if price is not None and mid is not None and mid > 0:
                        distance = mid - price if side == "bid" else price - mid
                        row[f"{side}_distance_bps_{i}"] = distance / mid * Decimal(10000)
            for i in range(1, 6):
                row[f"level_imbalance_{i}"] = _imbalance(row[f"bid_quantity_{i}"], row[f"ask_quantity_{i}"], reasons, "ZERO_LEVEL_DENOMINATOR")
            for k in (1, 3, 5):
                row[f"obi_{k}"] = _imbalance(row[f"cumulative_bid_quantity_{k}"], row[f"cumulative_ask_quantity_{k}"], reasons, "ZERO_DEPTH_DENOMINATOR")
            bq, aq = row["bid_quantity_1"], row["ask_quantity_1"]
            bid, ask = row["bid_price_1"], row["ask_price_1"]
            if all(value is not None for value in (bq, aq, bid, ask)):
                if bq + aq == 0:
                    reasons.add("ZERO_MICROPRICE_DENOMINATOR")
                else:
                    micro = (ask * bq + bid * aq) / (bq + aq)
                    row["microprice"] = micro
                    if not bid <= micro <= ask:
                        reasons.add("MICROPRICE_OUT_OF_SPREAD")
                    if row["mid_price"] is not None and row["mid_price"] > 0:
                        row["microprice_deviation_bps"] = (micro - row["mid_price"]) / row["mid_price"] * Decimal(10000)
        except DecimalException:
            reasons.add("DECIMAL_ARITHMETIC_ERROR")
    return _finish(row, reasons)
