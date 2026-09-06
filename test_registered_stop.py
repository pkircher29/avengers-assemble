import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import run_registry, process_control
class RegisteredStopTests(unittest.TestCase):
 def test_registered_pid_stop_updates_state(self):
  with tempfile.TemporaryDirectory() as temp:
   state=Path(temp); run_registry.register(state,'r1','codex',123)
   class R: returncode=0; stdout='ok'; stderr=''
   with patch('process_control.subprocess.run',return_value=R()) as call:
    result=process_control.stop_registered_run(state,'r1','Paul requested stop')
   self.assertEqual('stopped',result['state']); self.assertTrue(result['termination_verified']); self.assertIn('/PID',call.call_args.args[0])
if __name__=='__main__': unittest.main()
