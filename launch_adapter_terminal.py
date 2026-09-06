"""Visible, task-directed adapter terminal. This does not create a managed run."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'

def task(task_id):
    rows = json.loads((STATE / 'coordination' / 'tasks.json').read_text(encoding='utf-8'))
    found = next((row for row in rows if row.get('id') == task_id), None)
    if not found:
        raise SystemExit('Unknown Avengers task: ' + task_id)
    return found

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
    print('AVENGERS DIRECTED TERMINAL')
    print('Mission task:', item['id'])
    print('Recipient:', adapter)
    print('Title:', item['title'])
    print('Status:', item['status'])
    print('--- executing bounded adapter command ---', flush=True)
    if adapter == 'claude':
        cmd = [shutil.which('claude') or 'claude', '--safe-mode', '-p', '--dangerously-skip-permissions', '--output-format', 'json', '--max-turns', '1', '--model', 'sonnet', '--effort', 'low', prompt]
    elif adapter == 'codex':
        cmd = ['codex', 'exec', '--json', '--dangerously-bypass-approvals-and-sandbox', '--config', 'mcp_servers={}', '--sandbox', 'read-only', prompt]
    elif adapter == 'antigravity':
        agy = Path(os.environ.get('LOCALAPPDATA', 'C:/Users/Paul/AppData/Local')) / 'agy' / 'bin' / 'agy.exe'
        cmd = [str(agy), '--dangerously-skip-permissions', '--disable-slash-commands', '--output-format', 'json', '--effort', 'low', '-p', prompt]
    elif adapter == 'tally':
        cmd = ['openclaw', '--profile', 'avengers-free', 'terminal', '--local', '--message', prompt]
    else:
        raise SystemExit('Unsupported adapter: ' + adapter)
    result = subprocess.run(cmd, cwd=ROOT)
    raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()
