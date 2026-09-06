"""Claude adapter using proven safe-mode JSON output."""
import json, shutil, subprocess
from pathlib import Path
import coordination
import run_registry

class ClaudeAdapter:
    runtime='claude'
    def __init__(self,state,workspace=None): self.state=Path(state); self.workspace=Path(workspace) if workspace else Path.home()/'GITHUB'/'avengers-dashboard-ui-claude'
    def launch(self,task,dispatch):
        prompt='You are Claude, a bounded read-only worker directed by Chuck. Do not edit files, use network, read credentials, or delegate. Reply with a concise acknowledgement only. Task title: '+task['title']+'. Brief: '+task['brief']
        cmd=[shutil.which('claude') or 'claude','--safe-mode','-p','--dangerously-skip-permissions','--output-format','json','--max-turns','1','--model','sonnet','--effort','low',prompt]
        proc=subprocess.Popen(cmd,cwd=self.workspace,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace')
        run_registry.register(self.state,dispatch['run_id'],self.runtime,proc.pid)
        return {'process':proc}
    def collect(self,task,dispatch,handle):
        out,err=handle['process'].communicate(timeout=300); evidence=self.state/'coordination'/'runtime'/(task['id']+'.json'); evidence.parent.mkdir(parents=True,exist_ok=True)
        try: result=json.loads(out)
        except ValueError as exc: evidence.write_text(json.dumps({'stdout':out,'stderr':err},indent=2),encoding='utf-8'); raise ValueError('Claude runner did not return JSON') from exc
        if isinstance(result, list):
            result = next((item for item in reversed(result) if isinstance(item, dict) and isinstance(item.get('result'), str)), result[-1] if result else {})
        text=result.get('result') if isinstance(result, dict) else None; evidence.write_text(json.dumps(result,indent=2),encoding='utf-8')
        if getattr(handle['process'],'returncode',None)!=0 or result.get('is_error') or not isinstance(text,str) or not text.strip(): raise ValueError('Claude runner did not return successful result')
        coordination.record_runtime_ack(self.state,task['id'],dispatch['run_id'],self.runtime,text,str(evidence)); return result
