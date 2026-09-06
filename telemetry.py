"""Aggregate dashboard facts without inventing unavailable runtime telemetry."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'
REGISTRY = ROOT / 'agent_registry.json'


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return default


def unavailable(reason):
    return {'state': 'unavailable', 'reason': reason}


def claude_telemetry():
    status = load_json(STATE / 'status.json', {})
    results = []
    for path in (STATE / 'results').glob('*.json') if (STATE / 'results').exists() else []:
        data = load_json(path, {})
        if data:
            results.append(data)
    cost = sum(float(item.get('total_cost_usd') or 0) for item in results)
    return {
        'requested_model': status.get('requested_model') or unavailable('No request has been recorded.'),
        'effective_model': status.get('effective_model') or unavailable('Runtime has not reported a model.'),
        'requested_effort': status.get('requested_effort') or unavailable('No request has been recorded.'),
        'effective_effort': unavailable('Claude stream metadata does not report effective effort.'),
        'usage': {'reported_cost_usd': cost, 'token_usage': unavailable('Claude results currently record cost but not token totals.')},
        'session_id': status.get('session_id') or unavailable('No Claude session exists.'),
        'raw_state': status.get('state', 'not-launched'),
    }


def tally_telemetry():
    session_root = Path.home() / '.openclaw-avengers-free' / 'agents' / 'main' / 'sessions'
    latest = max(session_root.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, default=None) if session_root.exists() else None
    return {
        'requested_model': 'openrouter/openrouter/free',
        'effective_model': 'openrouter/free',
        'requested_effort': 'low',
        'effective_effort': 'low',
        'usage': unavailable('OpenClaw session usage parser is not implemented in V1.'),
        'session_file': str(latest) if latest else unavailable('No session file found.'),
    }


def build_roster():
    registry = load_json(REGISTRY, {'agents': []})
    roster = []
    for agent in registry['agents']:
        item = dict(agent)
        if agent['id'] == 'claude': item['telemetry'] = claude_telemetry()
        elif agent['id'] == 'tally': item['telemetry'] = tally_telemetry()
        else: item['telemetry'] = unavailable('Adapter does not have a verified telemetry bridge.')
        roster.append(item)
    return roster
