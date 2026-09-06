"""Loopback-only local mission console. Explicitly started; no autostart."""
import argparse, json, os, subprocess, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import mission
import telemetry
import coordination
import process_control
import run_registry
import dispatcher
from claude_adapter import ClaudeAdapter
from codex_adapter import CodexAdapter
from tally_adapter import TallyAdapter
from antigravity_adapter import AntigravityAdapter

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'
MISSION = STATE / 'mission.json'
DASHBOARD = ROOT / 'dashboard.html'


def read_json(path, default):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError): return default

def worker_lifecycle(mission_record, worker):
    mission_state = (mission_record or {}).get('state')
    worker_state = worker.get('state', 'not-launched')
    if mission_state == 'paused':
        return 'paused'
    if worker_state == 'working':
        return 'working'
    if worker_state == 'blocked':
        return 'blocked'
    if worker_state in {'stopped', 'not-launched'}:
        return 'waiting-to-launch' if mission_state == 'active' else 'stopped'
    if worker_state == 'waiting-for-chuck':
        return 'waiting-for-chuck'
    return 'unknown'


def stop_worker():
    result = subprocess.run([sys.executable, str(ROOT / 'bridge.py'), 'stop'], cwd=ROOT, capture_output=True, text=True, timeout=20)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or 'worker stop failed')
    return read_json(STATE / 'status.json', {'state': 'unknown'})


def open_task_terminal(task_id):
    task = coordination.get_task(STATE, task_id)
    agent_id = task['recipient']
    if agent_id not in {'claude', 'tally', 'antigravity', 'codex'}:
        raise ValueError('task recipient has no directed terminal adapter')
    title = f'Avengers — {agent_id.title()} — {task_id[:8]}'
    wt = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WindowsApps', 'wt.exe')
    if not os.path.exists(wt):
        raise ValueError('Windows Terminal launcher is unavailable')
    command = f'"{sys.executable}" "{ROOT / "launch_adapter_terminal.py"}" {agent_id} {task_id}'
    subprocess.Popen([wt, 'new-tab', '--title', title, 'cmd.exe', '/k', command], cwd=ROOT)
    receipt = {'time': time.time(), 'type': 'directed_terminal_open_requested', 'agent': agent_id, 'task_id': task_id, 'title': title, 'command_kind': 'task_directed_native_terminal'}
    with (STATE / 'events.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(receipt) + '\n')
    return receipt


def open_native_terminal(agent_id):
    commands = {
        'chuck': 'hermes',
        'claude': f'"{sys.executable}" "{ROOT / "bridge.py"}" launch',
        'tally': f'"{sys.executable}" "{ROOT / "launch_tally_terminal.py"}"',
        'antigravity': f'"{os.environ.get("LOCALAPPDATA", "C:/Users/Paul/AppData/Local")}/agy/bin/agy.exe" --dangerously-skip-permissions',
        'codex': 'codex --dangerously-bypass-approvals-and-sandbox',
    }
    if agent_id not in commands:
        raise ValueError('unknown agent terminal')
    title = f'Avengers — {agent_id.title()}'
    wt = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WindowsApps', 'wt.exe')
    if not os.path.exists(wt):
        raise ValueError('Windows Terminal launcher is unavailable')
    subprocess.Popen([wt, 'new-tab', '--title', title, 'cmd.exe', '/k', commands[agent_id]], cwd=ROOT)
    receipt = {'time': time.time(), 'type': 'terminal_open_requested', 'agent': agent_id, 'title': title, 'command_kind': 'native_terminal'}
    with (STATE / 'events.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(receipt) + '\n')
    return receipt


def snapshot():
    rows = []
    events = STATE / 'events.jsonl'
    if events.exists():
        for line in events.read_text(encoding='utf-8').splitlines()[-40:]:
            try: rows.append(json.loads(line))
            except json.JSONDecodeError: pass
    mission_record = mission.load(MISSION)
    worker = read_json(STATE/'status.json', {'state':'not-launched'})
    runs_path = STATE / 'coordination' / 'runs.json'
    runs = read_json(runs_path, {})
    return {'generated_at': time.time(), 'mission': mission_record, 'worker': worker, 'worker_lifecycle': worker_lifecycle(mission_record, worker), 'roster': telemetry.build_roster(), 'host_processes': telemetry.host_processes(), 'coordination': coordination.snapshot(STATE), 'runs': list(runs.values()) if isinstance(runs, dict) else [], 'events': rows,
            'scope_boundary':'Local-only control plane. Dispatch and stop are limited to registered managed adapters; browser terminals are not implemented.'}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    def send_json(self, code, body):
        data=json.dumps(body).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path == '/api/snapshot': return self.send_json(200, snapshot())
        if self.path == '/api/comms':
            data = snapshot()
            return self.send_json(200, {'generated_at': data['generated_at'], 'events': data['events'], 'source': 'durable controller event log'})
        if self.path != '/': return self.send_json(404, {'error':'not found'})
        data=DASHBOARD.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        actions={'/api/pause':'pause','/api/resume':'resume','/api/clear':'clear'}
        try:
            length = int(self.headers.get('Content-Length', '0'))
            payload = json.loads(self.rfile.read(length) or b'{}') if length else {}
            if not isinstance(payload, dict): raise ValueError('request body must be an object')
            if self.path == '/api/tasks':
                task = coordination.create_task(STATE, **payload)
                return self.send_json(201, {'task': task})
            parts = self.path.strip('/').split('/')
            if len(parts) == 4 and parts[:2] == ['api', 'tasks'] and parts[3] == 'acknowledgements':
                task = coordination.acknowledge_task(STATE, parts[2], payload.get('recipient'), payload.get('note'))
                return self.send_json(200, {'task': task})
            if len(parts) == 4 and parts[:2] == ['api', 'tasks'] and parts[3] == 'handoffs':
                handoff = coordination.submit_handoff(STATE, parts[2], **payload)
                return self.send_json(201, {'handoff': handoff})
            if len(parts) == 5 and parts[:2] == ['api', 'tasks'] and parts[3:] == ['terminal', 'open']:
                return self.send_json(200, {'receipt': open_task_terminal(parts[2])})
            if len(parts) == 4 and parts[:2] == ['api', 'tasks'] and parts[3] == 'dispatch':
                adapters={'claude':ClaudeAdapter,'codex':CodexAdapter,'tally':TallyAdapter,'antigravity':AntigravityAdapter}
                task=coordination.get_task(STATE,parts[2]); adapter_class=adapters.get(task['recipient'])
                if not adapter_class: raise ValueError('task recipient has no managed adapter')
                active=mission.load(MISSION); dispatched=dispatcher.dispatch_task(STATE,MISSION,task['id'],active['id'],adapter_class(STATE))
                return self.send_json(200, {'task':dispatched})
            if len(parts) == 4 and parts[:2] == ['api', 'handoffs'] and parts[3] == 'review':
                handoff = coordination.review_handoff(STATE, parts[2], payload.get('decision'), payload.get('rationale'))
                return self.send_json(200, {'handoff': handoff})
            if len(parts) == 4 and parts[:2] == ['api', 'runs'] and parts[3] == 'stop':
                run = process_control.stop_registered_run(STATE, parts[2], payload.get('reason', 'dashboard stop request'))
                return self.send_json(200, {'run': run})
            if self.path.startswith('/api/agents/') and self.path.endswith('/terminal/open'):
                agent_id = self.path.split('/')[3]
                return self.send_json(200, {'receipt': open_native_terminal(agent_id)})
            if self.path == '/api/stop-worker':
                return self.send_json(200, {'worker': stop_worker()})
            if self.path not in actions: return self.send_json(404, {'error':'not found'})
            result=mission.transition(MISSION, actions[self.path]); self.send_json(200, {'mission':result})
        except ValueError as exc: self.send_json(409, {'error':str(exc)})

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('action', choices=['start','status','mission-start','pause','resume','clear']); parser.add_argument('--objective'); args=parser.parse_args()
    STATE.mkdir(exist_ok=True)
    if args.action=='start':
        server=ThreadingHTTPServer(('127.0.0.1',8765),Handler); print('Mission Console: http://127.0.0.1:8765'); server.serve_forever()
    elif args.action=='status': print(json.dumps(snapshot(),indent=2))
    elif args.action=='mission-start':
        if not args.objective: parser.error('--objective required')
        print(json.dumps(mission.start(MISSION,args.objective,['dashboard reflects durable state'],[{'name':'Chuck','role':'coordinator','requested_model':'current','requested_effort':'high'},{'name':'Claude','role':'worker','requested_model':'sonnet','requested_effort':'medium'}],{'max_rounds':5,'max_turns_per_worker':8,'max_budget_usd':2.0}),indent=2))
    else: print(json.dumps(mission.transition(MISSION,args.action),indent=2))
if __name__=='__main__': main()
