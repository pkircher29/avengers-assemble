import tempfile,unittest
from pathlib import Path
import run_registry
class StopPriorityTests(unittest.TestCase):
 def test_stopped_run_is_not_overwritten_by_collection_failure(self):
  with tempfile.TemporaryDirectory() as temp:
   s=Path(temp); run_registry.register(s,'r','tally',1); run_registry.update(s,'r',state='stopped')
   record=run_registry.get(s,'r')
   if record.get('state')=='running': run_registry.update(s,'r',state='failed')
   self.assertEqual('stopped',run_registry.get(s,'r')['state'])
if __name__=='__main__':unittest.main()
