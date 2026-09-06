import io
import json
import tempfile
import unittest
from pathlib import Path

import coordination
import codex_adapter


class FakeProcess:
    returncode = 0

    def communicate(self, timeout):
        rows = [
            {'type': 'thread.started', 'thread_id': 'thread-1'},
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'id': 'm1', 'text': 'Codex acknowledged the bounded task.'}},
            {'type': 'turn.completed', 'usage': {'input_tokens': 10, 'cached_input_tokens': 2, 'cache_write_input_tokens': 0, 'output_tokens': 8, 'reasoning_output_tokens': 1}},
        ]
        return '\n'.join(json.dumps(row) for row in rows), ''


class CodexAdapterTests(unittest.TestCase):
    def test_collect_captures_final_message_usage_and_runtime_ack(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)
            task = coordination.create_task(state, producer='chuck', recipient='codex', title='Bounded task', brief='Acknowledge safely.', requested_action='Return acknowledgement.', evidence=[])
            coordination.claim_dispatch(state, task['id'], 'mission-1', 'codex')
            dispatched = coordination.mark_dispatched(state, task['id'])
            adapter = codex_adapter.CodexAdapter(state, process_factory=lambda _: FakeProcess())
            adapter.collect(dispatched, dispatched['dispatch'], {'process': FakeProcess()})
            updated = coordination.get_task(state, task['id'])
            self.assertEqual('acknowledged', updated['status'])
            evidence = json.loads(Path(updated['acknowledgement']['evidence_ref']).read_text())
            self.assertEqual('thread-1', evidence['thread_id'])
            self.assertEqual('Codex acknowledged the bounded task.', evidence['final_text'])
            self.assertEqual(8, evidence['usage']['output_tokens'])


if __name__ == '__main__':
    unittest.main()
