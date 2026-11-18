"""Build raw matched future returns and descriptive horizon quality per feature view."""
from collections import Counter
from contextlib import ExitStack
from decimal import Decimal
import json
import time
from .schema import HORIZONS_MS, LABEL_FIELDS, CONTEXT, decimal_text, return_bps
from .matcher import first_target, segments
from .reference import reference_label
from .validator import read_feature_rows
from .writer import LabelWriter, write_json

REFERENCE_KEYS = ("target_event_time_ms", "actual_horizon_ms", "match_error_ms",
                  "future_mid_price", "future_return_bps", "valid_label", "invalid_reason")

def _percentile(sorted_values, percent):
    if not sorted_values:
        return None
    position = CONTEXT.divide(CONTEXT.multiply(Decimal(len(sorted_values)-1), Decimal(percent)), Decimal(100))
    lower = int(position)
    upper = min(lower + 1, len(sorted_values)-1)
    fraction = CONTEXT.subtract(position, Decimal(lower))
    return CONTEXT.add(CONTEXT.multiply(sorted_values[lower], CONTEXT.subtract(Decimal(1), fraction)),
                       CONTEXT.multiply(sorted_values[upper], fraction))

def distribution(values, percentiles):
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None,
                **{f"p{p}": None for p in percentiles}}
    ordered = sorted(Decimal(v) for v in values)
    total = sum(ordered, Decimal(0))
    result = {"count": len(ordered), "min": decimal_text(ordered[0]),
              "max": decimal_text(ordered[-1]),
              "mean": decimal_text(CONTEXT.divide(total, Decimal(len(ordered)))),
              "median": decimal_text(_percentile(ordered, 50))}
    for p in percentiles:
        result[f"p{p}"] = decimal_text(_percentile(ordered, p))
    return result

def reference_indices(source_id, count):
    if source_id == "replay_events_1000":
        return set(range(count))
    if source_id == "replay_events_50000":
        return set(range(min(1000, count))) | set(range(max(0, count-1000), count)) | set(range(999, count, 1000))
    midpoint = count // 2
    return set(range(min(500, count))) | set(range(max(0, midpoint-250), min(count, midpoint+250))) | set(range(max(0,count-500),count))

def event_interval_profile(rows):
    per_session = {}
    by_session = {}
    for row in rows:
        by_session.setdefault(row.session_id, []).append(row)
    for session, items in by_session.items():
        deltas = [items[i].event_time_ms - items[i-1].event_time_ms for i in range(1,len(items))]
        counts = {"negative": sum(v<0 for v in deltas), "zero": sum(v==0 for v in deltas)}
        for h in HORIZONS_MS:
            counts[f"greater_than_{h}ms"] = sum(v>h for v in deltas)
        intervals = [v for v in deltas if v>=0]
        stat = distribution(intervals, (50,95,99))
        large = [{"from_record_index": items[i-1].record_index,
                  "to_record_index": items[i].record_index,
                  "from_event_time_ms": items[i-1].event_time_ms,
                  "to_event_time_ms": items[i].event_time_ms,
                  "delta_event_ms": deltas[i-1]}
                 for i in range(1,len(items)) if deltas[i-1] > 100]
        per_session[session] = {"interval_count": len(deltas), **counts,
                                "distribution_ms": stat, "intervals_gt_100ms": large,
                                "gap_threshold_ms": None,
                                "candidate_policy": "SELECT_FROM_TRAINING_SIDE_ONLY_IN_PHASE_2E"}
    return per_session

def _label(rows, times, index, horizon, end, backward_boundary, rollback_indices):
    current = rows[index]
    j = first_target(rows, times, index, horizon, end)
    target = None if j is None else rows[j]
    actual = None if target is None else target.event_time_ms - current.event_time_ms
    error = None if actual is None else actual - horizon
    reason = ""
    if index in rollback_indices:
        reason = "EVENT_TIME_BACKWARDS"
    elif not current.valid_feature_row:
        reason = "INVALID_CURRENT_FEATURE_ROW"
    elif current.mid_price is None or current.mid_price <= 0:
        reason = "INVALID_CURRENT_PRICE"
    elif target is None:
        reason = "EVENT_TIME_BACKWARDS" if backward_boundary else "SESSION_TAIL_INSUFFICIENT"
    elif not target.valid_feature_row:
        reason = "INVALID_FUTURE_FEATURE_ROW"
    elif target.mid_price is None or target.mid_price <= 0:
        reason = "INVALID_FUTURE_PRICE"
    value = None if reason else return_bps(current.mid_price, target.mid_price)
    data = {
        "source_id": current.source_id, "session_id": current.session_id,
        "record_index": current.record_index, "feature_view": current.feature_view,
        "requested_horizon_ms": horizon, "current_event_time_ms": current.event_time_ms,
        "target_event_time_ms": None if target is None else target.event_time_ms,
        "actual_horizon_ms": actual, "match_error_ms": error,
        "current_mid_price": current.mid_price,
        "future_mid_price": None if target is None else target.mid_price,
        "future_return_bps": value,
        "valid_label": not bool(reason), "invalid_reason": reason,
    }
    assert tuple(data) == LABEL_FIELDS
    return data

def build_view(root, source_id, view, output_dir, *, compare_reference=True, progress_every=10000):
    """Create one source/session/view directory; every file uses exclusive creation."""
    if progress_every < 1:
        raise ValueError("INVALID_PROGRESS_EVERY")
    rows = read_feature_rows(root, source_id, view)
    output_dir.mkdir(exist_ok=False)
    if not rows:
        raise ValueError("EMPTY_FEATURE_INPUT")
    sessions = {row.session_id for row in rows}
    if len(sessions) != 1:
        raise ValueError("CROSS_SESSION_INPUT")
    intervals = event_interval_profile(rows)
    segment_list = list(segments(rows))
    times = [row.event_time_ms for row in rows]
    rollback_indices = {i for i in range(1,len(rows)) if rows[i].event_time_ms < rows[i-1].event_time_ms}
    sample = reference_indices(source_id, len(rows)) if compare_reference else set()
    reference = {"status": "PASS" if compare_reference else "NOT_RUN_REPEAT",
                 "sample_row_count": len(sample), "comparisons": 0,
                 "mismatch_count": 0, "mismatches": [], "method": "independent_linear_forward_search"}
    summary = {}
    started = time.monotonic()
    with ExitStack() as stack:
        writers = {h: stack.enter_context(LabelWriter(output_dir/f"labels_{h}ms.csv")) for h in HORIZONS_MS}
        invalid = stack.enter_context(LabelWriter(output_dir/"invalid_labels.csv"))
        for horizon in HORIZONS_MS:
            counts = Counter()
            returns, errors, actuals = [], [], []
            for begin,end,backward_boundary in segment_list:
                for i in range(begin,end):
                    label = _label(rows,times,i,horizon,end,backward_boundary,rollback_indices)
                    writers[horizon].write(label)
                    if not label["valid_label"]:
                        invalid.write(label)
                    if label["target_event_time_ms"] is None:
                        counts["unmatched_rows"] += 1
                    else:
                        counts["matched_rows"] += 1
                        errors.append(label["match_error_ms"])
                        actuals.append(label["actual_horizon_ms"])
                    if label["valid_label"]:
                        counts["valid_labels"] += 1
                        returns.append(label["future_return_bps"])
                        if label["future_return_bps"] == 0:
                            counts["zero_return_count"] += 1
                    else:
                        counts["invalid_labels"] += 1
                        counts[label["invalid_reason"]] += 1
                    if i in sample:
                        ref = reference_label(rows,i,horizon,end,backward_boundary)
                        if i in rollback_indices:
                            ref["valid_label"] = False
                            ref["invalid_reason"] = "EVENT_TIME_BACKWARDS"
                            ref["future_return_bps"] = None
                        reference["comparisons"] += 1
                        differences = [key for key in REFERENCE_KEYS if label[key] != ref[key]]
                        if differences:
                            reference["mismatch_count"] += 1
                            if len(reference["mismatches"]) < 20:
                                reference["mismatches"].append({"record_index": rows[i].record_index,
                                                                 "horizon_ms": horizon, "fields": differences})
                    if (i+1) % progress_every == 0:
                        done = (HORIZONS_MS.index(horizon)*len(rows)) + i + 1
                        total = len(rows)*len(HORIZONS_MS)
                        elapsed = time.monotonic()-started
                        print(json.dumps({"source_id":source_id,"feature_view":view,"processed_labels":done,
                                          "total_labels":total,"percent":round(done*100/total,2),
                                          "elapsed_seconds":round(elapsed,3),
                                          "eta_seconds":round((total-done)*elapsed/done,3)}),flush=True)
            n=len(rows)
            summary[str(horizon)] = {
                "requested_horizon_ms": horizon, "input_rows": n,
                "matched_rows": counts["matched_rows"], "unmatched_rows": counts["unmatched_rows"],
                "valid_labels": counts["valid_labels"], "invalid_labels": counts["invalid_labels"],
                "session_tail_count": counts["SESSION_TAIL_INSUFFICIENT"],
                "invalid_current_price": counts["INVALID_CURRENT_PRICE"],
                "invalid_future_price": counts["INVALID_FUTURE_PRICE"],
                "invalid_current_feature_row": counts["INVALID_CURRENT_FEATURE_ROW"],
                "invalid_future_feature_row": counts["INVALID_FUTURE_FEATURE_ROW"],
                "event_time_backwards": sum(v["negative"] for v in intervals.values()),
                "duplicate_event_time": sum(v["zero"] for v in intervals.values()),
                "zero_return_count": counts["zero_return_count"],
                "zero_return_fraction": decimal_text(CONTEXT.divide(Decimal(counts["zero_return_count"]),
                                                 Decimal(counts["valid_labels"]))) if counts["valid_labels"] else None,
                "return_distribution_bps": distribution(returns,(1,5,25,50,75,95,99)),
                "match_error_distribution_ms": distribution(errors,(50,75,90,95,99)),
                "actual_horizon_distribution_ms": distribution(actuals,(50,95,99)),
                "invalid_reasons": {k:v for k,v in sorted(counts.items()) if k in (
                    "SESSION_TAIL_INSUFFICIENT","INVALID_CURRENT_PRICE","INVALID_FUTURE_PRICE",
                    "INVALID_CURRENT_FEATURE_ROW","INVALID_FUTURE_FEATURE_ROW","EVENT_TIME_BACKWARDS")},
            }
    results = {str(h): writers[h].close() for h in HORIZONS_MS}
    results["invalid_labels"] = invalid.close()
    if reference["mismatch_count"]:
        reference["status"] = "FAIL"
    quality = {"status": "PASS" if reference["mismatch_count"]==0 else "FAIL",
               "source_id":source_id,"session_id":rows[0].session_id,"feature_view":view,
               "input_rows":len(rows),"horizons":summary,
               "event_interval_profile":intervals,
               "max_match_error_ms":None,"gap_threshold_ms":None,
               "threshold_selection_status":"DEFERRED_TO_TRAINING_SIDE_PROTOCOL",
               "float_used_for_labels":False,"local_timestamp_used":False,
               "output_files":results}
    write_json(output_dir/"label_quality.json",quality)
    write_json(output_dir/"match_error_statistics.json",
               {"source_id":source_id,"session_id":rows[0].session_id,"feature_view":view,
                "per_horizon":{str(h):{"match_error":summary[str(h)]["match_error_distribution_ms"],
                                        "actual_horizon":summary[str(h)]["actual_horizon_distribution_ms"]}
                               for h in HORIZONS_MS},
                "threshold_ms":None,"selection_status":"DEFERRED_TO_TRAINING_SIDE_PROTOCOL"})
    write_json(output_dir/"reference_comparison.json",reference)
    print(json.dumps({"source_id":source_id,"feature_view":view,
                      "processed_labels":len(rows)*len(HORIZONS_MS),
                      "total_labels":len(rows)*len(HORIZONS_MS),
                      "percent":100,"elapsed_seconds":round(time.monotonic()-started,3),
                      "eta_seconds":0}),flush=True)
    return quality, reference
