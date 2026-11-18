"""Artificial current-state rows and timing metadata; no model training."""
from decimal import Decimal
from data_pipeline.features.formulas import aggregate
from data_pipeline.datasets.schema import sample_id,decimal_text
from experiments.phase4b0 import audit,temporal as t
def raw(i=0,source="fixture",session="s",start=0,update_base=1000):
    now=start+i*100;v=aggregate(Decimal("99"),Decimal("101"),Decimal("2"),Decimal("1"))
    r={"feature_view":"aggregate_core_v1","source_id":source,"session_id":session,"record_index":str(i+1),"event_time_ms":str(now),
       "current_event_time_ms":str(now),"local_update_id":str(update_base+i),"first_update_id":"","final_update_id":"",
       "target_event_time_ms":str(now+1000),"actual_horizon_ms":"1000","requested_horizon_ms":"1000","match_error_ms":"0",
       "current_mid_price":"100","future_mid_price":"100","valid_feature_row":"true","valid_label":"true","future_return_bps":"0"}
    for k in ("best_bid","best_ask","bid_volume_5","ask_volume_5","mid_price","spread","spread_bps","obi_5"):r[k]=decimal_text(v[k])
    r["sample_id"]=sample_id(r);return r
def source(n=1000,name="fixture",start=0,update_base=1000):
    rows=[audit.project(raw(i,name,"s_"+name,start,update_base),i) for i in range(n)]
    region={"source_id":name,"session_id":"s_"+name,"start":start,"end_exclusive":start+n*100+1001}
    return rows,region
def prepared(n=1000,name="fixture",start=0,update_base=1000):
    rows,region=source(n,name,start,update_base);mapping,bounds,dups=t.leakage_groups(rows);audit.witnesses(rows,mapping)
    return rows,region,mapping,bounds
class PoisonLabels(dict):
    def __getitem__(self,key):
        if key in ("future_return_bps","class_label"):raise AssertionError("LABEL_SIGN_CONSULTED")
        return super().__getitem__(key)
