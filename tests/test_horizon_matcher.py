import unittest
from data_pipeline.labels.matcher import first_target,segments
from tests.fixtures.phase2d.helpers import rows

class HorizonMatcherTests(unittest.TestCase):
    def check_exact(self,horizon,index):
        data=rows()
        self.assertEqual(first_target(data,[r.event_time_ms for r in data],0,horizon,len(data)),index)
    def test_exact_100(self): self.check_exact(100,1)
    def test_exact_200(self): self.check_exact(200,2)
    def test_exact_500(self): self.check_exact(500,3)
    def test_exact_1000(self): self.check_exact(1000,4)
    def test_101_for_requested_100(self):
        data=rows((0,101))
        self.assertEqual(first_target(data,[r.event_time_ms for r in data],0,100,2),1)
    def test_first_at_or_after_target_with_duplicates(self):
        data=rows((0,0,100,100,101))
        self.assertEqual(first_target(data,[r.event_time_ms for r in data],0,100,5),2)
    def test_session_tail(self):
        data=rows((0,99))
        self.assertIsNone(first_target(data,[r.event_time_ms for r in data],0,100,2))
    def test_no_cross_session(self):
        data=rows((0,50),session="a")+rows((100,200),session="b")
        self.assertEqual(list(segments(data))[0][0:2],(0,2))
        self.assertIsNone(first_target(data,[r.event_time_ms for r in data],0,100,2))
    def test_no_cross_source(self):
        data=rows((0,50),source="a")+rows((100,200),source="b")
        self.assertEqual(list(segments(data))[0][0:2],(0,2))
    def test_backward_boundary(self):
        data=rows((0,100,50,150))
        self.assertEqual(list(segments(data)),[(0,2,True),(2,4,False)])
    def test_no_unsupported_horizon(self):
        data=rows((0,250))
        with self.assertRaises(ValueError):
            first_target(data,[r.event_time_ms for r in data],0,250,2)
