import json, os, time, uuid
from pathlib import Path
def _path(state): return Path(state)/'coordination'/'runs.json'
def _save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp'); tmp.write_text(json.dumps(data,indent=2),encoding='utf-8'); os.replace(tmp,path)
def register(state,run_id,runtime,pid):
 path=_path(state); rows=json.loads(path.read_text()) if path.exists() else {}; record={'run_id':run_id,'runtime':runtime,'pid':pid,'state':'running','started_at':time.time()}; rows[run_id]=record; _save(path,rows); return record
def get(state,run_id):
 path=_path(state); rows=json.loads(path.read_text()) if path.exists() else {}; return rows.get(run_id)
