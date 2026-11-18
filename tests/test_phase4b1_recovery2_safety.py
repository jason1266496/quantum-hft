"""Real OS security and import checks, confined to the new private temporary directory."""
import unittest,os,stat,io
from pathlib import Path
from experiments.phase4b1_recovery2 import scope
from experiments.phase4b1_recovery import harness as old_harness
class PrivateTmpSafetyTests(unittest.TestCase):
    def p(self):return scope.active()
    def blocked(self,path,mode="wb"):
        with self.assertRaises(scope.ScopeViolation):
            with open(path,mode) as f:f.write(b"forbidden")
    def test_00_fresh_process_environment_and_permissions(self):
        p=self.p();s=p.tmp.lstat()
        self.assertEqual({os.environ[k] for k in ("TMPDIR","TEMP","TMP")},{str(p.tmp)})
        self.assertEqual(stat.S_IMODE(s.st_mode),0o700);self.assertEqual(s.st_uid,os.geteuid())
        self.assertFalse(p.tmp.is_symlink());self.assertEqual(p.tmp.resolve(),p.tmp);self.assertTrue(__import__("sys").dont_write_bytecode)
    def test_01_tempfile_gettempdir_exact(self):
        import tempfile
        self.assertEqual(tempfile.gettempdir(),str(self.p().tmp))
    def test_02_named_tempfile_create_read_write_cleanup(self):
        import tempfile
        p=self.p();data=b"ARTIFICIAL_PRIVATE_TEMP"
        with tempfile.NamedTemporaryFile(mode="w+b") as f:
            path=Path(f.name);self.assertEqual(path.parent,p.tmp)
            f.write(data);f.flush();p.note_file_io(path,"write",len(data))
            f.seek(0);received=f.read();p.note_file_io(path,"read",len(received));self.assertEqual(received,data)
        self.assertFalse(path.exists());self.assertTrue(p.created[str(path)]["deleted"])
    def test_03_mkstemp_real_FD_lifecycle_and_complete_log(self):
        import tempfile
        p=self.p();start=len(p.events);fd,name=tempfile.mkstemp()
        try:
            self.assertEqual(Path(name).parent,p.tmp);self.assertEqual(os.write(fd,b"fixture"),7)
            os.lseek(fd,0,os.SEEK_SET);self.assertEqual(os.read(fd,7),b"fixture")
        finally:
            os.close(fd);os.unlink(name)
        kinds={v["kind"] for v in p.events[start:]}
        self.assertTrue({"TEMP_OPEN_AUTHORIZED","TEMP_FD_OPEN_COMPLETED","TEMP_FD_WRITE_COMPLETED","TEMP_FD_READ_COMPLETED","TEMP_FD_CLOSE_COMPLETED","TEMP_CLEANUP_AUTHORIZED","TEMP_CLEANUP_COMPLETED"}<=kinds)
    def test_04_dill_import(self):
        import dill
        self.assertTrue(dill.__version__)
    def test_05_Qiskit_QSVC_imports(self):
        import qiskit
        from qiskit_machine_learning.algorithms import QSVC
        from qiskit_machine_learning.kernels import FidelityStatevectorKernel,FidelityQuantumKernel
        from qiskit.circuit.library import zz_feature_map
        self.assertTrue(qiskit.__version__);self.assertTrue(callable(QSVC));self.assertTrue(callable(FidelityStatevectorKernel));self.assertTrue(callable(FidelityQuantumKernel));self.assertTrue(callable(zz_feature_map))
    def test_06_system_tmp_write_denied(self):self.blocked("/tmp/recovery2_forbidden_"+self.p().run.name)
    def test_07_var_tmp_write_denied(self):self.blocked("/var/tmp/recovery2_forbidden_"+self.p().run.name)
    def test_08_other_device_write_denied(self):self.blocked("/dev/zero","r+b")
    def test_09_direct_null_write_denied(self):self.blocked("/dev/null","r+b")
    def test_10_symlink_inside_private_tmp_cannot_escape(self):self.blocked(self.p().tmp/"escape_link")
    def test_11_relative_path_escape_denied(self):self.blocked(self.p().tmp/"../../FORBIDDEN_ESCAPE")
    def test_12_old_artifact_overwrite_denied(self):self.blocked(scope.ROOT/"artifacts/phase4b1/20261030T032635Z/completion_manifest.json")
    def test_13_Dataset_write_denied(self):self.blocked(scope.ROOT/"artifacts/datasets/btcusdt_aggregate_v1_20261026T202040Z/RECOVERY2_FORBIDDEN")
    def test_14_Frozen_Subset_write_denied(self):self.blocked(scope.ROOT/"artifacts/phase4a0/20261029T222609Z/quantum_budget_subset_v1_manifest.json")
    def test_15_ML_venv_write_denied(self):self.blocked("/home/jason/.venvs/quantum-hft-ml/RECOVERY2_FORBIDDEN")
    def test_16_QML_venv_write_denied(self):self.blocked("/home/jason/.venvs/quantum-hft-qml/RECOVERY2_FORBIDDEN")
    def test_17_cleanup_outside_private_tmp_denied(self):
        with self.assertRaises(scope.ScopeViolation):os.unlink(scope.ROOT/"artifacts/phase4b1/20261030T032635Z/completion_manifest.json")
    def test_18_owned_temp_reopen_write_and_cleanup(self):
        import tempfile
        fd,name=tempfile.mkstemp();os.close(fd)
        try:
            with open(name,"w+b") as f:
                f.write(b"owned");f.flush();self.p().note_file_io(name,"write",5)
                f.seek(0);self.assertEqual(f.read(),b"owned");self.p().note_file_io(name,"read",5)
        finally:os.unlink(name)
        self.assertFalse(Path(name).exists())
    def test_19_import_failure_traceback_capture(self):
        log=io.StringIO();r=old_harness.discover(["tests.fixtures.phase4b1_recovery.import_error_fixture"],log)
        self.assertEqual(r["status"],"ERROR");self.assertIn("Traceback",log.getvalue());self.assertIn("ARTIFICIAL_DISCOVERY_RUNTIME_ERROR",log.getvalue())
    def test_20_formal_CSV_values_prohibited_in_unit_process(self):
        with self.assertRaises(scope.ScopeViolation):
            with open(scope.ROOT/"artifacts/datasets/btcusdt_aggregate_v1_20261026T202040Z/1000ms/train.csv") as f:f.read(1)

    def test_21_direct_directory_write_is_not_allowed(self):self.blocked(self.p().tmp,"w+b")
