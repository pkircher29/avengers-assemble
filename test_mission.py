import tempfile
import unittest
from pathlib import Path

import mission


PARTICIPANTS = [
    {'name': 'Chuck', 'role': 'coordinator', 'requested_model': 'current', 'requested_effort': 'high'},
    {'name': 'Claude', 'role': 'worker', 'requested_model': 'sonnet', 'requested_effort': 'medium'},
]
LIMITS = {'max_rounds': 2, 'max_turns_per_worker': 8, 'max_budget_usd': 1.0}


class MissionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'mission.json'

    def tearDown(self):
        self.temp.cleanup()

    def start(self):
        return mission.start(self.path, 'Build a truthful local console', ['state is durable'], PARTICIPANTS, LIMITS)

    def test_start_persists_valid_active_mission(self):
        created = self.start()
        loaded = mission.load(self.path)
        self.assertEqual(created, loaded)
        self.assertEqual('active', loaded['state'])
        self.assertEqual(0, loaded['rounds'])

    def test_cannot_replace_active_mission(self):
        self.start()
        with self.assertRaisesRegex(ValueError, 'cannot replace an active mission'):
            self.start()

    def test_pause_resume_clear_lifecycle(self):
        self.start()
        self.assertEqual('paused', mission.transition(self.path, 'pause')['state'])
        self.assertEqual('active', mission.transition(self.path, 'resume')['state'])
        mission.transition(self.path, 'pause')
        self.assertEqual('cleared', mission.transition(self.path, 'clear')['state'])

    def test_invalid_transitions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no mission exists'):
            mission.transition(self.path, 'pause')
        self.start()
        with self.assertRaisesRegex(ValueError, 'only a paused mission can be resumed'):
            mission.transition(self.path, 'resume')
        with self.assertRaisesRegex(ValueError, 'pause the active mission'):
            mission.transition(self.path, 'clear')

    def test_rounds_require_active_mission_and_respect_limit(self):
        self.start()
        self.assertEqual(1, mission.add_round(self.path)['rounds'])
        self.assertEqual(2, mission.add_round(self.path)['rounds'])
        with self.assertRaisesRegex(ValueError, 'maximum rounds'):
            mission.add_round(self.path)
        mission.transition(self.path, 'pause')
        with self.assertRaisesRegex(ValueError, 'only an active mission'):
            mission.add_round(self.path)

    def test_rejects_invalid_mission_shape(self):
        with self.assertRaisesRegex(ValueError, 'mission must be an object'):
            mission.validate([])
        bad = {'id': 'x'}
        with self.assertRaisesRegex(ValueError, 'missing mission field'):
            mission.validate(bad)


if __name__ == '__main__':
    unittest.main()
