import tempfile
import unittest
from pathlib import Path

import coordination
import dispatcher
import mission


PARTICIPANTS = [{'name': 'Chuck', 'role': 'coordinator', 'requested_model': 'current', 'requested_effort': 'high'}]
LIMITS = {'max_rounds': 2, 'max_turns_per_worker': 4, 'max_budget_usd': 3.0}


class SequencedAdapter:
    runtime = 'tally'

    def __init__(self, state):
        self.state = state
        self.observed = []

    def launch(self, task, dispatch):
        self.observed.append(('launch', coordination.get_task(self.state, task['id'])['status']))
        return {'handle': 'h1'}

    def collect(self, task, dispatch, handle):
        self.observed.append(('collect', coordination.get_task(self.state, task['id'])['status']))
        return {'handle': handle}


class AdapterSequenceTests(unittest.TestCase):
    def test_dispatch_marks_launched_before_collecting_runtime_output(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / 'state'; mission_path = state / 'mission.json'
            active = mission.start(mission_path, 'Verify sequence', ['ordered runtime evidence'], PARTICIPANTS, LIMITS)
            task = coordination.create_task(state, producer='chuck', recipient='tally', title='Bounded task', brief='Reply safely.', requested_action='Return handoff.', evidence=[])
            adapter = SequencedAdapter(state)
            dispatcher.dispatch_task(state, mission_path, task['id'], active['id'], adapter)
            self.assertEqual([('launch', 'dispatching'), ('collect', 'dispatched')], adapter.observed)


if __name__ == '__main__':
    unittest.main()
