"""Local Dashboard V1 telemetry. Unknown values are never estimates.

Usage totals cover only the records reporting each metric; per-record values and
coverage counts preserve partial evidence. Tally reads canonical session JSONL,
not trace sidecars, and emits only explicitly allowlisted metadata.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'
REGISTRY = ROOT / 'agent_registry.json'
TOKEN_KEYS = ('input_tokens', 'output_tokens', 'cache_creation_input_tokens',
              'cache_read_input_tokens', 'input', 'output', 'cacheRead',
              'cacheWrite', 'reasoningTokens', 'totalTokens', 'total')


def load_json(path, default):
    try:
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        return value if isinstance(value, type(default)) else default
    except (OSError, UnicodeError, ValueError):
        return default


def records(path):
    try:
        with path.open(encoding='utf-8-sig') as stream:
            for line in stream:
                try:
                    value = json.loads(line)
                except ValueError:
                    continue
                if isinstance(value, dict):
                    yield value
    except (OSError, UnicodeError):
        return


def unavailable(reason):
    return {'state': 'unavailable', 'reason': reason}


def text_value(value, reason):
    return value if isinstance(value, str) and value.strip() else unavailable(reason)


def number(value):
    return (type(value) is int and value >= 0 or
            type(value) is float and math.isfinite(value) and value >= 0)


def safe_fields(record, keys):
    return {key: record[key] for key in keys
            if isinstance(record.get(key), str) or number(record.get(key))}


def empty_telemetry(reason):
    return {key: unavailable(reason) for key in (
        'requested_model', 'effective_model', 'requested_effort',
        'effective_effort', 'current_work', 'last_event', 'session_id',
        'raw_state', 'evidence_source')} | {
            'usage': usage_summary([], 'No verified usage records.')}


def usage_record(data, source, record_id=None, tally=False):
    usage = data.get('usage')
    usage = usage if isinstance(usage, dict) else {}
    tokens = {key: value for key, value in usage.items()
              if key in TOKEN_KEYS and type(value) is int and value >= 0}
    cost = data.get('total_cost_usd')
    if tally:
        cost_data = usage.get('cost')
        # OpenClaw also stores locally calculated price estimates. Only costs
        # explicitly marked as provider-reported qualify as actual metadata.
        cost = (cost_data.get('total') if isinstance(cost_data, dict)
                and cost_data.get('totalOrigin') == 'provider-billed' else None)
    return {'record_id': record_id, 'evidence_source': source,
            'token_usage': tokens or unavailable('No token metadata reported.'),
            'reported_cost_usd': cost if number(cost) else unavailable('No actual cost metadata reported.')}


def usage_summary(items, scope):
    totals, coverage, costs = {}, {}, []
    for item in items:
        for key, value in item['token_usage'].items():
            if key in TOKEN_KEYS:
                totals[key] = totals.get(key, 0) + value
                coverage[key] = coverage.get(key, 0) + 1
        if number(item['reported_cost_usd']):
            costs.append(item['reported_cost_usd'])
    try:
        cost_total = sum(costs) if costs else None
    except OverflowError:
        cost_total = None
    return {'scope': scope, 'record_count': len(items), 'records': items,
            'token_usage': totals or unavailable('No token metadata reported.'),
            'reported_cost_usd': cost_total if number(cost_total) else unavailable(
                'Reported cost total exceeds numeric range.' if costs else 'No actual cost metadata reported.'),
            'coverage': {'token_records': coverage, 'cost_records': len(costs)}}


def claude_telemetry():
    result = empty_telemetry('No Claude runtime metadata recorded.')
    status_path = STATE / 'status.json'
    status = load_json(status_path, {})
    for key in ('requested_model', 'effective_model', 'requested_effort', 'effective_effort', 'session_id'):
        result[key] = text_value(status.get(key), 'No recorded ' + key + '.')
    result['raw_state'] = text_value(status.get('state'), 'No worker state recorded.')
    if (status.get('state') == 'working' and isinstance(status.get('request_id'), str)
            and status['request_id'].strip()):
        result['current_work'] = {'request_id': status['request_id'], 'evidence_source': str(status_path)}
    else:
        result['current_work'] = unavailable('No active request recorded in worker status.')
    event_path = STATE / 'events.jsonl'
    for row in records(event_path):
        event = safe_fields(row, ('type', 'time', 'request_id', 'message_id', 'subtype', 'name'))
        if 'type' in event:
            result['last_event'] = event | {'evidence_source': str(event_path)}
    items = []
    for path in sorted((STATE / 'results').glob('*.json')):
        data = load_json(path, {})
        if data:
            items.append(usage_record(data, str(path), path.stem))
    result['usage'] = usage_summary(items, 'All local Claude result files; only reported metrics are summed.')
    if status or items or not result['last_event'].get('state'):
        result['evidence_source'] = {'status': str(status_path), 'events': str(event_path),
                                     'results': str(STATE / 'results')}
    return result


def tally_telemetry():
    result = empty_telemetry('No canonical OpenClaw session metadata recorded.')
    session_root = Path.home() / '.openclaw-avengers-free' / 'agents' / 'main' / 'sessions'
    candidates = []
    for path in session_root.glob('*.jsonl'):
        first = next(records(path), {})
        if first.get('type') == 'session':
            try:
                candidates.append((path.stat().st_mtime_ns, str(path), path))
            except OSError:
                pass
    if not candidates:
        result['session_file'] = unavailable('No canonical session file found.')
        return result
    path = max(candidates)[2]
    source = str(path)
    result['session_file'] = source
    result['evidence_source'] = source
    items, seen = [], set()
    for row in records(path):
        kind = row.get('type')
        if kind not in ('session', 'model_change', 'thinking_level_change', 'message'):
            continue
        result['last_event'] = safe_fields(row, ('type', 'timestamp', 'id')) | {'evidence_source': source}
        if kind == 'session':
            result['session_id'] = text_value(row.get('id'), 'Session id absent.')
        elif kind == 'model_change':
            result['requested_model'] = text_value(row.get('modelId'), 'Model selection absent.')
            # A new selection is not proof that a response used that model.
            result['effective_model'] = unavailable('No response after the latest model selection.')
        elif kind == 'thinking_level_change':
            result['requested_effort'] = text_value(row.get('thinkingLevel'), 'Thinking selection absent.')
            result['effective_effort'] = unavailable('No response effort metadata after the latest selection.')
        elif kind == 'message':
            message = row.get('message')
            if not isinstance(message, dict) or message.get('role') != 'assistant':
                continue
            identity = message.get('responseId') or row.get('id')
            if isinstance(identity, str):
                if identity in seen:
                    continue
                seen.add(identity)
            else:
                identity = None
            # Replayed responses are not evidence for a later model selection.
            result['effective_model'] = text_value(message.get('model'), 'Response model absent.')
            result['effective_effort'] = text_value(message.get('reasoningEffort'), 'Response does not report effective effort.')
            items.append(usage_record(message, source, identity, tally=True))
    result['usage'] = usage_summary(items, 'Latest canonical Tally session; trace sidecars excluded to avoid double counting.')
    result['current_work'] = unavailable('Session history does not establish currently active work.')
    result['raw_state'] = unavailable('Session history does not establish live worker state.')
    return result


def capability(value, terminal=False):
    """Normalize registry declarations without treating a CLI as an attach API."""
    result = dict(value) if isinstance(value, dict) else {}
    state = result.get('state', result.get('availability') if terminal else None)
    if state not in ('supported', 'unavailable'):
        state = 'unavailable'
        result['reason'] = 'No verified capability registered.'
    result['state'] = state
    if terminal:
        result['availability'] = state
    if state == 'unavailable':
        if not isinstance(result.get('reason'), str) or not result['reason'].strip():
            result['reason'] = 'No verified capability registered.'
        if not terminal:
            result['actions'] = []
    elif not terminal:
        actions = result.get('actions')
        if (not isinstance(actions, list) or not actions or
                any(not isinstance(action, str) or not action.strip() for action in actions)
                or not isinstance(result.get('endpoint'), str) or not result['endpoint'].strip()):
            result.update(unavailable('No verified control actions and endpoint registered.'))
            result['actions'] = []
    if not isinstance(result.get('evidence_source'), str) or not result['evidence_source'].strip():
        result['evidence_source'] = str(REGISTRY)
    return result


def build_roster():
    registry = load_json(REGISTRY, {'agents': []})
    roster = []
    agents = registry.get('agents', [])
    for agent in agents if isinstance(agents, list) else []:
        if not isinstance(agent, dict) or not isinstance(agent.get('id'), str):
            continue
        item = dict(agent)
        if agent['id'] == 'claude':
            facts = claude_telemetry()
        elif agent['id'] == 'tally':
            facts = tally_telemetry()
        else:
            facts = empty_telemetry('Adapter does not have a verified telemetry bridge.')
        item['terminal'] = capability(agent.get('terminal'), terminal=True)
        item['control_capability'] = capability(agent.get('control_capability'))
        item['controls'] = item['control_capability'].get('actions', [])
        item['evidence_source'] = {'registry': str(REGISTRY), 'runtime': facts['evidence_source']}
        facts['evidence_source'] = item['evidence_source']
        facts['terminal_capability'] = item['terminal']
        facts['control_capability'] = item['control_capability']
        item['telemetry'] = facts
        roster.append(item)
    return roster
