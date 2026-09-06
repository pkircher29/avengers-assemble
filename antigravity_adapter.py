"""Antigravity adapter: capture JSON print-mode output before acknowledgement."""
import json, os, shutil, subprocess
from pathlib import Path
import coordination
import run_registry


class AntigravityAdapter:
    runtime = 'antigravity'
    def __init__(self, state: Path, process_factory=None, workspace=None):
        self.state = Path(state); self.process_factory = process_factory
        self.workspace = Path(workspace) if workspace else Path.home() / 'GITHUB' / 'avengers-antigravity-readonly'

    def launch(self, task, dispatch):
        prompt = ('You are Antigravity, a bounded read-only worker directed by Chuck. Do not edit files, use network, read credentials, or delegate. Reply with a concise acknowledgement only. Task title: ' + task['title'] + '. Brief: ' + task['brief'])
        exe = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'agy', 'bin', 'agy.exe')
        command = [exe if os.path.exists(exe) else (shutil.which('agy') or 'agy'), '--dangerously-skip-permissions', '--disable-slash-commands', '--output-format', 'json', '--effort', 'medium', '-p', prompt]
        if self.process_factory: return {'process': self.process_factory(command)}
        proc = subprocess.Popen(command, cwd=self.workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        run_registry.register(self.state, dispatch['run_id'], self.runtime, proc.pid)
        return {'process': proc}

    def collect(self, task, dispatch, handle):
        stdout, stderr = handle['process'].communicate(timeout=600)
        evidence = self.state / 'coordination' / 'runtime' / (task['id'] + '.json'); evidence.parent.mkdir(parents=True, exist_ok=True)
        try: result = json.loads(stdout)
        except ValueError as exc:
            evidence.write_text(json.dumps({'stdout':stdout,'stderr':stderr,'returncode':getattr(handle['process'],'returncode',None),'parse_error':str(exc)},indent=2),encoding='utf-8'); raise ValueError('Antigravity runner did not return JSON') from exc
        response = result.get('response')
        evidence.write_text(json.dumps(result,indent=2),encoding='utf-8')
        if getattr(handle['process'],'returncode',None) != 0 or result.get('status') != 'SUCCESS' or not isinstance(response,str) or not response.strip(): raise ValueError('Antigravity runner did not return a complete successful result')
        coordination.record_runtime_ack(self.state, task['id'], dispatch['run_id'], self.runtime, response, str(evidence)); return result
