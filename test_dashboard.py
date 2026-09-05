import os
import re
import unittest

DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), "dashboard.html")

REQUIRED_IDS = (
    "mission-objective",
    "mission-state",
    "scope-boundary",
    "requested-model",
    "effective-model",
    "requested-effort",
    "effective-effort",
    "worker-state",
    "event-timeline",
    "empty-state",
    "error-state",
    "btn-refresh",
    "btn-pause",
    "btn-resume",
    "btn-stop",
)

REQUIRED_BUTTON_LABELS = ("Refresh", "Pause", "Resume", "Stop Worker")


class DashboardFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DASHBOARD_PATH, "r", encoding="utf-8") as handle:
            cls.content = handle.read()

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(DASHBOARD_PATH))

    def test_contains_required_ids(self):
        for element_id in REQUIRED_IDS:
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', self.content)

    def test_contains_required_button_labels(self):
        for label in REQUIRED_BUTTON_LABELS:
            with self.subTest(label=label):
                self.assertIn(label, self.content)

    def test_control_buttons_disabled_by_default(self):
        for button_id in ("btn-refresh", "btn-pause", "btn-resume", "btn-stop"):
            with self.subTest(button_id=button_id):
                pattern = rf'id="{button_id}"[^>]*disabled'
                self.assertRegex(self.content, pattern)

    def test_no_external_resources(self):
        self.assertNotIn("http://", self.content)
        self.assertNotIn("https://", self.content)

    def test_no_external_link_or_script_tags(self):
        self.assertNotRegex(self.content, r"<link[^>]+href=")
        self.assertNotRegex(self.content, r'<script[^>]+src=')

    def test_wire_controls_function_present(self):
        self.assertIn("function wireControls", self.content)


if __name__ == "__main__":
    unittest.main()
