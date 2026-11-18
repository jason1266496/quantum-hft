"""Real audit-hook checks; no skips, mocks or writes to protected targets."""
import unittest,io,os,json,stat
from pathlib import Path
from experiments.phase4b1_recovery import scope,harness
class RecoveryScopeTests(unittest.TestCase):
    def policy(self):return scope.ACTIVE
    def blocked(self,path,mode="wb"):
        with self.assertRaises(scope.ScopeViolation):
            with open(path,mode) as f:f.write(b"unauthorized")
    def test_dill_import_completed(self):
        import dill
        self.assertTrue(dill.__version__)
    def test_real_null_character_device(self):
        p=Path("/dev/null");s=p.lstat()
        self.assertTrue(stat.S_ISCHR(s.st_mode));self.assertFalse(p.is_symlink());self.assertEqual((os.major(s.st_rdev),os.minor(s.st_rdev)),(1,3))
    def test_exact_dill_rplus_probe_allowed_and_logged(self):
        import dill._dill as d,io
        before=len(self.policy().events)
        self.assertIs(d.get_file_type("r+b",buffering=-1),io.BufferedRandom)
        self.assertTrue(any(e["kind"]=="ALLOWED_NULL_TYPE_PROBE" and e["original_mode"]=="r+b" for e in self.policy().events[before:]))
    def test_exact_dill_writer_probe_allowed(self):
        import dill._dill as d,io
        self.assertIs(d.get_file_type("wb",buffering=-1),io.BufferedWriter)
    def test_direct_null_write_is_not_whitelisted(self):self.blocked("/dev/null","r+b")
    def test_other_device_not_allowed(self):self.blocked("/dev/zero","r+b")
    def test_unapproved_null_buffering_rejected(self):
        import dill._dill as d
        with self.assertRaises(scope.ScopeViolation):d.get_file_type("r+b",buffering=0)
    def test_absolute_external_write_denied(self):self.blocked("/tmp/quantum_hft_scope_forbidden_"+self.policy().run.name)
    def test_relative_escape_denied(self):self.blocked("artifacts/phase4b1_recovery/"+self.policy().run.name+"/../../FORBIDDEN_ESCAPE")
    def test_symlink_escape_denied(self):self.blocked(self.policy().run/"fixtures/escape_link")
    def test_Dataset_write_denied(self):self.blocked(scope.ROOT/"artifacts/datasets/btcusdt_aggregate_v1_20261026T202040Z/1000ms/RECOVERY_FORBIDDEN_PROBE")
    def test_old_FAIL_overwrite_denied(self):self.blocked(scope.ROOT/"artifacts/phase4b1/20261030T032635Z/completion_manifest.json")
    def test_legal_new_artifact_write(self):
        p=self.policy().run/"fixtures/allowed_artifact.json"
        with p.open("x") as f:f.write('{"artificial":true}')
        self.assertEqual(json.loads(p.read_text()),{"artificial":True})
    def test_existing_new_artifact_cannot_be_overwritten(self):
        p=self.policy().run/"fixtures/retained_fixture.txt"
        with p.open("x") as f:f.write("retained")
        self.blocked(p)
        self.assertEqual(p.read_text(),"retained")
    def test_os_open_external_write_denied(self):
        with self.assertRaises(scope.ScopeViolation):os.open("/tmp/quantum_hft_osopen_forbidden_"+self.policy().run.name,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    def test_all_denials_are_logged(self):
        before=len(self.policy().events);self.blocked("/dev/zero","r+b")
        self.assertEqual(len(self.policy().events),before+1);self.assertEqual(self.policy().events[-1]["kind"],"DENIED")
    def test_discovery_runtime_error_captured_with_traceback(self):
        log=io.StringIO();r=harness.discover(["tests.fixtures.phase4b1_recovery.import_error_fixture"],log)
        self.assertEqual(r["status"],"ERROR");self.assertIn("ARTIFICIAL_DISCOVERY_RUNTIME_ERROR",log.getvalue());self.assertIn("Traceback",log.getvalue())
