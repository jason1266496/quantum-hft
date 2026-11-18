"""Artificial current rows, endpoint metadata, and complete stage contracts."""
import copy
import numpy as np
from tests.fixtures.phase4b0.helpers import raw
from data_pipeline.datasets.schema import sample_id
from experiments.phase4b1 import contracts as c,analysis as a
def member(row,index):
    return {"sample_id":row["sample_id"],"source_id":row["source_id"],"session_id":row["session_id"],"record_index":int(row["record_index"]),"event_time_ms":int(row["event_time_ms"]),
       "provided_update_id":int(row["local_update_id"]),"actual_target_event_time_ms":int(row["target_event_time_ms"]),"source_Train_file_row_index":index,
       "leakage_group":c.digest([row["sample_id"]]),"actual_target_group":c.digest(["artificial_target_"+row["sample_id"]])}
def data():
    fold={"fold_id":1,"region":{"source_id":"fixture","session_id":"s","start":0,"end_exclusive":100000},"boundary":15000}
    selected={};index=0
    for split,counts,start in (("Train",(16,76,4),0),("Validation",(32,253,99),200)):
        members=[]
        ys=[j for j,n in enumerate(counts) for _ in range(n)]
        for i,y in enumerate(ys):
            row=raw(i+start)
            row["future_return_bps"]=str((-100,0,100)[y]);row["future_mid_price"]=str((99,100,101)[y])
            selected[row["sample_id"]]=row;members.append(member(row,index));index+=1
        fold[split]={"sample_ids":[m["sample_id"] for m in members],"members":members}
    return fold,selected
def kernel_data():
    rng=np.random.default_rng(42)
    return rng.uniform(.1,3.,(9,4)),np.asarray([0,0,0,1,1,1,1,2,2],dtype=np.int64),rng.uniform(.1,3.,(6,4))
def stage():
    y=np.asarray([0,0,1,1,2,2]);pred=np.asarray([0,1,1,1,0,2])
    record={"predictions":pred.tolist(),"prediction_sha256":c.digest(pred.tolist()),"metrics":a.metric(y,pred),"execution":{"actual_class_weights":{n:1. for n in c.NAMES}}}
    return {"fold_id":1,"inputs":{"Train":"artificial","Validation":"artificial"},"preprocessing_parameters":{"mean":[0.,1.,2.,3.]},"preprocessing_sha256":c.digest([0]),
       "angle_array_shas":{"Train":c.digest([1]),"Validation":c.digest([2])},"kernels":{"fixture":c.digest([3])},"models":{n:copy.deepcopy(record) for n in c.MODELS}}
