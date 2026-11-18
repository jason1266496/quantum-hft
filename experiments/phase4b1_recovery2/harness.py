"""Safety first, then all pinned regression cases. Never run official models."""
import os,sys,json,time,ast,hashlib,contextlib,unittest,traceback
from pathlib import Path
from experiments.phase4b1_recovery.harness import Tee,discover
from .scope import PrivateTmpScope,ROOT
def write(p,v):
    with Path(p).open("x",encoding="utf-8") as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
def case_manifest(names):
    expected=[];sources={}
    for name in names:
        path=ROOT/(name.replace(".","/")+".py");text=path.read_text()
        sources[str(path)]={"sha256":hashlib.sha256(text.encode()).hexdigest()}
        tree=ast.parse(text)
        for cls in tree.body:
            if isinstance(cls,ast.ClassDef):
                expected += [name+"."+cls.name+"."+n.name for n in cls.body if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")]
    return {"modules":list(names),"expected_cases":sorted(expected),"expected_count":len(expected),"source_files":sources,"version_control":"No Git claim; exact source SHA and explicit case IDs are sealed."}
def flatten(suite):
    ids=[]
    for t in suite:
        if isinstance(t,unittest.TestSuite):ids+=flatten(t)
        else:ids.append(t.id())
    return sorted(ids)
def run(run_id):
    run=ROOT/"artifacts/phase4b1_recovery"/run_id;policy=PrivateTmpScope(run,unit=True);started=time.perf_counter()
    expected_env={k:str(run/"tmp") for k in ("TMPDIR","TEMP","TMP")}
    if any(os.environ.get(k)!=v for k,v in expected_env.items()):raise RuntimeError("TMP_ENV_NOT_SET_BEFORE_PROCESS")
    safe_names=("tests.test_phase4b1_recovery2_safety",)
    full_names=("tests.test_phase4b1_recovery","tests.test_phase4b1","tests.test_phase4b0_temporal")
    manifests={"safety":case_manifest(safe_names),"regression":case_manifest(full_names)}
    write(run/"test_list_manifest.json",manifests)
    profile={"fixture_solver_fit_calls":[],"fixture_Quantum_evaluate_calls":[],"fixture_preprocessing_fit_calls":[],"forbidden_formal_calls":[]}
    stage="initialization";unraisable=[];outcomes={};records={}
    def profiler(frame,event,arg):
        if event!="call":return
        filename=frame.f_code.co_filename.replace("\\","/");name=frame.f_code.co_name
        if filename.endswith("/experiments/phase4b1/runner.py") and name in ("run","stage","prep_stage","first_kernel"):
            profile["forbidden_formal_calls"].append({"file":filename,"function":name});raise RuntimeError("FORMAL_EXECUTION_PROHIBITED")
        if name=="fit" and filename.endswith("/sklearn/svm/_base.py"):
            profile["fixture_solver_fit_calls"].append({"stage":stage,"test":policy.current_test})
        if name=="evaluate" and filename.endswith("/kernels/fidelity_statevector_kernel.py"):
            profile["fixture_Quantum_evaluate_calls"].append({"stage":stage,"test":policy.current_test})
        if name=="fit" and filename.endswith("/experiments/phase4b1/preprocessing.py"):
            profile["fixture_preprocessing_fit_calls"].append({"stage":stage,"test":policy.current_test})
    with (run/"logs/gate.stdout.txt").open("x") as out,(run/"logs/gate.stderr.txt").open("x") as err:
        with contextlib.redirect_stdout(Tee(out,sys.stdout)),contextlib.redirect_stderr(Tee(err,sys.stderr)):
            policy.install();sys.setprofile(profiler)
            def unraisable_hook(arg):
                unraisable.append({"type":str(arg.exc_type),"value":str(arg.exc_value),"object":str(arg.object)})
                traceback.print_exception(arg.exc_type,arg.exc_value,arg.exc_traceback)
            sys.unraisablehook=unraisable_hook
            success=False
            try:
                import tempfile
                initial_cache=tempfile.tempdir
                if initial_cache is not None:raise RuntimeError("TEMP_DIR_ALREADY_CACHED_BEFORE_GUARDED_SELECTION")
                selected=tempfile.gettempdir()
                if selected!=str(run/"tmp"):raise RuntimeError("TEMP_DIR_SELECTED_OUTSIDE_PRIVATE_SCOPE")
                write(run/"child_environment.json",{"pid":os.getpid(),"python":sys.executable,"python_version":sys.version,"environment":{k:os.environ.get(k) for k in ("TMPDIR","TEMP","TMP","PYTHONDONTWRITEBYTECODE")},
                   "initial_tempfile_cache":initial_cache,"selected_tempfile_directory":selected,"dont_write_bytecode":sys.dont_write_bytecode,"fresh_process":True})
                for stage,names in (("safety",safe_names),("regression",full_names)):
                    manifest=manifests[stage];discovery=discover(names,sys.stderr)
                    if discovery["status"]!="PASS":raise RuntimeError(stage.upper()+"_IMPORT_ERROR")
                    actual=flatten(discovery["suite"])
                    if actual!=manifest["expected_cases"]:raise RuntimeError("CASE_LIST_MISMATCH")
                    case_results=[];outcomes[stage]=case_results;total=len(actual)
                    class Result(unittest.TextTestResult):
                        def startTest(self,test):policy.current_test=test.id();super().startTest(test)
                        def addSuccess(self,test):super().addSuccess(test);case_results.append({"id":test.id(),"outcome":"PASS"})
                        def addError(self,test,err):super().addError(test,err);case_results.append({"id":test.id(),"outcome":"ERROR","traceback":self._exc_info_to_string(err,test)})
                        def addFailure(self,test,err):super().addFailure(test,err);case_results.append({"id":test.id(),"outcome":"FAIL","traceback":self._exc_info_to_string(err,test)})
                        def addSkip(self,test,reason):super().addSkip(test,reason);case_results.append({"id":test.id(),"outcome":"SKIP","reason":reason})
                        def stopTest(self,test):
                            super().stopTest(test)
                            if self.testsRun%10==0 or self.testsRun==total:print(json.dumps({"stage":"RECOVERY2_"+stage.upper(),"processed":self.testsRun,"total":total,"percent":100*self.testsRun/total,"elapsed_seconds":time.perf_counter()-started,"eta_seconds":"NOT_AVAILABLE"}),flush=True)
                            policy.current_test=None
                    result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2,resultclass=Result).run(discovery["suite"])
                    good=result.wasSuccessful() and not result.skipped and result.testsRun==total and len(case_results)==total and not unraisable
                    record={"status":"PASS" if good else "RECOVERY_BLOCKED","expected":manifest["expected_count"],"discovered":len(actual),"tests_run":result.testsRun,
                       "failures":len(result.failures),"errors":len(result.errors),"skipped":len(result.skipped),"cases":case_results,"import_errors":0}
                    records[stage]=record;write(run/"summary"/(stage+"_tests.json"),record)
                    if not good:raise RuntimeError(stage.upper()+"_TEST_GATE_FAILED")
                if profile["forbidden_formal_calls"]:raise RuntimeError("FORMAL_EXECUTION_ATTEMPTED")
                if any(not v.get("deleted") for v in policy.created.values()):raise RuntimeError("TEMPORARY_PATHS_NOT_CLEANED")
                success=True
            except BaseException:
                traceback.print_exc()
                write(run/"discovery_or_gate_error.json",{"status":"RECOVERY_BLOCKED","stage":stage,"traceback":traceback.format_exc()})
            policy.current_test=None
            # Keep the audit hook active; stop only the non-enforcing call profiler after finishing.
            sys.setprofile(None)
            record={"status":"PASS" if success else "RECOVERY_BLOCKED","stages":{k:{x:v for x,v in v.items() if x!="cases"} for k,v in records.items()},
              "elapsed_seconds":time.perf_counter()-started,"unraisable_errors":unraisable,"formal_model_fits":0,"formal_predictions":0,"formal_preprocessing_fits":0,"formal_Quantum_evaluate_calls":0,
              "official_values_loaded":False,"Test_evaluated":False,"Holdout_opened":False,"full_regression_started": "regression" in records}
            write(run/"scope_audit.json",policy.summary());write(run/"fixture_call_profile.json",profile);write(run/"summary/unit_gate.json",record)
            print(json.dumps(record),flush=True)
    return record
