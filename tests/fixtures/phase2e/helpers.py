"""Artificial times/labels only; no HFT or prior-phase input is opened."""
from pathlib import Path
from data_pipeline.splits.schema import FeatureIndex,LabelIndex,SourceData,HORIZONS
from data_pipeline.splits.policy import whole_session_plan,depth_plan,scaler_policy
from data_pipeline.splits.matcher_policy import choose_policy
from data_pipeline.splits.splitter import training_candidates,build_membership
from data_pipeline.splits.walk_forward import build_windows
FIXTURES=Path(__file__).parent

def source(sid,start=0,n=21,view="aggregate_core_v1",times=None):
    if times is None:times=[start+i*100 for i in range(n)]
    rows=[FeatureIndex(sid,"session_"+sid,view,i+1,t,str(t)+":"+str(i+1)) for i,t in enumerate(times)]
    labels={}
    for h in HORIZONS:
        values=[]
        for i,t in enumerate(times):
            target=next((v for v in times[i+1:] if v>=t+h),None)
            values.append(LabelIndex(target,None if target is None else target-t-h,
                                     target is not None,"" if target is not None else "SESSION_TAIL_INSUFFICIENT"))
        labels[h]=values
    return SourceData(sid,"session_"+sid,view,rows,labels,"a"*64,{str(h):"b"*64 for h in HORIZONS})

def sources(view="aggregate_core_v1"):
    if view=="depth_top5_v1":
        return [source("replay_events_1000",60000,10,view),
                source("replay_events_50000",100000,500,view)]
    return [source("csv_early_"+str(i),i*10000) for i in range(4)]+[
        source("replay_events_1000",60000,10),source("replay_events_50000",100000,500),
        source("csv_latest",200000)]

def pipeline(view="depth_top5_v1"):
    data=sources(view)
    plan=depth_plan(data[-1]) if view=="depth_top5_v1" else whole_session_plan(data)
    policy=choose_policy(training_candidates(data,plan),view)
    membership=build_membership(data,plan,policy)
    windows=build_windows(data,plan)
    return data,plan,policy,membership,scaler_policy(),windows

def candidates(errors=(0,)*17+(1,1,99)):
    return {h:[{"source_id":"artificial","session_id":"synthetic","record_index":i+1,
                "current_event_time_ms":i*1000,"target_event_time_ms":i*1000+h+error,
                "match_error_ms":error,"training_end_exclusive":1000000,
                "split":"Train","is_holdout":False} for i,error in enumerate(errors)]
            for h in HORIZONS}
