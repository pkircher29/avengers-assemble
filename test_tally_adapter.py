import json
import tempfile
import unittest
from pathlib import Path

import coordination
import tally_adapter


class FakeProcess:
    def communicate(self, timeout):
        result = {'meta': {'agentMeta': {'sessionId': 'session-1', 'provider': 'tally-granite', 'model': 'granite4.2:8b'}}, 'finalAssistantVisibleText': 'TALLY_HANDOFF_OK'}
        return json.dumps(result), ''


class TallyAdapterTests(unittest.TestCase):
    def test_collect_persists_openclaw_result_then_records_runtime_ack(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)
            task = coordination.create_task(state, producer='chuck', recipient='tally', title='Bounded task', brief='Reply safely.', requested_action='Return handoff.', evidence=[])
            coordination.claim_dispatch(state, task['id'], 'mission-1', 'tally')
            dispatched = coordination.mark_dispatched(state, task['id'])
            adapter = tally_adapter.TallyAdapter(state, process_factory=lambda command: FakeProcess())
            adapter.collect(dispatched, dispatched['dispatch'], {'process': FakeProcess()})
            updated = coordination.get_task(state, task['id'])
            self.assertEqual('acknowledged', updated['status'])
            self.assertEqual('runtime', updated['acknowledgement']['origin'])
            evidence = Path(updated['acknowledgement']['evidence_ref'])
            self.assertTrue(evidence.exists())
            self.assertEqual('TALLY_HANDOFF_OK', json.loads(evidence.read_text())['finalAssistantVisibleText'])


if __name__ == '__main__':
    unittest.main()
