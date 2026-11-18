"""Pure temporal/grouping primitives; no label-return access."""
from collections import defaultdict
from .contracts import canonical_sha
def key(r):return (r["t"],r["source"],r["session"],r["record"],r["id"])
def positions(n,k):
    if k<2 or n<k:raise ValueError("INSUFFICIENT_SAMPLES")
    return [i*(n-1)//(k-1) for i in range(k)]
def sample(rows,k):
    ordered=sorted(rows,key=key)
    if len({r["id"] for r in ordered})!=len(ordered):raise ValueError("DUPLICATE_SAMPLE_ID")
    return [ordered[i] for i in positions(len(ordered),k)]
def actual_endpoint(row):
    for field in ("event_time_ms","target_event_time_ms","actual_horizon_ms","requested_horizon_ms","match_error_ms"):
        if field not in row or row[field] in ("",None):raise ValueError("MISSING_"+field.upper())
    t=int(row["event_time_ms"]);end=int(row["target_event_time_ms"]);actual=int(row["actual_horizon_ms"]);h=int(row["requested_horizon_ms"]);error=int(row["match_error_ms"])
    if h!=1000 or end!=t+actual or error!=actual-h or actual<h:raise ValueError("INCONSISTENT_ACTUAL_LABEL_ENDPOINT")
    return end
def leakage_groups(rows):
    parent={r["id"]:r["id"] for r in rows};byuid={};bystate={};exact=0;ambiguous=0;conflicts=[];examples=[]
    if len(parent)!=len(rows):raise ValueError("DUPLICATE_SAMPLE_ID")
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):
        x,y=find(a),find(b)
        if x!=y:parent[max(x,y)]=min(x,y)
    for r in rows:
        if r["update"] in byuid:
            prev=byuid[r["update"]];union(prev["id"],r["id"])
            if (prev["t"],prev["state"])!=(r["t"],r["state"]):conflicts.append({"a":prev["id"],"b":r["id"],"update":r["update"]})
            else:
                exact+=1
                if len(examples)<10:examples.append({"a":prev["id"],"b":r["id"],"update":r["update"],"time":r["t"]})
        else:byuid[r["update"]]=r
        state=(r["t"],r["state"])
        if state in bystate:
            prev=bystate[state];union(prev["id"],r["id"])
            if prev["update"]!=r["update"]:ambiguous+=1
        else:bystate[state]=r
    buckets=defaultdict(list)
    for r in rows:buckets[find(r["id"])].append(r)
    mapping={};bounds={}
    for members in buckets.values():
        gid=canonical_sha(sorted(r["id"] for r in members))
        bounds[gid]={"min_t":min(r["t"] for r in members),"max_t":max(r["t"] for r in members),"max_end":max(r["end"] for r in members),"members":len(members)}
        for r in members:mapping[r["id"]]=gid
    return mapping,bounds,{"event_group_count":len(bounds),"exact_duplicate_observations":exact,"ambiguous_time_state_collisions":ambiguous,
      "conflicting_update_identity_count":len(conflicts),"conflict_examples":conflicts[:10],"duplicate_examples":examples,
      "global_namespace":"provided update-ID shared across all Train aliases; no source_id namespace isolation"}
def split_candidates(rows,region,mapping,bounds,embargo=0):
    if embargo<0:raise ValueError("NEGATIVE_EMBARGO")
    b=(region["start"]+region["end_exclusive"])//2
    train=[];val=[];counts={"Train_purged_by_actual_endpoint_or_group":0,"Validation_excluded_by_group_or_endpoint":0,"not_witness_eligible":0}
    for r in rows:
        if (r["source"],r["session"])!=(region["source_id"],region["session_id"]):raise ValueError("SESSION_BOUNDARY_MISMATCH")
        if not region["start"]<=r["t"]<region["end_exclusive"]:raise ValueError("EVENT_OUTSIDE_SESSION_REGION")
        if not r["eligible"]:counts["not_witness_eligible"]+=1;continue
        g=bounds[mapping[r["id"]]]
        if r["t"]<b:
            if g["max_t"]<b and g["max_end"]+embargo<b:train.append(r)
            else:counts["Train_purged_by_actual_endpoint_or_group"]+=1
        else:
            if g["min_t"]>=b and g["max_end"]<region["end_exclusive"]:val.append(r)
            else:counts["Validation_excluded_by_group_or_endpoint"]+=1
    return train,val,b,counts
def check_split(train,val,mapping,boundary,session_end,embargo=0):
    if not train or not val:raise ValueError("EMPTY_SPLIT")
    if set(r["id"] for r in train)&set(r["id"] for r in val):raise ValueError("SAMPLE_ID_OVERLAP")
    tg={mapping[r["id"]] for r in train};vg={mapping[r["id"]] for r in val}
    if tg&vg:raise ValueError("DUPLICATE_EVENT_GROUP_LEAKAGE")
    if len({(r["source"],r["session"]) for r in train+val})!=1:raise ValueError("CROSS_SESSION_SPLIT")
    if max(r["t"] for r in train)>=min(r["t"] for r in val):raise ValueError("TRAIN_NOT_EARLIER")
    if any(r["end"]+embargo>=boundary for r in train):raise ValueError("ACTUAL_ENDPOINT_OR_EMBARGO_LEAKAGE")
    if any(r["end"]>=session_end for r in val):raise ValueError("VALIDATION_LABEL_CROSSES_SESSION")
    # The actual target market event may not also be a Validation input.
    if {r["target_group"] for r in train}&vg:raise ValueError("TARGET_EVENT_GROUP_LEAKAGE")
    return {"status":"PASS","ID_overlap":0,"event_group_overlap":0,"max_Train_actual_endpoint":max(r["end"] for r in train),
      "min_Validation_event":min(r["t"] for r in val),"boundary":boundary,"embargo_ms":embargo,"Validation_adjacent_label_overlaps":sum(a["end"]>=b["t"] for a,b in zip(sorted(val,key=key),sorted(val,key=key)[1:]))}
