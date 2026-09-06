"""Tally adapter: preserve captured OpenClaw output before runtime acknowledgement."""
import json
from pathlib import Path

import coordination


class TallyAdapter:
    runtime = 'tally'

    def __init__(self, state: Path, process_factory=None):
        self.state = Path(state)
        self.process_factory = process_factory

    def launch(self, task, dispatch):
        if self.process_factory is None:
            raise ValueError('Tally process launcher is not configured')
        return {'process': self.process_factory([])}

    def collect(self, task, dispatch, handle):
        stdout, stderr = handle['process'].communicate(timeout=600)
        try:
            result = json.loads(stdout)
        except (TypeError, ValueError) as exc:
            raise ValueError('Tally runner did not return a JSON result') from exc
        response = result.get('finalAssistantVisibleText')
        if not isinstance(response, str) or not response.strip():
            raise ValueError('Tally runner returned no assistant response')
        evidence = self.state / 'coordination' / 'runtime' / (task['id'] + '.json')
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(json.dumps(result, indent=2), encoding='utf-8')
        coordination.record_runtime_ack(self.state, task['id'], dispatch['run_id'], self.runtime, response, str(evidence))
        return result
