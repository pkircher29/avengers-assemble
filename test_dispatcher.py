import tempfile
import unittest
from pathlib import Path

import coordination
import dispatcher
import mission


PARTICIPANTS = [{'name': 'Chuck', 'role': 'coordinator', 'requested_model': 'current', 'requested_effort': 'high'}]
LIMITS = {'max_rounds': 2, 'max_turns_per_worker': 4, 'max_budget_usd': 3.0}


class FakeAdapter:
    runtime = 'fake-runtime'

    def __init__(self, state):
        self.state = state
        self.calls = []

    def launch(self, task, dispatch):
        self.calls.append((task['id'], dispatch['run_id']))
        return {'pid': 1234}


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name) / 'state'
        self.mission_path = self.state / 'mission.json'
        self.active = mission.start(self.mission_path, 'Verify dispatch', ['explicit dispatch only'], PARTICIPANTS, LIMITS)
        self.task = coordination.create_task(self.state, producer='chuck', recipient='claude', title='Bounded task', brief='Reply with a fact.', requested_action='Return a handoff.', evidence=[])
        self.adapter = FakeAdapter(self.state)

    def tearDown(self):
        self.temp.cleanup()

    def test_dispatch_claims_before_adapter_launch_and_consumes_round(self):
        dispatched = dispatcher.dispatch_task(self.state, self.mission_path, self.task['id'], self.active['id'], self.adapter)
        self.assertEqual('dispatched', dispatched['status'])
        self.assertEqual(self.task['id'], dispatched['dispatch']['run_id'])
        self.assertEqual([(self.task['id'], self.task['id'])], self.adapter.calls)
        self.assertEqual(1, mission.load(self.mission_path)['rounds'])

    def test_pause_or_duplicate_dispatch_never_launches(self):
        mission.transition(self.mission_path, 'pause')
        with self.assertRaisesRegex(ValueError, 'active'):
            dispatcher.dispatch_task(self.state, self.mission_path, self.task['id'], self.active['id'], self.adapter)
        self.assertEqual([], self.adapter.calls)
        mission.transition(self.mission_path, 'resume')
        dispatcher.dispatch_task(self.state, self.mission_path, self.task['id'], self.active['id'], self.adapter)
        with self.assertRaisesRegex(ValueError, 'already claimed'):
            dispatcher.dispatch_task(self.state, self.mission_path, self.task['id'], self.active['id'], self.adapter)
        self.assertEqual(1, len(self.adapter.calls))

    def test_wrong_mission_never_claims_or_launches(self):
        with self.assertRaisesRegex(ValueError, 'mission id'):
            dispatcher.dispatch_task(self.state, self.mission_path, self.task['id'], 'stale', self.adapter)
        self.assertIsNone(coordination.get_task(self.state, self.task['id']).get('dispatch'))
        self.assertEqual([], self.adapter.calls)


if __name__ == '__main__':
    unittest.main()
