import tempfile
import unittest
from pathlib import Path

import coordination


class RuntimeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name)
        self.task = coordination.create_task(self.state, producer='chuck', recipient='tally', title='Bounded task', brief='Answer safely.', requested_action='Return handoff.', evidence=[])
        self.run_id = self.task['id']

    def tearDown(self):
        self.temp.cleanup()

    def test_runtime_ack_requires_matching_dispatched_run(self):
        with self.assertRaisesRegex(ValueError, 'dispatched'):
            coordination.record_runtime_ack(self.state, self.task['id'], self.run_id, 'tally', 'accepted', 'runtime://tally/1')
        coordination.claim_dispatch(self.state, self.task['id'], 'mission-1', 'tally')
        coordination.mark_dispatched(self.state, self.task['id'])
        acknowledged = coordination.record_runtime_ack(self.state, self.task['id'], self.run_id, 'tally', 'accepted', 'runtime://tally/1')
        self.assertEqual('acknowledged', acknowledged['status'])
        self.assertEqual('runtime', acknowledged['acknowledgement']['origin'])

    def test_runtime_ack_rejects_wrong_run_and_duplicate(self):
        coordination.claim_dispatch(self.state, self.task['id'], 'mission-1', 'tally')
        coordination.mark_dispatched(self.state, self.task['id'])
        with self.assertRaisesRegex(ValueError, 'run id'):
            coordination.record_runtime_ack(self.state, self.task['id'], 'wrong', 'tally', 'accepted', 'runtime://tally/1')
        coordination.record_runtime_ack(self.state, self.task['id'], self.run_id, 'tally', 'accepted', 'runtime://tally/1')
        with self.assertRaisesRegex(ValueError, 'already acknowledged'):
            coordination.record_runtime_ack(self.state, self.task['id'], self.run_id, 'tally', 'again', 'runtime://tally/2')


if __name__ == '__main__':
    unittest.main()
