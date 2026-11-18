import unittest
from data_pipeline.splits.policy import whole_session_plan,depth_plan,time_boundaries,locate
from data_pipeline.splits.splitter import build_membership
from tests.fixtures.phase2e.helpers import sources,source,pipeline
class TimeSplitterTests(unittest.TestCase):
    def test_aggregate_complete_session(self):
        data=sources();plan=whole_session_plan(data)
        for s in data:
            if s.source_id=="replay_events_1000":continue
            self.assertEqual(len({locate(r,plan) for r in s.rows}),1)
    def test_time_order(self):
        data,plan,policy,m,*_=pipeline("aggregate_core_v1")
        times={s:[r[4] for r in m["raw"] if r[6]==s] for s in plan["assignments"]}
        ordered=list(times)
        for a,b in zip(ordered,ordered[1:]):self.assertLess(max(times[a]),min(times[b]))
    def test_depth_initial_time_ratio(self):
        data,plan,p,m,*_=pipeline()
        counts={s:sum(r[6]==s for r in m["raw"]) for s in plan["assignments"]}
        self.assertEqual(list(counts.values()),[300,100,50,50])
    def test_not_blind_row_cut(self):
        s=source("replay_events_50000",view="depth_top5_v1",times=list(range(400))+list(range(10000,20000,100)))
        p=depth_plan(s)
        self.assertNotEqual(sum(r.event_time_ms<p["boundaries"][0] for r in s.rows),len(s.rows)*60//100)
    def test_replay1000_smoke_only(self):
        data,plan,p,m,*_=pipeline()
        self.assertFalse(any(r[1]=="replay_events_1000" for r in m["raw"]))
    def test_shuffle_rejected(self):
        with self.assertRaises(ValueError):time_boundaries([0,100,50,200])
    def test_boundary_groups_duplicate_timestamps(self):
        _,cuts=time_boundaries([0,10,20,30,40,50,60,60,70,80,90,100])
        self.assertEqual(cuts,[60,80,90])
