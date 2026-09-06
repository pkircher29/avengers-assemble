import tempfile
import unittest
from pathlib import Path

import coordination


class CoordinationLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_task_acknowledgement_and_handoff_preserve_evidence(self):
        task = coordination.create_task(
            self.state, producer='chuck', recipient='codex',
            title='Inspect one Python module', brief='Read coordination.py and report one factual observation.',
            requested_action='Return a cited observation.', evidence=['C:/project/coordination.py'],
        )
        acknowledged = coordination.acknowledge_task(self.state, task['id'], 'codex', 'I own this bounded inspection.')
        handoff = coordination.submit_handoff(
            self.state, task['id'], producer='codex', recipient='chuck',
            claim='The module persists task records atomically.', confidence='high',
            sources=['C:/project/coordination.py'], requested_action='Review the observation.',
        )
        self.assertEqual('acknowledged', acknowledged['status'])
        self.assertEqual('handoff-submitted', coordination.get_task(self.state, task['id'])['status'])
        self.assertEqual('codex', handoff['producer'])
        self.assertEqual('chuck', handoff['recipient'])
        self.assertEqual(['C:/project/coordination.py'], handoff['sources'])

    def test_acknowledgement_rejects_wrong_recipient_and_duplicate(self):
        task = coordination.create_task(
            self.state, producer='chuck', recipient='antigravity', title='Bounded task',
            brief='Do one safe thing.', requested_action='Report result.', evidence=[],
        )
        with self.assertRaisesRegex(ValueError, 'only the recipient'):
            coordination.acknowledge_task(self.state, task['id'], 'codex', 'wrong worker')
        coordination.acknowledge_task(self.state, task['id'], 'antigravity', 'accepted')
        with self.assertRaisesRegex(ValueError, 'already acknowledged'):
            coordination.acknowledge_task(self.state, task['id'], 'antigravity', 'again')

    def test_handoff_rejects_unknown_task_and_wrong_producer(self):
        with self.assertRaisesRegex(ValueError, 'unknown task'):
            coordination.submit_handoff(self.state, 'missing', 'codex', 'chuck', 'claim', 'low', [], 'review')
        task = coordination.create_task(
            self.state, producer='chuck', recipient='codex', title='Bounded task',
            brief='Do one safe thing.', requested_action='Report result.', evidence=[],
        )
        with self.assertRaisesRegex(ValueError, 'only the assigned recipient'):
            coordination.submit_handoff(self.state, task['id'], 'antigravity', 'chuck', 'claim', 'low', [], 'review')


if __name__ == '__main__':
    unittest.main()
