"""Managed adapter process stop/recovery primitives."""
import subprocess
import time
import run_registry

def stop_registered_run(state, run_id, reason):
 record=run_registry.get(state,run_id)
 if not record: raise ValueError('unknown managed run')
 if record['state']!='running': return record
 run_registry.update(state,run_id,state='stopping',stop_reason=reason,stop_requested_at=time.time())
 result=subprocess.run(['taskkill.exe','/PID',str(record['pid']),'/T','/F'],capture_output=True,text=True)
 return run_registry.update(state,run_id,state='stopped' if result.returncode==0 else 'termination_failed',termination_verified=result.returncode==0,stopped_at=time.time(),termination_output=(result.stdout+result.stderr).strip())

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
