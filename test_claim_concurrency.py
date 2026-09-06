import tempfile
import threading
import unittest
from pathlib import Path

import coordination


class ClaimConcurrencyTests(unittest.TestCase):
    def test_two_concurrent_claims_produce_one_winner(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)
            task = coordination.create_task(state, producer='chuck', recipient='codex', title='Concurrent task', brief='Do one thing.', requested_action='Report.', evidence=[])
            outcomes = []

            def claim():
                try:
                    coordination.claim_dispatch(state, task['id'], 'mission-1', 'codex')
                    outcomes.append('claimed')
                except ValueError:
                    outcomes.append('rejected')

            first, second = threading.Thread(target=claim), threading.Thread(target=claim)
            first.start(); second.start(); first.join(); second.join()
            self.assertEqual(['claimed', 'rejected'], sorted(outcomes))
            self.assertEqual('dispatching', coordination.get_task(state, task['id'])['status'])


if __name__ == '__main__':
    unittest.main()
