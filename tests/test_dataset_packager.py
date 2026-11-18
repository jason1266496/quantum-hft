import contextlib,csv,json,unittest
from io import StringIO
from data_pipeline.datasets.packager import package_family,SampleRegistry,return_statistics
from data_pipeline.datasets.checksums import fingerprint
from decimal import Decimal
from tests.fixtures.phase2f.helpers import fixture,RUN
class DatasetPackagerTests(unittest.TestCase):
    def setUp(self):
        cm=fixture();self.base,self.ctx=cm.__enter__();self.addCleanup(cm.__exit__,None,None,None)
    def package(self,line="aggregate",name="dataset"):
        with contextlib.redirect_stdout(StringIO()):
            self.result=package_family(self.ctx,line,RUN,self.base/name,"synthetic-v1")
        return self.base/name
    def rows(self,root,h,split):
        with (root/f"{h}ms"/(split+".csv")).open(newline="") as f:return list(csv.DictReader(f))
    def test_train_packaging(self):self.assertEqual(len(self.rows(self.package(),100,"train")),31)
    def test_validation_packaging(self):self.assertEqual(len(self.rows(self.package(),100,"validation")),15)
    def test_test_packaging(self):self.assertEqual(len(self.rows(self.package(),100,"test")),15)
    def test_holdout_packaging(self):self.assertEqual(len(self.rows(self.package(),100,"final_holdout")),15)
    def test_all_horizons_and_different_membership(self):
        root=self.package()
        self.assertEqual([len(self.rows(root,h,"train")) for h in (100,200,500,1000)],[31,30,27,22])
    def test_same_event_same_id_across_horizon(self):
        root=self.package();self.assertEqual(self.rows(root,100,"train")[0]["sample_id"],self.rows(root,200,"train")[0]["sample_id"])
    def test_tail_not_packaged(self):
        root=self.package()
        self.assertTrue(all(int(x["record_index"])<=70 for x in self.rows(root,1000,"final_holdout")))
    def test_match_error_rejected(self):
        p=self.ctx["label_root"]/"sources/artificial_aggregate/aggregate_core_v1/labels_100ms.csv"
        with p.open(newline="") as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
        rows[0]["match_error_ms"]="2"
        with p.open("w",newline="") as f:writer=csv.DictWriter(f,fields,lineterminator="\n");writer.writeheader();writer.writerows(rows)
        with self.assertRaisesRegex(ValueError,"MATCH_ERROR_REJECTED"):self.package()
    def test_purged_row_rejected(self):
        p=self.ctx["split_root"]/"aggregate/train_indices.csv"
        with p.open(newline="") as f:fields=csv.DictReader(f).fieldnames
        row={"feature_view":"aggregate_core_v1","source_id":"artificial_aggregate","session_id":"session_artificial_aggregate",
             "record_index":"32","event_time_ms":"3100","event_identity":"3100:32","requested_horizon_ms":"100",
             "target_event_time_ms":"3200","split":"Train"}
        with p.open("a",newline="") as f:csv.DictWriter(f,fields,lineterminator="\n").writerow(row)
        with self.assertRaisesRegex(ValueError,"PURGED_ROW"):self.package()
    def test_invalid_label_rejected(self):
        p=self.ctx["label_root"]/"sources/artificial_aggregate/aggregate_core_v1/labels_100ms.csv"
        with p.open(newline="") as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
        rows[0]["valid_label"]="false";rows[0]["invalid_reason"]="INVALID_CURRENT_PRICE"
        with p.open("w",newline="") as f:writer=csv.DictWriter(f,fields,lineterminator="\n");writer.writeheader();writer.writerows(rows)
        with self.assertRaises(ValueError):self.package()
    def test_feature_schema_byte_archive(self):
        root=self.package();self.assertEqual(fingerprint(root/"feature_schema.json"),fingerprint(self.ctx["feature_root"]/"schemas/aggregate_core_v1.schema.json"))
    def test_label_schema_byte_archive(self):
        root=self.package();self.assertEqual(fingerprint(root/"label_schema.json"),fingerprint(self.ctx["label_root"]/"schemas/label.schema.json"))
    def test_holdout_no_return_statistics(self):
        q=json.loads((self.package()/"quality_report.json").read_text())
        stat=q["per_horizon"]["100"]["Final Holdout"]["continuous_return_bps"]
        self.assertEqual(stat,{"status":"NOT_COMPUTED_HOLDOUT_LOCKED","count":15})
    def test_no_output_overwrite(self):
        self.package()
        with self.assertRaises(FileExistsError):self.package()
    def test_duplicate_id_rejected(self):
        registry=SampleRegistry();registry.observe("id",b"a","Train",100)
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):registry.observe("id",b"a","Train",100)
    def test_collision_rejected(self):
        registry=SampleRegistry();registry.observe("id",b"a","Train",100)
        with self.assertRaisesRegex(ValueError,"COLLISION"):registry.observe("id",b"b","Train",200)
    def test_split_overlap_rejected(self):
        registry=SampleRegistry();registry.observe("id",b"a","Train",100)
        with self.assertRaisesRegex(ValueError,"OVERLAP"):registry.observe("id",b"a","Test",200)
    def test_return_statistics_include_zero(self):
        self.assertEqual(return_statistics([Decimal("-1"),Decimal("0"),Decimal("1")])["median"],"0")
