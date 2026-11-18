"""Artificial metadata fixture only; never used for formal training."""
def rows(n):
    return [{"sample_id":f"id{i:04d}","source_id":"fixture","session_id":"s","record_index":str(i+1),"event_time_ms":str(1000+i*100),
             "future_return_bps":str((i%3)-1),"obi_5":str(i)} for i in range(n)]
class PoisonLabels(dict):
    def __getitem__(self,key):
        if key in ("future_return_bps","class_label","obi_5"):raise AssertionError("LABEL_OR_FEATURE_CONSULTED")
        return super().__getitem__(key)
