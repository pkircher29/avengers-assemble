"""Tally adapter: preserve captured OpenClaw output before runtime acknowledgement."""
import json
from pathlib import Path
import shutil
import subprocess

import coordination


class TallyAdapter:
    runtime = 'tally'

    def __init__(self, state: Path, process_factory=None, workspace=None):
        self.state = Path(state)
        self.workspace = Path(workspace) if workspace else Path.home() / 'GITHUB' / 'avengers-openclaw-free-workspace'
        self.process_factory = process_factory

    def launch(self, task, dispatch):
        prompt = ('You are Tally, a bounded support worker directed by Chuck. Do not use tools, '
                  'do not make external calls, and do not read credentials. Reply with a concise factual '
                  'acknowledgement of this exact task only. Task title: ' + task['title'] + '. Brief: ' + task['brief'])
        command = [shutil.which('openclaw') or 'openclaw', '--profile', 'avengers-free', '--no-color', '--log-level', 'error',
                   'agent', '--local', '--agent', 'main', '--session-key', 'agent:main:coord-' + task['id'],
                   '--model', 'tally-granite/granite4.2:8b', '--thinking', 'off', '--timeout', '600', '--json', '--message', prompt]
        if self.process_factory is not None:
            return {'process': self.process_factory(command)}
        return {'process': subprocess.Popen(command, cwd=self.workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                             text=True, encoding='utf-8', errors='replace')}

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
