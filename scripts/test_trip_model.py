#!/usr/bin/env python3
"""Synthetic regression cases; no network, accounts, or production writes."""
import copy,unittest
from trip_model import ROOT,load,validate,request_scope,public_data
from build_mobile_html import build
class Tests(unittest.TestCase):
 def setUp(self):self.d=load(ROOT/'assets/example-trip.json')
 def test_valid_with_honest_warnings(self):
  r=validate(self.d);self.assertFalse(r['errors']);self.assertTrue(r['warnings'])
 def test_booking_date_locked(self):
  self.d['days'][1]['date']='2026-11-05';self.assertTrue(any('预订日期' in x for x in validate(self.d)['errors']))
 def test_duplicate_cost(self):
  c=copy.deepcopy(self.d['costs'][0]);c['id']='another';self.d['costs'].append(c);self.assertIn('同一预订重复计费',validate(self.d)['errors'])
 def test_transfer(self):
  s=copy.deepcopy(self.d['days'][0]['stops'][0]);s.update(id='second',start='2026-11-02T11:10:00+08:00',end='2026-11-02T12:00:00+08:00',transfer_minutes=30);self.d['days'][0]['stops'].append(s);self.assertTrue(any('转场时间不足' in x for x in validate(self.d)['errors']))
 def test_overnight(self):
  s=self.d['days'][0]['stops'][0];s.update(start='2026-11-02T23:00:00+08:00',end='2026-11-03T01:00:00+08:00');self.assertFalse(validate(self.d)['errors'])
 def test_request_scope_and_stale(self):
  r={'trip_id':self.d['trip_id'],'base_revision':1,'operations':[{'day_id':'day1','type':'remove','stop_id':'walk'}]};self.assertEqual(request_scope(self.d,r)['affected_days'],['day1']);r['base_revision']=0
  with self.assertRaises(ValueError):request_scope(self.d,r)
 def test_locked_request(self):
  with self.assertRaises(ValueError):request_scope(self.d,{'trip_id':self.d['trip_id'],'base_revision':1,'operations':[{'day_id':'day2','type':'remove','stop_id':'shop'}]})
 def test_semantic_scope(self):
  r=request_scope(self.d,{'trip_id':self.d['trip_id'],'base_revision':1,'operations':[{'day_id':'day1','type':'note','text':'改城市'}]});self.assertTrue(r['needs_semantic_review'])
 def test_private_projection_and_escape(self):
  self.d['raw_order']='SECRET-MARKER';self.d['bookings'][0]['order_number']='PRIVATE-MARKER';self.d['title']='</script><script>alert(1)</script>'
  s=build(self.d);self.assertNotIn('SECRET-MARKER',s);self.assertNotIn('PRIVATE-MARKER',s);self.assertNotIn('<script>alert(1)</script>',s)
 def test_invalid_url(self):
  self.d['places'][0]['map_url']='javascript:alert(1)';self.assertTrue(validate(self.d)['errors'])
 def test_identity_dedup(self):
  self.d['places'].append(copy.deepcopy(self.d['places'][0]));self.assertTrue(validate(self.d)['errors'])
if __name__=='__main__':unittest.main()
