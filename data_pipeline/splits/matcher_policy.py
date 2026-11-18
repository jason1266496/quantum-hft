"""Training-candidate-only match error selection, with fixed distortion guardrails."""
from decimal import Decimal,ROUND_CEILING
import hashlib,json
from .schema import HORIZONS,CONTEXT,decimal_text

STATIC_THRESHOLDS=(0,1,2,5,10,25,50,100)
MIN_RETENTION=Decimal("0.90")
MAX_NOMINAL_DEVIATION=Decimal("0.05")

def percentile(values,p):
    if not values:return None
    data=sorted(Decimal(x) for x in values)
    position=Decimal(len(data)-1)*Decimal(str(p))/100
    lower=int(position);upper=min(lower+1,len(data)-1);fraction=position-lower
    return data[lower]*(1-fraction)+data[upper]*fraction

def choose_policy(candidates,view):
    selected={};analyses={};scope={}
    for h in HORIZONS:
        samples=candidates[h]
        if not samples:
            return {"status":"NEED_POLICY_REVIEW","reason":"NO_TRAINING_CANDIDATE_LABELS"}
        for row in samples:
            if row["split"]!="Train" or row.get("is_holdout",False) or row["target_event_time_ms"]>=row["training_end_exclusive"]:
                raise ValueError("POLICY_SELECTION_MUST_BE_TRAINING_ONLY")
        values=[r["match_error_ms"] for r in samples]
        if any(type(v) is not int or v<0 for v in values):
            raise ValueError("INVALID_TRAINING_MATCH_ERROR")
        stats={f"p{p}":decimal_text(percentile(values,p)) for p in (50,75,90,95,97.5,99)}
        stats.update({"count":len(values),"max":max(values)})
        options=[(str(t),Decimal(t)) for t in STATIC_THRESHOLDS]
        options += [("TRAIN_P95",percentile(values,95)),("TRAIN_P99",percentile(values,99))]
        evaluations=[]
        for name,threshold in options:
            kept=sum(Decimal(v)<=threshold for v in values)
            rate=CONTEXT.divide(Decimal(kept),Decimal(len(values)))
            distortion=CONTEXT.divide(threshold,Decimal(h))
            evaluations.append({"candidate":name,"threshold_ms":decimal_text(threshold),
                                "retained":kept,"eligible_training_count":len(values),
                                "valid_retention_rate":decimal_text(rate),
                                "maximum_allowed_nominal_deviation_ratio":decimal_text(distortion),
                                "passes_coverage":rate>=MIN_RETENTION,
                                "passes_distortion_cap":distortion<=MAX_NOMINAL_DEVIATION})
        acceptable=[x for x in evaluations if x["passes_coverage"] and x["passes_distortion_cap"]]
        if not acceptable:
            return {"status":"NEED_POLICY_REVIEW","reason":"NO_CANDIDATE_MEETS_FIXED_GUARDRAILS",
                    "feature_view":view,"horizon":h,"analysis":evaluations}
        chosen=min(acceptable,key=lambda x:(Decimal(x["threshold_ms"]),x["candidate"].startswith("TRAIN_"),x["candidate"]))
        selected[str(h)]=chosen["threshold_ms"]
        analyses[str(h)]={"statistics":stats,"candidates":evaluations,"chosen_retention":chosen["valid_retention_rate"]}
        identities=[{k:r[k] for k in ("source_id","session_id","record_index","current_event_time_ms",
                                     "target_event_time_ms","match_error_ms","training_end_exclusive")}
                    for r in samples]
        scope[str(h)]={"count":len(samples),"source_ids":sorted({r["source_id"] for r in samples}),
                       "current_start":min(r["current_event_time_ms"] for r in samples),
                       "current_end":max(r["current_event_time_ms"] for r in samples),
                       "target_end":max(r["target_event_time_ms"] for r in samples),
                       "candidate_identity_sha256":hashlib.sha256(json.dumps(identities,sort_keys=True,separators=(",",":")).encode()).hexdigest()}
    return {"status":"PASS","feature_view":view,
            "selection_data_scope":{"name":"TRAINING_CANDIDATE_REGION","per_horizon":scope,
                                    "targets_must_end_before_training_boundary":True},
            "threshold_candidates":[*STATIC_THRESHOLDS,"TRAIN_P95","TRAIN_P99"],
            "retention_by_candidate":analyses,"chosen_policy":"MINIMUM_THRESHOLD_MEETING_TRAINING_COVERAGE_AND_DISTORTION_CAP",
            "chosen_threshold_by_horizon":selected,
            "horizon_specific_thresholds_required":len(set(selected.values()))>1,
            "guardrails":{"minimum_training_retention":"0.90","maximum_error_over_nominal_horizon":"0.05",
                          "fixed_before_training_distribution_evaluation":True},
            "rationale":"Select the smallest evaluated threshold meeting >=90% Training Candidate retention and <=5% of nominal horizon. This bounds timing distortion, especially at 100ms, and does not maximize sample retention. Failure to meet both requires policy review; no return values or later data select thresholds.",
            "test_data_used_for_selection":False,"final_holdout_used_for_selection":False,
            "phase2d_all_data_quantiles_used":False}

def accepted(error,horizon,policy):
    return Decimal(error)<=Decimal(policy["chosen_threshold_by_horizon"][str(horizon)])
