import json
import tempfile
import unittest
from pathlib import Path

import coordination
import antigravity_adapter


class FakeProcess:
    returncode = 0
    def communicate(self, timeout):
        return json.dumps({'conversation_id': 'conv-1', 'status': 'SUCCESS', 'response': 'Antigravity acknowledged the task.', 'usage': {'total_tokens': 12}}), ''


class AntigravityAdapterTests(unittest.TestCase):
    def test_collect_persists_json_and_records_runtime_ack(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)
            task = coordination.create_task(state, producer='chuck', recipient='antigravity', title='Bounded task', brief='Acknowledge safely.', requested_action='Return acknowledgement.', evidence=[])
            coordination.claim_dispatch(state, task['id'], 'mission-1', 'antigravity')
            dispatched = coordination.mark_dispatched(state, task['id'])
            adapter = antigravity_adapter.AntigravityAdapter(state, process_factory=lambda _: FakeProcess())
            adapter.collect(dispatched, dispatched['dispatch'], {'process': FakeProcess()})
            updated = coordination.get_task(state, task['id'])
            self.assertEqual('acknowledged', updated['status'])
            evidence = json.loads(Path(updated['acknowledgement']['evidence_ref']).read_text())
            self.assertEqual('conv-1', evidence['conversation_id'])
            self.assertEqual('Antigravity acknowledged the task.', evidence['response'])


if __name__ == '__main__':
    unittest.main()
