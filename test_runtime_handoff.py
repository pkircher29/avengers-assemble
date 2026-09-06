import tempfile, unittest
from pathlib import Path
import coordination

class RuntimeHandoffTests(unittest.TestCase):
 def test_runtime_handoff_requires_matching_acknowledged_run(self):
  with tempfile.TemporaryDirectory() as temp:
   state=Path(temp); task=coordination.create_task(state,producer='chuck',recipient='codex',title='T',brief='B',requested_action='A',evidence=[])
   coordination.claim_dispatch(state,task['id'],'m','codex'); coordination.mark_dispatched(state,task['id'])
   with self.assertRaisesRegex(ValueError,'acknowledged'):
    coordination.record_runtime_handoff(state,task['id'],task['id'],'codex','claim','high',[],'review','evidence://x')
   coordination.record_runtime_ack(state,task['id'],task['id'],'codex','ack','evidence://a')
   handoff=coordination.record_runtime_handoff(state,task['id'],task['id'],'codex','claim','high',[],'review','evidence://x')
   self.assertEqual('runtime',handoff['origin'])
   self.assertEqual('needs-review',handoff['review_status'])

if __name__=='__main__': unittest.main()
