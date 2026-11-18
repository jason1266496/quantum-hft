import unittest
from unittest.mock import patch
from experiments.quantum_preparation.environment import inspect_dependencies,circuit_design
from experiments.quantum_preparation.runner import execute,research_policy
from experiments.quantum_preparation.io import write,read
from tests.fixtures.phase4a0.helpers import run_tree
class ToolTests(unittest.TestCase):
    def test_missing_dependency_report_without_install(self):
        import importlib.metadata as md
        with patch("experiments.quantum_preparation.environment.metadata.metadata",side_effect=md.PackageNotFoundError("fixture")),patch("experiments.quantum_preparation.environment.importlib.import_module",side_effect=ModuleNotFoundError("fixture")):
            d,loaded=inspect_dependencies()
        self.assertEqual(d["status"],"DEPENDENCY_MISSING");self.assertEqual(d["execution_environment_status"],"DEPENDENCY_BLOCKED");self.assertFalse(d["packages_changed"]);self.assertFalse(d["remediation"]["candidate_venv_created"])
    def test_versions_do_not_prove_imports(self):
        class Meta:
            def get(self,*a):return ">=3.8"
            def get_all(self,*a):return []
        with patch("experiments.quantum_preparation.environment.metadata.metadata",return_value=Meta()),patch("experiments.quantum_preparation.environment.metadata.version",return_value="fixture"),patch("experiments.quantum_preparation.environment.importlib.import_module",side_effect=ImportError("incompatible fixture")):
            d,_=inspect_dependencies()
        self.assertEqual(d["status"],"INCOMPATIBLE_ENVIRONMENT");self.assertFalse(d["quantum_runtime_ready"])
    def test_missing_sdk_metrics_not_fabricated(self):
        d=circuit_design({"failed_imports":["missing"],"packages":{}},{})
        self.assertEqual(d["SDK_observed_gate_count"],"NOT_AVAILABLE");self.assertFalse(d["SDK_circuit_constructed"]);self.assertEqual(d["kernel_evaluations"],0)
    def test_reference_circuit_schedule_arithmetic(self):
        d=circuit_design({"failed_imports":["missing"],"packages":{}},{})["analytical_reference"]
        self.assertEqual(len(d["schedule"]),11);self.assertEqual(sum(len(x) for x in d["schedule"]),17);self.assertTrue(d["not_SDK_measured"])
    def test_policy_no_training_or_test(self):
        p=research_policy();self.assertFalse(p["model_fitting_allowed"]);self.assertFalse(p["formal_kernel_computation_allowed"]);self.assertFalse(p["Phase4A1_started"])
    def test_cli_execution_logs_fixture_only(self):
        r=run_tree()
        def fake(run):write(run/"summary/fake.json",{"synthetic":True});return {}
        with patch("experiments.quantum_preparation.runner.prepare",side_effect=fake):self.assertEqual(execute(r),0)
        self.assertEqual(read(r/"logs/execution.json")["exit_code"],0)
