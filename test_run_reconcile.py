import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import run_registry
class ReconcileTests(unittest.TestCase):
 def test_missing_pid_becomes_orphaned(self):
  with tempfile.TemporaryDirectory() as temp:
   state=Path(temp); run_registry.register(state,'r','codex',999)
   class R:returncode=1
   with patch('run_registry.subprocess.run',return_value=R()): runs=run_registry.reconcile(state)
   self.assertEqual('orphaned',runs[0]['state'])
if __name__=='__main__':unittest.main()
