"""Tally adapter: preserve captured OpenClaw output before runtime acknowledgement."""
import json
from pathlib import Path
import shutil
import subprocess

import coordination
import run_registry


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
        proc = subprocess.Popen(command, cwd=self.workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                             text=True, encoding='utf-8', errors='replace')
        run_registry.register(self.state, dispatch['run_id'], self.runtime, proc.pid)
        return {'process': proc}

    def collect(self, task, dispatch, handle):
        stdout, stderr = handle['process'].communicate(timeout=600)
        evidence = self.state / 'coordination' / 'runtime' / (task['id'] + '.json')
        evidence.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = json.loads(stdout)
        except (TypeError, ValueError) as exc:
            evidence.write_text(json.dumps({'stdout': stdout, 'stderr': stderr, 'returncode': getattr(handle['process'], 'returncode', None), 'parse_error': str(exc)}, indent=2), encoding='utf-8')
            raise ValueError('Tally runner did not return a JSON result; raw output saved at ' + str(evidence)) from exc
        response = result.get('finalAssistantVisibleText')
        if not isinstance(response, str) or not response.strip():
            payloads = result.get('payloads')
            if isinstance(payloads, list):
                texts = [item.get('text') for item in payloads if isinstance(item, dict) and isinstance(item.get('text'), str) and item['text'].strip()]
                response = texts[-1] if texts else None
        if not isinstance(response, str) or not response.strip():
            evidence.write_text(json.dumps(result, indent=2), encoding='utf-8')
            raise ValueError('Tally runner returned no assistant response; result saved at ' + str(evidence))
        evidence.write_text(json.dumps(result, indent=2), encoding='utf-8')
        coordination.record_runtime_ack(self.state, task['id'], dispatch['run_id'], self.runtime, response, str(evidence))
        return result
