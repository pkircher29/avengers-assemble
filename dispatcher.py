"""Explicit at-most-once dispatcher core; adapters are supplied by the caller."""
from pathlib import Path

import coordination
import mission


def dispatch_task(state: Path, mission_path: Path, task_id: str, mission_id: str, adapter):
    current = mission.load(mission_path)
    if not current or current['id'] != mission_id:
        raise ValueError('mission id does not match the active record')
    if current['state'] != 'active':
        raise ValueError('mission must be active before dispatch')
    if current['rounds'] >= current['limits']['max_rounds']:
        raise ValueError('mission maximum rounds reached')
    task = coordination.claim_dispatch(state, task_id, mission_id, adapter.runtime)
    mission.add_round(mission_path)
    adapter.launch(task, task['dispatch'])
    return coordination.mark_dispatched(state, task_id)
