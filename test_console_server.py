import unittest
from unittest.mock import patch
import console_server


class NativeTerminalTests(unittest.TestCase):
    @patch('console_server.os.path.exists', return_value=True)
    @patch('console_server.subprocess.Popen')
    def test_open_terminal_launches_windows_terminal_and_returns_receipt(self, popen, _exists):
        receipt = console_server.open_native_terminal('codex')
        self.assertEqual(receipt['agent'], 'codex')
        self.assertEqual(receipt['command_kind'], 'native_terminal')
        args = popen.call_args.args[0]
        self.assertIn('wt.exe', args[0])
        self.assertIn('codex --dangerously-bypass-approvals-and-sandbox', args)

    @patch('console_server.coordination.get_task', return_value={'recipient': 'codex'})
    @patch('console_server.os.path.exists', return_value=True)
    @patch('console_server.subprocess.Popen')
    def test_task_terminal_is_bound_to_task_recipient(self, popen, _exists, _task):
        receipt = console_server.open_task_terminal('task-12345678')
        self.assertEqual(receipt['agent'], 'codex')
        self.assertEqual(receipt['task_id'], 'task-12345678')
        self.assertEqual(receipt['command_kind'], 'task_directed_native_terminal')
        self.assertIn('launch_adapter_terminal.py', popen.call_args.args[0][-1])

    def test_open_terminal_rejects_unknown_agent(self):
        with self.assertRaisesRegex(ValueError, 'unknown agent terminal'):
            console_server.open_native_terminal('invented-agent')


if __name__ == '__main__':
    unittest.main()
