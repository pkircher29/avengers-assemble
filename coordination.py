"""Durable, runtime-neutral task and handoff ledger for the local team."""
from __future__ import annotations

import json
import os
from pathlib import Path
import time
import uuid


def _now():
    return time.time()


def _save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding='utf-8')
    os.replace(temporary, path)


def _load(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def _tasks_path(state: Path) -> Path:
    return state / 'coordination' / 'tasks.json'


def _handoffs_path(state: Path) -> Path:
    return state / 'coordination' / 'handoffs.json'


def _validate_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be a non-empty string')
    return value.strip()


def _validate_strings(values, field):
    if not isinstance(values, list) or not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError(f'{field} must be a list of non-empty strings')
    return [value.strip() for value in values]


def _read_tasks(state: Path) -> list[dict]:
    tasks = _load(_tasks_path(state), [])
    if not isinstance(tasks, list):
        raise ValueError('task ledger is malformed')
    return tasks


def _find_task(tasks: list[dict], task_id: str) -> dict:
    for task in tasks:
        if task.get('id') == task_id:
            return task
    raise ValueError('unknown task')


def create_task(state: Path, *, producer: str, recipient: str, title: str, brief: str,
                requested_action: str, evidence: list[str]) -> dict:
    task = {
        'id': uuid.uuid4().hex,
        'producer': _validate_text(producer, 'producer'),
        'recipient': _validate_text(recipient, 'recipient'),
        'title': _validate_text(title, 'title'),
        'brief': _validate_text(brief, 'brief'),
        'requested_action': _validate_text(requested_action, 'requested_action'),
        'evidence': _validate_strings(evidence, 'evidence'),
        'status': 'queued',
        'created_at': _now(),
        'acknowledgement': None,
        'handoff_id': None,
    }
    tasks = _read_tasks(state)
    tasks.append(task)
    _save(_tasks_path(state), tasks)
    return task


def get_task(state: Path, task_id: str) -> dict:
    return _find_task(_read_tasks(state), task_id)


def acknowledge_task(state: Path, task_id: str, recipient: str, note: str) -> dict:
    tasks = _read_tasks(state)
    task = _find_task(tasks, task_id)
    if task['recipient'] != _validate_text(recipient, 'recipient'):
        raise ValueError('only the recipient can acknowledge this task')
    if task['acknowledgement'] is not None:
        raise ValueError('task already acknowledged')
    task['acknowledgement'] = {'recipient': recipient, 'note': _validate_text(note, 'note'), 'at': _now()}
    task['status'] = 'acknowledged'
    _save(_tasks_path(state), tasks)
    return task


def submit_handoff(state: Path, task_id: str, producer: str, recipient: str, claim: str,
                   confidence: str, sources: list[str], requested_action: str) -> dict:
    tasks = _read_tasks(state)
    task = _find_task(tasks, task_id)
    if task['recipient'] != _validate_text(producer, 'producer'):
        raise ValueError('only the assigned recipient can submit a handoff')
    if task['handoff_id'] is not None:
        raise ValueError('task already has a handoff')
    if confidence not in {'low', 'medium', 'high'}:
        raise ValueError('confidence must be low, medium, or high')
    handoff = {
        'id': uuid.uuid4().hex,
        'task_id': task_id,
        'producer': producer,
        'recipient': _validate_text(recipient, 'recipient'),
        'claim': _validate_text(claim, 'claim'),
        'confidence': confidence,
        'sources': _validate_strings(sources, 'sources'),
        'requested_action': _validate_text(requested_action, 'requested_action'),
        'review_status': 'needs-review',
        'created_at': _now(),
    }
    handoffs = _load(_handoffs_path(state), [])
    if not isinstance(handoffs, list):
        raise ValueError('handoff ledger is malformed')
    handoffs.append(handoff)
    _save(_handoffs_path(state), handoffs)
    task['handoff_id'] = handoff['id']
    task['status'] = 'handoff-submitted'
    _save(_tasks_path(state), tasks)
    return handoff


def snapshot(state: Path) -> dict:
    tasks = _read_tasks(state)
    handoffs = _load(_handoffs_path(state), [])
    if not isinstance(handoffs, list):
        raise ValueError('handoff ledger is malformed')
    return {'tasks': tasks, 'handoffs': handoffs}
