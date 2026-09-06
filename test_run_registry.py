import json, tempfile, unittest
from pathlib import Path
import run_registry
class RunRegistryTests(unittest.TestCase):
 def test_register_and_read_run(self):
  with tempfile.TemporaryDirectory() as temp:
   state=Path(temp); record=run_registry.register(state,'r1','codex',123)
   self.assertEqual('running',record['state'])
   self.assertEqual(record,run_registry.get(state,'r1'))
if __name__=='__main__': unittest.main()
