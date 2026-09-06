import unittest
from unittest.mock import patch
import telemetry


class HostProcessTelemetryTests(unittest.TestCase):
    @patch('telemetry.subprocess.run')
    def test_recognized_images_are_observed_but_unassigned(self, run):
        run.return_value.stdout = '"codex.exe","41","Console","1","10 K"\n"agy.exe","42","Console","1","10 K"\n"python.exe","43","Console","1","10 K"\n'
        result = telemetry.host_processes()
        self.assertEqual('available', result['state'])
        self.assertEqual([41, 42], [item['pid'] for item in result['items']])
        self.assertTrue(all(item['attribution'] == 'host-observed-unassigned' for item in result['items']))


if __name__ == '__main__':
    unittest.main()
