import tempfile, unittest
from pathlib import Path
import coordination

class ReviewTests(unittest.TestCase):
 def test_handoff_can_be_quarantined_and_released_with_rationale(self):
  with tempfile.TemporaryDirectory() as temp:
   state=Path(temp); task=coordination.create_task(state,producer='chuck',recipient='codex',title='T',brief='B',requested_action='A',evidence=[])
   coordination.claim_dispatch(state,task['id'],'m','codex'); coordination.mark_dispatched(state,task['id']); coordination.record_runtime_ack(state,task['id'],task['id'],'codex','ack','e://a')
   handoff=coordination.record_runtime_handoff(state,task['id'],task['id'],'codex','claim','high',[],'review','e://h')
   q=coordination.review_handoff(state,handoff['id'],'quarantined','Missing source verification.')
   self.assertEqual('quarantined',q['review_status'])
   r=coordination.review_handoff(state,handoff['id'],'released','Paul reviewed the source.')
   self.assertEqual('released',r['review_status'])

if __name__=='__main__': unittest.main()
