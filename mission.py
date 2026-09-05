"""Durable goal-style mission records for the local Avengers control plane."""
from __future__ import annotations

import json
import os
from pathlib import Path
import time
import uuid

VALID_STATES = frozenset({'active', 'paused', 'cleared'})


def _now():
    return time.time()


def _save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding='utf-8')
    os.replace(temporary, path)


def load(path: Path) -> dict | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding='utf-8'))
    validate(value)
    return value


def validate(value: dict) -> dict:
    if not isinstance(value, dict):
        raise ValueError('mission must be an object')
    required = {'id', 'objective', 'acceptance_checks', 'state', 'participants', 'limits', 'created_at', 'updated_at', 'rounds'}
    extras = set(value) - required
    missing = required - set(value)
    if extras:
        raise ValueError(f'unexpected mission field: {sorted(extras)[0]}')
    if missing:
        raise ValueError(f'missing mission field: {sorted(missing)[0]}')
    for field in ('id', 'objective'):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError(f'mission {field} must be a non-empty string')
    if value['state'] not in VALID_STATES:
        raise ValueError('mission state must be active, paused, or cleared')
    if not isinstance(value['acceptance_checks'], list) or not all(isinstance(item, str) and item.strip() for item in value['acceptance_checks']):
        raise ValueError('mission acceptance_checks must be a list of non-empty strings')
    if not isinstance(value['participants'], list) or not value['participants']:
        raise ValueError('mission participants must be a non-empty list')
    for participant in value['participants']:
        if not isinstance(participant, dict) or set(participant) != {'name', 'role', 'requested_model', 'requested_effort'}:
            raise ValueError('mission participant has invalid fields')
        if not all(isinstance(participant[field], str) and participant[field].strip() for field in participant):
            raise ValueError('mission participant values must be non-empty strings')
    if not isinstance(value['limits'], dict) or set(value['limits']) != {'max_rounds', 'max_turns_per_worker', 'max_budget_usd'}:
        raise ValueError('mission limits have invalid fields')
    if not isinstance(value['limits']['max_rounds'], int) or value['limits']['max_rounds'] < 1:
        raise ValueError('mission max_rounds must be a positive integer')
    if not isinstance(value['limits']['max_turns_per_worker'], int) or value['limits']['max_turns_per_worker'] < 1:
        raise ValueError('mission max_turns_per_worker must be a positive integer')
    if not isinstance(value['limits']['max_budget_usd'], (int, float)) or value['limits']['max_budget_usd'] <= 0:
        raise ValueError('mission max_budget_usd must be positive')
    if not isinstance(value['rounds'], int) or value['rounds'] < 0:
        raise ValueError('mission rounds must be a non-negative integer')
    return value


def start(path: Path, objective: str, acceptance_checks: list[str], participants: list[dict], limits: dict) -> dict:
    existing = load(path)
    if existing and existing['state'] == 'active':
        raise ValueError('cannot replace an active mission; pause or clear it first')
    mission = {
        'id': uuid.uuid4().hex,
        'objective': objective.strip(),
        'acceptance_checks': acceptance_checks,
        'state': 'active',
        'participants': participants,
        'limits': limits,
        'created_at': _now(),
        'updated_at': _now(),
        'rounds': 0,
    }
    validate(mission)
    _save(path, mission)
    return mission


def transition(path: Path, action: str) -> dict:
    mission = load(path)
    if not mission:
        raise ValueError('no mission exists')
    current = mission['state']
    if action == 'pause':
        if current != 'active':
            raise ValueError('only an active mission can be paused')
        mission['state'] = 'paused'
    elif action == 'resume':
        if current != 'paused':
            raise ValueError('only a paused mission can be resumed')
        mission['state'] = 'active'
    elif action == 'clear':
        if current == 'active':
            raise ValueError('pause the active mission before clearing it')
        mission['state'] = 'cleared'
    else:
        raise ValueError('unknown mission action')
    mission['updated_at'] = _now()
    _save(path, mission)
    return mission


def add_round(path: Path) -> dict:
    mission = load(path)
    if not mission or mission['state'] != 'active':
        raise ValueError('only an active mission can start a worker round')
    if mission['rounds'] >= mission['limits']['max_rounds']:
        raise ValueError('mission maximum rounds reached')
    mission['rounds'] += 1
    mission['updated_at'] = _now()
    _save(path, mission)
    return mission
