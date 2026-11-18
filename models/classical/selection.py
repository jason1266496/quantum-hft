"""Validation-only selection and an immutable all-model Test-label access barrier."""
import json,math
from datetime import datetime,timezone
from .registry import write_json,sha
def utc():return datetime.now(timezone.utc).isoformat()
def choose(candidates,model,*,split="Validation"):
    if split!="Validation" or not candidates:raise ValueError("SELECTION_MUST_USE_VALIDATION_ONLY")
    def key(item):
        metrics=item["validation_metrics"];config=item["config"]
        f1,balanced=metrics["macro_f1"],metrics["balanced_accuracy"]
        if not math.isfinite(f1) or not math.isfinite(balanced):raise ValueError("NONFINITE_SELECTION_METRIC")
        gamma_rank=0 if config.get("gamma")=="scale" else 1
        return (-f1,-balanced,gamma_rank if model=="rbf_svm" else 0,config.get("C",0))
    return min(candidates,key=key)
def seal(path,candidates,selected,model,horizon):
    document={"model":model,"horizon_ms":horizon,"candidate_configs":[x["config"] for x in candidates],
              "validation_candidates":candidates,"selected_config":selected["config"],
              "selection_metric":"macro_f1","tie_break_rule":"balanced_accuracy desc; RBF gamma=scale first; smaller C",
              "selection_split":"Validation","test_used_for_selection":False,"holdout_used":False,
              "selected_at_utc":utc(),"test_evaluated":False}
    digest=write_json(path,document)
    return document,digest

class TestGate:
    def __init__(self,paths,barrier_path):
        self.paths=paths;self.barrier_path=barrier_path;self.sealed=False
        self.hashes={};self.read_horizons=set();self.evaluated=set()
    def assert_selection_open(self):
        if self.sealed or self.barrier_path.exists():raise ValueError("TEST_SEALED_NO_RETUNING")
    def freeze(self):
        self.assert_selection_open()
        if not self.paths:raise ValueError("NO_SELECTION_MANIFESTS")
        for key,path in self.paths.items():
            value=json.loads(path.read_text())
            if value["test_evaluated"] or value["test_used_for_selection"] or value["selection_split"]!="Validation":
                raise ValueError("INVALID_SELECTION_SEAL")
            self.hashes[key]=sha(path)
        write_json(self.barrier_path,{"status":"ALL_SELECTIONS_SEALED_BEFORE_ANY_TEST_LABEL_READ",
                    "selected_at_utc":utc(),"selection_sha256":self.hashes,
                    "test_label_access_started":False,"retuning_allowed":False})
        self.sealed=True
    def authorize_test_read(self,horizon):
        if not self.sealed:raise ValueError("TEST_LABEL_READ_BEFORE_SELECTION_SEAL")
        if horizon in self.read_horizons:raise ValueError("TEST_LABELS_ALREADY_READ")
        for key,path in self.paths.items():
            if sha(path)!=self.hashes[key]:raise ValueError("SELECTION_MANIFEST_CHANGED")
        self.read_horizons.add(horizon)
    def claim_evaluation(self,key,horizon):
        if not self.sealed or horizon not in self.read_horizons:raise ValueError("TEST_ACCESS_NOT_AUTHORIZED")
        if key in self.evaluated:raise ValueError("TEST_EVALUATION_ALREADY_PERFORMED")
        if sha(self.paths[key])!=self.hashes[key]:raise ValueError("SELECTION_MANIFEST_CHANGED")
        self.evaluated.add(key)
        return self.hashes[key]
    def assert_all_evaluated_once(self):
        if self.evaluated!=set(self.paths):raise ValueError("INCOMPLETE_TEST_EVALUATION")
