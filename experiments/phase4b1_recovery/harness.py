"""Capture discovery before imports; execute complete artificial regression gate."""
import os,sys,json,time,traceback,unittest,contextlib,ast
from pathlib import Path
from .scope import WriteScope,ROOT
def write(p,v):
    with Path(p).open("x",encoding="utf-8") as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
def discover(names,log):
    loader=unittest.TestLoader();suite=unittest.TestSuite()
    try:
        for name in names:suite.addTests(loader.loadTestsFromName(name))
        if loader.errors:
            text="\n".join(loader.errors);log.write(text)
            return {"status":"ERROR","suite":None,"traceback":text}
        return {"status":"PASS","suite":suite,"count":suite.countTestCases()}
    except BaseException:
        text=traceback.format_exc();log.write(text);log.flush()
        return {"status":"ERROR","suite":None,"traceback":text}
class Tee:
    def __init__(self,a,b):self.a,self.b=a,b
    def write(self,s):self.a.write(s);self.a.flush();return self.b.write(s)
    def flush(self):self.a.flush();self.b.flush()
def run(run_id):
    run=ROOT/"artifacts/phase4b1_recovery"/run_id
    # The fixture symlink is created only inside this new run, before installing the guard.
    link=run/"fixtures"/"escape_link";link.symlink_to("/tmp/quantum_hft_forbidden_"+run_id)
    names=("tests.test_phase4b1_recovery","tests.test_phase4b1","tests.test_phase4b0_temporal")
    expected=sum(sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith("test_") for n in ast.walk(ast.parse((ROOT/(name.replace(".","/")+".py")).read_text()))) for name in names)
    policy=WriteScope(run,unit=True);started=time.perf_counter();result=None;discovery=None
    with (run/"logs/recovery_tests.stdout.txt").open("x") as out,(run/"logs/recovery_tests.stderr.txt").open("x") as err:
        with contextlib.redirect_stdout(Tee(out,sys.stdout)),contextlib.redirect_stderr(Tee(err,sys.stderr)):
            policy.install()
            try:
                import dill
                print("DILL_IMPORT_PASS",flush=True)
                discovery=discover(names,sys.stderr)
                if discovery["status"]!="PASS":raise RuntimeError("DISCOVERY_ERROR")
                total=discovery["count"]
                if total!=expected:raise RuntimeError("DISCOVERED_COUNT_MISMATCH")
                class Result(unittest.TextTestResult):
                    def startTest(self,test):policy.current_test=test.id();super().startTest(test)
                    def stopTest(self,test):
                        super().stopTest(test)
                        if self.testsRun%10==0 or self.testsRun==total:
                            print(json.dumps({"stage":"RECOVERY_FIXTURE_GATE","processed":self.testsRun,"total":total,"percent":100*self.testsRun/total,"elapsed_seconds":time.perf_counter()-started,"eta_seconds":"NOT_AVAILABLE"}),flush=True)
                        policy.current_test=None
                result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2,resultclass=Result).run(discovery["suite"])
                success=result.wasSuccessful() and not result.skipped and result.testsRun==expected
            except BaseException:
                traceback.print_exc();success=False
            policy.current_test=None
            record={"status":"PASS" if success else "RECOVERY_BLOCKED","expected_tests":expected,"discovered_tests":discovery.get("count",0) if discovery else 0,
              "tests_run":result.testsRun if result else 0,"failures":len(result.failures) if result else 0,"errors":len(result.errors) if result else 1,
              "skipped":len(result.skipped) if result else 0,"elapsed_seconds":time.perf_counter()-started,"official_values_loaded":False,"formal_fits":0,"formal_Quantum_evaluate_calls":0}
            write(run/"summary/unit_tests.json",record);write(run/"scope_audit.json",policy.summary())
            print(json.dumps(record),flush=True)
    return record
