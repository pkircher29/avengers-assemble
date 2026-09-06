"""Codex adapter: collect verified JSONL output before runtime acknowledgement."""
import json
from pathlib import Path

import coordination


class CodexAdapter:
    runtime = 'codex'

    def __init__(self, state: Path, process_factory=None):
        self.state = Path(state)
        self.process_factory = process_factory

    def launch(self, task, dispatch):
        if self.process_factory is None:
            raise ValueError('Codex process launcher is not configured')
        return {'process': self.process_factory([])}

    def collect(self, task, dispatch, handle):
        stdout, stderr = handle['process'].communicate(timeout=600)
        events, thread_id, final_text, usage = [], None, None, None
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            events.append(event)
            if event.get('type') == 'thread.started':
                thread_id = event.get('thread_id')
            if event.get('type') == 'item.completed':
                item = event.get('item') or {}
                if item.get('type') == 'agent_message' and isinstance(item.get('text'), str) and item['text'].strip():
                    final_text = item['text'].strip()
            if event.get('type') == 'turn.completed' and isinstance(event.get('usage'), dict):
                usage = event['usage']
        evidence = self.state / 'coordination' / 'runtime' / (task['id'] + '.json')
        evidence.parent.mkdir(parents=True, exist_ok=True)
        result = {'thread_id': thread_id, 'final_text': final_text, 'usage': usage, 'events': events, 'stderr': stderr, 'returncode': getattr(handle['process'], 'returncode', None)}
        evidence.write_text(json.dumps(result, indent=2), encoding='utf-8')
        if getattr(handle['process'], 'returncode', None) != 0 or not thread_id or not final_text or not usage:
            raise ValueError('Codex runner did not produce a complete successful result; evidence saved at ' + str(evidence))
        coordination.record_runtime_ack(self.state, task['id'], dispatch['run_id'], self.runtime, final_text, str(evidence))
        return result
