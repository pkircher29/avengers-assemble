"""Managed adapter process stop/recovery primitives."""
import time

def stop_managed_run(records, run_id, process, reason, terminate):
    record=records.setdefault(run_id, {'run_id':run_id,'pid':process.pid,'state':'running'})
    if record['state'] in {'stopped','completed','failed'}: return record
    record.update(state='stopping',stop_requested_at=time.time(),stop_reason=reason)
    terminate(process)
    if process.poll() is None:
        record.update(state='termination_failed',termination_verified=False)
    else:
        record.update(state='stopped',stopped_at=time.time(),exit_code=process.poll(),termination_verified=True)
    return record
