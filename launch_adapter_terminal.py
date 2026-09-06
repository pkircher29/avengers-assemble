"""Visible task-directed adapter terminal with durable stdout capture."""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'


def task(task_id):
    rows = json.loads((STATE / 'coordination' / 'tasks.json').read_text(encoding='utf-8'))
    found = next((row for row in rows if row.get('id') == task_id), None)
    if not found:
        raise SystemExit('Unknown Avengers task: ' + task_id)
    return found


def status_path(task_id):
    return STATE / 'coordination' / 'terminal' / (task_id + '.json')


def save_status(status_task_id, **data):
    path = status_path(status_task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: launch_adapter_terminal.py ADAPTER TASK_ID')
    adapter, task_id = sys.argv[1:]
    item = task(task_id)
    if item.get('recipient') != adapter:
        raise SystemExit('Task recipient does not match adapter')
    prompt = ('You are ' + adapter + ', a bounded Avengers worker directed by Chuck. '
              'Do not use network, credentials, delegation, or edits. '
              'Return a concise acknowledgement and evidence note. Task: ' + item['title'] + '. Brief: ' + item['brief'])
    log = STATE / 'coordination' / 'terminal' / (task_id + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    header = ('AVENGERS DIRECTED TERMINAL\nMission task: ' + item['id'] + '\nRecipient: ' + adapter +
              '\nTitle: ' + item['title'] + '\nStatus: ' + item['status'] + '\n--- exact adapter output follows ---\n')
    print(header, end='', flush=True)
    log.write_text(header, encoding='utf-8')
    if adapter == 'claude':
        cmd = [shutil.which('claude') or 'claude', '--safe-mode', '-p', '--dangerously-skip-permissions', '--output-format', 'json', '--max-turns', '1', '--model', 'sonnet', '--effort', 'low', prompt]
    elif adapter == 'codex':
        codex = Path(os.environ.get('APPDATA', 'C:/Users/Paul/AppData/Roaming')) / 'npm' / 'codex.cmd'
        cmd = [str(codex), 'exec', '--json', '--dangerously-bypass-approvals-and-sandbox', '--config', 'mcp_servers={}', '--sandbox', 'read-only', prompt]
    elif adapter == 'antigravity':
        agy = Path(os.environ.get('LOCALAPPDATA', 'C:/Users/Paul/AppData/Local')) / 'agy' / 'bin' / 'agy.exe'
        cmd = [str(agy), '--dangerously-skip-permissions', '--disable-slash-commands', '--output-format', 'json', '--effort', 'low', '-p', prompt]
    elif adapter == 'tally':
        cmd = ['openclaw', '--profile', 'avengers-free', 'agent', '--agent', 'main', '--session-key', 'avengers-' + task_id, '--message', prompt, '--json']
    else:
        raise SystemExit('Unsupported adapter: ' + adapter)
    save_status(task_id, task_id=task_id, adapter=adapter, state='running', started_at=time.time(), log=str(log))
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace')
    with log.open('a', encoding='utf-8') as handle:
        for line in proc.stdout:
            sys.stdout.write(line); sys.stdout.flush(); handle.write(line); handle.flush()
    code = proc.wait()
    save_status(task_id, task_id=task_id, adapter=adapter, state='completed' if code == 0 else 'failed',
                exit_code=code, completed_at=time.time(), log=str(log))
    raise SystemExit(code)


if __name__ == '__main__':
    main()
