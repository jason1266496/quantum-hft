"""Artificial fixtures only: end-to-end feature tool contract and failure evidence."""
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from decimal import Decimal
from tools import build_features as tool
from data_pipeline.adapters.csv_adapter import REQUIRED_COLUMNS
from data_pipeline.features.schema import fields

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "phase2c"

class BuildFeaturesTests(unittest.TestCase):
    def setUp(self):
        FIXTURES.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=FIXTURES, prefix="cli_artificial_")
        self.base = Path(self.tmp.name)
        self.project = self.base/"project"
        self.hft = self.base/"artificial_input"
        (self.project/"configs").mkdir(parents=True)
        (self.hft/"results").mkdir(parents=True)
        self.sid, self.rid = "replay_snapshot_1000", "replay_events_1000"
        self.snapshot = self.hft/"results"/(self.sid+".json")
        self.replay = self.hft/"results"/(self.rid+".jsonl")
        self.csv = self.hft/"results"/"artificial.csv"
        self.snapshot.write_text(json.dumps({"lastUpdateId":10,
            "bids":[[str(99-i),str(2+i)] for i in range(5)],
            "asks":[[str(101+i),str(3+i)] for i in range(5)]}))
        self.events = [
            {"eventTime":100,"firstUpdateId":11,"finalUpdateId":11,"bids":[{"price":99,"quantity":4}],"asks":[]},
            {"eventTime":101,"firstUpdateId":12,"finalUpdateId":12,"bids":[],"asks":[{"price":101,"quantity":7}]}]
        self.csv_rows = [
            ["900",100,20,"99","101","100","2","15","15","0"],
            ["901",101,21,"99","101","100","2","20","20","0"]]
        self.config = {"schema_version":"1.0","access_mode":"read_only",
            "hft_project":str(self.hft),"hft_results":str(self.hft/"results"),
            "allow_hft_write":False,"allow_network":False,"allow_real_trading":False,
            "allow_testnet_trading":False,"allow_cross_session_labels":False,
            "time_order_field":"event_time_ms","local_timestamp_policy":"not_receive_time_do_not_use_for_latency",
            "sources":[]}
        self.config_path=self.project/"configs/data_sources.json"
        self.flush()
        self.source_id="artificial"
        self.view="aggregate_core_v1"
        self.output=self.project/"artifacts/phase2c/20260101T000000Z/sources"/self.source_id

    def tearDown(self):
        self.tmp.cleanup()

    def flush(self):
        self.replay.write_text("".join(json.dumps(e)+"\n" for e in self.events))
        with self.csv.open("w",newline="") as f:
            writer=csv.writer(f,lineterminator="\n");writer.writerow(REQUIRED_COLUMNS);writer.writerows(self.csv_rows)
        self.config["sources"]=[
            {"source_id":sid,"relative_path":"results/"+p.name,"absolute_path":str(p),"file_type":kind,
             "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"size_bytes":p.stat().st_size,
             "audit_status":"PASS","session_id":"artificial_pair" if kind!="csv" else "artificial_csv",
             "event_time_start":None if kind=="snapshot" else 100,"event_time_end":None if kind=="snapshot" else 101,
             "allowed_uses":["artificial_feature_test"],"prohibited_uses":["source_write"],"known_limitations":["artificial_only"]}
            for sid,p,kind in ((self.sid,self.snapshot,"snapshot"),(self.rid,self.replay,"replay"),("artificial",self.csv,"csv"))]
        self.save_config()

    def save_config(self):
        self.config_path.write_text(json.dumps(self.config))

    def replay_mode(self,large=False):
        if large:
            self.sid,self.rid="replay_snapshot_50000","replay_events_50000"
            self.flush()
        self.source_id=self.rid
        self.view="both"
        self.output=self.output.parent/self.rid

    def run_source(self,**kwargs):
        params=dict(project_root=self.project,allowed_roots=(self.hft,),require_nine_sources=False,
                    compare_reference=True,repeat=2,progress_every=1,progress_stream=io.StringIO())
        params.update(kwargs)
        return tool.build_source(self.config_path,self.source_id,self.view,self.output,**params)

    def read(self,name):
        return json.loads((self.output/name).read_text())

    def rows(self,view="aggregate_core_v1"):
        with (self.output/(view+".csv")).open(newline="") as f:
            return list(csv.DictReader(f))

    def test_csv_complete_and_artifacts(self):
        result=self.run_source()
        self.assertEqual(result["status"],"PASS")
        self.assertEqual([a["output_record_count"] for a in result["attempts"]],[2,2])
        for name in ("source_manifest.json","feature_manifest.json","aggregate_core_v1.csv",
                     "feature_quality.json","feature_errors.csv","reference_comparison.json","determinism.json","stdout.txt","stderr.txt"):
            self.assertTrue((self.output/name).is_file(),name)
        self.assertFalse((self.output/"depth_top5_v1.csv").exists())
        self.assertEqual(self.read("reference_comparison.json")["status"],"NOT_AVAILABLE")

    def test_csv_recomputed_and_ids_direct_alias(self):
        self.run_source()
        row=self.rows()[0]
        self.assertEqual((row["mid_price"],row["spread"],row["spread_bps"],row["obi_5"]),("100","2","200","0"))
        self.assertEqual((row["first_update_id"],row["final_update_id"],row["local_update_id"]),("","","20"))

    def test_no_local_timestamp_label_target_or_extra_fields(self):
        self.run_source()
        header=tuple(self.rows()[0])
        self.assertEqual(header,fields("aggregate_core_v1"))
        self.assertFalse(any("local_timestamp" in f or "label" in f or "target" in f or "future" in f for f in header))

    def test_csv_depth_rejected_without_output(self):
        self.view="depth_top5_v1"
        with self.assertRaises(ValueError):self.run_source()
        self.assertFalse(self.output.exists())

    def test_existing_output_preserved(self):
        self.output.mkdir(parents=True)
        marker=self.output/"keep";marker.write_text("keep")
        with self.assertRaises(FileExistsError):self.run_source()
        self.assertEqual(list(self.output.iterdir()),[marker])

    def test_hft_output_rejected(self):
        self.output=self.hft/"results/output"
        with self.assertRaises(ValueError):self.run_source()
        self.assertFalse(self.output.exists())

    def test_symlink_output_rejected(self):
        (self.project/"artifacts").symlink_to(self.hft,target_is_directory=True)
        with self.assertRaises(ValueError):self.run_source()
        self.assertFalse((self.hft/"phase2c").exists())

    def test_source_hash_mismatch_fails_with_evidence(self):
        self.config["sources"][2]["sha256"]="0"*64;self.save_config()
        result=self.run_source()
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(result["attempts"],[])
        self.assertEqual(self.read("source_manifest.json")["status"],"FAIL")

    def test_cross_session_rejected(self):
        self.replay_mode()
        self.config["sources"][1]["session_id"]="different";self.save_config()
        with self.assertRaises(ValueError):self.run_source()
        self.assertFalse(self.output.exists())

    def test_source_merge_rejected(self):
        self.source_id="artificial,replay_events_1000"
        self.output=self.output.parent/self.source_id
        with self.assertRaises((ValueError,KeyError)):self.run_source()
        self.assertFalse(self.output.exists())

    def test_replay_post_event_no_snapshot_or_future(self):
        self.replay_mode()
        result=self.run_source()
        self.assertEqual(result["status"],"PASS")
        rows=self.rows("depth_top5_v1")
        self.assertEqual(len(rows),2)
        self.assertEqual((rows[0]["bid_quantity_1"],rows[0]["ask_quantity_1"]),("4","3"))
        self.assertEqual(rows[1]["ask_quantity_1"],"7")
        self.assertEqual(rows[0]["first_update_id"],"11")
        self.assertEqual(self.read("reference_comparison.json")["full_checks"],4)

    def test_50000_last_non_checkpoint_full_check(self):
        self.replay_mode(large=True)
        result=self.run_source()
        self.assertEqual(result["status"],"PASS")
        reference=self.read("reference_comparison.json")
        self.assertEqual(reference["light_checks"],4)
        self.assertEqual(reference["full_checks"],2)
        self.assertEqual(reference["checkpoints"],[{"repeat":1,"record_index":2},{"repeat":2,"record_index":2}])

    def test_50000_periodic_and_last_all_fields(self):
        self.events=[{"eventTime":i,"firstUpdateId":10+i,"finalUpdateId":10+i,"bids":[],"asks":[]} for i in range(1,1002)]
        self.replay_mode(large=True)
        self.run_source(repeat=1,progress_every=1000)
        ref=self.read("reference_comparison.json")
        self.assertEqual(ref["full_checks"],2)
        self.assertEqual(ref["light_checks"],1000)
        self.assertEqual([c["record_index"] for c in ref["checkpoints"]],[1000,1001])

    def test_reference_mismatch_fails_with_field_evidence(self):
        self.replay_mode()
        actual=tool.reference_features
        def wrong(*args):
            value=actual(*args);value["aggregate_core_v1"]["mid_price"]+=Decimal("1");return value
        with patch.object(tool,"reference_features",side_effect=wrong):
            result=self.run_source()
        self.assertEqual(result["status"],"FAIL")
        self.assertGreater(self.read("reference_comparison.json")["mismatch_count"],0)
        self.assertIn("FEATURE_REFERENCE_MISMATCH",(self.output/"feature_errors.csv").read_text())
        self.assertIn("mid_price",(self.output/"feature_errors.csv").read_text())

    def test_invalid_zero_denominator_retained(self):
        self.csv_rows[0][7:10]=["0","0","0"];self.flush()
        self.run_source(repeat=1)
        rows=self.rows()
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["valid_feature_row"],"false")
        self.assertIn("ZERO_DEPTH_DENOMINATOR",rows[0]["invalid_reason"])
        self.assertEqual(rows[0]["obi_5"],"")

    def test_insufficient_depth_retained_in_both_views(self):
        self.events[0]["bids"]=[{"price":95,"quantity":0}];self.flush();self.replay_mode()
        result=self.run_source(repeat=1)
        self.assertEqual(result["status"],"PASS")
        for view in tool.VIEWS:
            rows=self.rows(view)
            self.assertEqual(len(rows),2)
            self.assertTrue(all(r["valid_feature_row"]=="false" for r in rows))
            self.assertIn("INSUFFICIENT_TOP5_DEPTH",rows[0]["invalid_reason"])

    def test_csv_source_tolerance_boundary_passes(self):
        self.csv_rows[0][5]="100.00000001";self.flush()
        self.assertEqual(self.run_source()["status"],"PASS")
        q=self.read("feature_quality.json")["attempts"][0]["aggregate_core_v1"]
        self.assertEqual(q["source_value_mismatch_count"],0)
        self.assertEqual(self.rows()[0]["mid_price"],"100")

    def test_csv_source_beyond_tolerance_fails_and_retains(self):
        self.csv_rows[0][5]="100.00000002";self.flush()
        result=self.run_source()
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(len(self.rows()),2)
        self.assertEqual(self.rows()[0]["valid_feature_row"],"false")
        self.assertEqual(result["attempts"][0]["quality"]["aggregate_core_v1"]["source_value_mismatch_count"],1)

    def test_parse_error_fails_with_preserved_prefix(self):
        self.csv_rows[1][0]="broken";self.flush()
        result=self.run_source()
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(result["attempts"][0]["parse_errors"],1)
        self.assertEqual(len(self.rows()),1)
        self.assertIn("DataFormatError",(self.output/"stderr.txt").read_text())

    def test_repeat_sha_and_quality_equal(self):
        result=self.run_source()
        self.assertEqual(self.read("determinism.json")["status"],"PASS")
        first,second=result["attempts"]
        self.assertEqual(first["quality"],second["quality"])
        self.assertEqual(first["views"]["aggregate_core_v1"]["sha256"],second["views"]["aggregate_core_v1"]["sha256"])

    def test_progress_does_not_change_output(self):
        a=self.run_source(repeat=1,progress_every=1)
        self.output=self.project/"artifacts/phase2c/20260101T000001Z/sources"/self.source_id
        b=self.run_source(repeat=1,progress_every=1000)
        self.assertEqual(a["attempts"][0]["views"]["aggregate_core_v1"]["sha256"],b["attempts"][0]["views"]["aggregate_core_v1"]["sha256"])
        self.assertEqual(a["attempts"][0]["quality"],b["attempts"][0]["quality"])

    def test_input_contents_and_metadata_unchanged(self):
        def state():
            return {p.name:(p.read_bytes(),p.stat().st_mtime_ns,p.stat().st_ctime_ns) for p in (self.snapshot,self.replay,self.csv)}
        before=state();self.run_source();self.assertEqual(before,state())

    def test_duplicate_time_invalid_retained(self):
        self.csv_rows[1][1]=100;self.flush();self.run_source()
        self.assertEqual(len(self.rows()),2)
        self.assertEqual(self.rows()[1]["valid_feature_row"],"false")
        self.assertEqual(self.read("feature_quality.json")["attempts"][0]["aggregate_core_v1"]["duplicate_event_time"],1)

    def test_external_root_rejected_before_any_mkdir(self):
        with patch.object(Path,"mkdir",side_effect=AssertionError("mkdir must not occur")):
            with self.assertRaisesRegex(ValueError,"project root must remain"):
                tool.build_source(self.config_path,self.source_id,self.view,
                    "/home/jason/artifacts/phase2c/20260101T000000Z/sources/artificial",
                    project_root="/home/jason",allowed_roots=(self.hft,),require_nine_sources=False)

    def test_all_skipped_cannot_claim_reference_pass(self):
        self.events=[{"eventTime":100,"firstUpdateId":8,"finalUpdateId":9,"bids":[],"asks":[]}]
        self.flush();self.replay_mode()
        result=self.run_source()
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(self.read("reference_comparison.json")["status"],"FAIL")
        self.assertEqual(self.read("reference_comparison.json")["full_checks"],0)

    def test_invalid_repeat_and_progress_rejected(self):
        for params in ({"repeat":0},{"progress_every":0},{"repeat":True}):
            with self.subTest(params=params),self.assertRaises(ValueError):self.run_source(**params)
        self.assertFalse(self.output.exists())

if __name__=="__main__":
    unittest.main()

