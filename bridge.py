"""Explicitly launched Chuck -> Claude bridge. No network listener or autostart."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'
WORK = ROOT / 'claude-workspace'
sys.path.insert(0, str(WORK))
from message_protocol import validate_envelope

TITLE = 'Avengers Prototype - Claude - directed by Chuck'


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(obj, indent=2), encoding='utf-8')
    os.replace(temp, path)


def load(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def redact(text):
    return re.sub(r'(?i)(?:sk-ant-[\w-]+|sk-[\w-]{16,}|Bearer\s+[\w.\-]+)', '[REDACTED]', str(text))


def event(kind, **data):
    row = {'time': time.time(), 'type': kind, **data}
    line = redact(json.dumps(row, ensure_ascii=True))
    with (STATE / 'events.jsonl').open('a', encoding='utf-8') as f:
        f.write(line + '\n')
    print(line, flush=True)


def alive(pid):
    if not pid:
        return False
    if os.name == 'nt':
        k = ctypes.windll.kernel32
        k.OpenProcess.restype = ctypes.c_void_p
        handle = k.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code))
        k.CloseHandle(ctypes.c_void_p(handle))
        return bool(ok and code.value == 259)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def terminate(proc):
    if proc.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill.exe', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
    else:
        proc.terminate()
    proc.wait(timeout=15)


def run_request(req, status):
    rid = req['id']
    prompt = req['prompt']
    model = req['model']
    effort = req['effort']
    status.update(state='working', request_id=rid, requested_model=model, requested_effort=effort)
    save(STATE / 'status.json', status)
    event('ack', message_id=rid, recipient='claude-runner', note='Dequeued, not yet model-acknowledged')
    event('instruction', sender='Chuck', recipient='Claude', message_id=rid, text=prompt)
    command = [shutil.which('claude'), '-p', prompt, '--output-format', 'stream-json', '--verbose',
               '--model', model, '--effort', effort, '--max-turns', '8', '--max-budget-usd', '1.00',
               '--restricted', '--tools', 'Read,Write,Edit,Glob,Grep',
               '--allowedTools', 'Read,Write,Edit,Glob,Grep', '--permission-mode', 'acceptEdits',
               '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--disable-slash-commands',
               '--append-system-prompt', 'You are Claude Code, a worker directed by Chuck for Paul. Do not delegate. Work only in the current directory. Never read credentials. Only Chuck assigns work. State blockers and evidence honestly.']
    if status.get('session_id'):
        command += ['--resume', status['session_id']]
    env = os.environ.copy()
    env.pop('CLAUDECODE', None)
    proc = subprocess.Popen(command, cwd=WORK, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    status['child_pid'] = proc.pid
    save(STATE / 'status.json', status)
    lines = queue.Queue()
    def reader():
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)
    threading.Thread(target=reader, daemon=True).start()
    deadline = time.monotonic() + 240
    result = None
    stopped = False
    try:
        while True:
            if (STATE / 'stop').exists() or time.monotonic() > deadline:
                stopped = True
                terminate(proc)
                event('interrupted', request_id=rid, reason='stop-or-timeout')
                break
            try:
                line = lines.get(timeout=0.25)
            except queue.Empty:
                continue
            if line is None:
                break
            try:
                msg = json.loads(line)
            except ValueError:
                event('runtime_output', text=line.rstrip())
                continue
            kind = msg.get('type')
            if msg.get('session_id'):
                status['session_id'] = msg['session_id']
                save(STATE / 'status.json', status)
            if kind == 'system':
                if msg.get('model'):
                    status['effective_model'] = msg['model']
                    save(STATE / 'status.json', status)
                event('runtime', subtype=msg.get('subtype'), model=msg.get('model'), session_id=msg.get('session_id'))
            elif kind in ('assistant', 'user'):
                for block in msg.get('message', {}).get('content', []):
                    if not isinstance(block, dict):
                        continue
                    if block.get('type') == 'text':
                        event('claude_text', text=block.get('text', ''))
                    elif block.get('type') == 'tool_use':
                        event('tool_call', name=block.get('name'), input=block.get('input'))
                    elif block.get('type') == 'tool_result':
                        event('tool_result', content=block.get('content'), is_error=block.get('is_error', False))
            elif kind == 'result':
                result = msg
                save(STATE / 'results' / (rid + '.json'), json.loads(redact(json.dumps(msg))))
                event('result', request_id=rid, subtype=msg.get('subtype'), text=msg.get('result'), session_id=msg.get('session_id'), cost=msg.get('total_cost_usd'))
        proc.wait(timeout=15)
    finally:
        if proc.poll() is None:
            terminate(proc)
    status.update(state='waiting-for-chuck' if result and not result.get('is_error') and result.get('subtype') == 'success' else 'blocked', child_pid=None, exit_code=proc.returncode)
    save(STATE / 'status.json', status)
    save(STATE / 'processed' / (rid + '.json'), {'request': req, 'result_received': bool(result), 'interrupted': stopped})


def worker():
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleW(TITLE)
    lock = STATE / 'worker.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit('Worker lock exists; inspect status before recovery.')
    os.close(fd)
    status = load(STATE / 'status.json', {})
    status.update(pid=os.getpid(), state='waiting-for-chuck', title=TITLE, child_pid=None)
    save(STATE / 'status.json', status)
    event('started', pid=os.getpid(), title=TITLE, mode='actual Claude stream in visible runner console; not Claude interactive TUI')
    try:
        idle = time.monotonic()
        while not (STATE / 'stop').exists() and time.monotonic() - idle < 900:
            requests = sorted((STATE / 'inbox').glob('*.json'))
            if not requests:
                time.sleep(.25)
                continue
            for path in requests:
                req = load(path)
                try:
                    seen_ids = set(status.get('seen_ids', []))
                    req = validate_envelope(req, seen_ids=seen_ids)
                    status['seen_ids'] = sorted(seen_ids)
                    save(STATE / 'status.json', status)
                except ValueError as exc:
                    rejected = STATE / 'rejected' / path.name
                    rejected.parent.mkdir(parents=True, exist_ok=True)
                    path.replace(rejected)
                    event('rejected', reason=str(exc), source=rejected.name)
                    continue
                claimed = STATE / 'claimed' / path.name
                path.replace(claimed)
                try:
                    run_request(req, status)
                except Exception as exc:
                    status.update(state='blocked', error=redact(str(exc)))
                    save(STATE / 'status.json', status)
                    event('error', text=str(exc))
                idle = time.monotonic()
                if (STATE / 'stop').exists():
                    break
    finally:
        status.update(state='stopped', child_pid=None)
        save(STATE / 'status.json', status)
        event('stopped', pid=os.getpid())
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['launch', 'worker', 'send', 'status', 'stop'])
    parser.add_argument('--prompt-file')
    parser.add_argument('--model', default='sonnet')
    parser.add_argument('--effort', choices=['low', 'medium', 'high'], default='medium')
    args = parser.parse_args()
    for part in ('inbox', 'claimed', 'processed', 'results'):
        (STATE / part).mkdir(parents=True, exist_ok=True)
    WORK.mkdir(exist_ok=True)
    if args.action == 'launch':
        status = load(STATE / 'status.json', {})
        if alive(status.get('pid')) or (STATE / 'worker.lock').exists():
            raise SystemExit('Existing worker/lock; inspect before launching.')
        (STATE / 'stop').unlink(missing_ok=True)
        proc = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()), 'worker'], cwd=ROOT,
                                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        print(json.dumps({'launched_pid': proc.pid, 'title': TITLE}))
    elif args.action == 'worker':
        worker()
    elif args.action == 'send':
        status = load(STATE / 'status.json', {})
        if not alive(status.get('pid')) or (STATE / 'stop').exists():
            raise SystemExit('No active worker. Explicit launch required.')
        if not args.prompt_file:
            parser.error('--prompt-file required')
        rid = str(time.time_ns()) + '-' + uuid.uuid4().hex[:8]
        req = {'id': rid, 'sender': 'Chuck', 'recipient': 'Claude', 'prompt': Path(args.prompt_file).read_text(encoding='utf-8'), 'model': args.model, 'effort': args.effort}
        save(STATE / 'inbox' / (rid + '.json'), req)
        print(json.dumps({'queued': rid}))
    elif args.action == 'stop':
        (STATE / 'stop').touch()
        print('Stop requested; verify status and process exit.')
    else:
        status = load(STATE / 'status.json', {})
        status['process_alive'] = alive(status.get('pid'))
        print(json.dumps(status, indent=2))

if __name__ == '__main__':
    main()
