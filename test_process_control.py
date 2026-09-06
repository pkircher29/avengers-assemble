import unittest
import process_control

class FakeProcess:
 def __init__(self): self.pid=321; self.returncode=None
 def poll(self): return self.returncode

class ProcessControlTests(unittest.TestCase):
 def test_stop_records_request_and_terminal_state(self):
  records={}; proc=FakeProcess()
  result=process_control.stop_managed_run(records,'run-1',proc,'Paul requested stop',terminate=lambda p: setattr(p,'returncode',-9))
  self.assertEqual('stopped',result['state'])
  self.assertEqual('Paul requested stop',result['stop_reason'])

if __name__=='__main__': unittest.main()
