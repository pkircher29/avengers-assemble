import os
import re
import unittest

DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), "dashboard.html")


class DashboardFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DASHBOARD_PATH, encoding="utf-8") as handle:
            cls.content = handle.read()

    def test_operator_regions_exist(self):
        for element_id in (
            "mission-objective", "mission-state", "rounds", "task-count",
            "attention-count", "scope-boundary", "freshness", "agent-roster",
            "attention-list", "task-list", "run-list", "handoff-list",
            "event-timeline", "task-form", "error-state", "live-status",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', self.content)

    def test_real_controls_are_present_and_initially_disabled(self):
        for button_id in ("btn-refresh", "btn-pause", "btn-resume", "btn-stop"):
            with self.subTest(button_id=button_id):
                self.assertRegex(self.content, rf'id="{button_id}"[^>]*disabled')
        for label in ("Dispatch", "Force stop process tree", "Approve", "Quarantine", "Release"):
            self.assertIn(label, self.content)

    def test_control_labels_do_not_overstate_capabilities(self):
        self.assertIn("Launch new terminal", self.content)
        self.assertIn("No retry/recovery endpoint is currently implemented", self.content)
        self.assertIn("Controller reachability does not prove live worker telemetry", self.content)
        self.assertNotIn("embedded terminal", self.content.lower())

    def test_uses_exact_targeted_endpoints(self):
        for route in ("/api/tasks/", "/dispatch", "/api/runs/", "/stop", "/api/handoffs/", "/review"):
            self.assertIn(route, self.content)
        self.assertIn("encodeURIComponent(t.id)", self.content)
        self.assertIn("encodeURIComponent(r.run_id)", self.content)
        self.assertIn("encodeURIComponent(h.id)", self.content)

    def test_review_requires_inline_rationale_not_browser_prompt(self):
        self.assertIn("Rationale for", self.content)
        self.assertIn("textarea required", self.content)
        self.assertNotIn("window.prompt", self.content)

    def test_truthful_fleet_rendering_is_per_agent(self):
        self.assertIn("function renderRoster", self.content)
        self.assertIn("d.roster", self.content)
        self.assertIn("function ownState", self.content)
        self.assertIn("Live state unknown", self.content)
        self.assertIn("agent.lifecycle", self.content)
        self.assertIn("telemetry.current_work", self.content)

    def test_no_external_or_fake_terminal_resources(self):
        self.assertNotIn("http://", self.content)
        self.assertNotIn("https://", self.content)
        self.assertNotRegex(self.content, r"<link[^>]+href=")
        self.assertNotRegex(self.content, r'<script[^>]+src=')
        self.assertNotRegex(self.content, r"<iframe", re.IGNORECASE)
        for token in ("xterm", "term.js", "pty.js", "fake-terminal", "simulated-terminal"):
            self.assertNotIn(token, self.content.lower())

    def test_error_handling_and_accessibility_hooks_exist(self):
        self.assertIn("if(!r.ok)", self.content)
        self.assertIn("aria-live=\"polite\"", self.content)
        self.assertIn("@media(max-width:56rem)", self.content)
        self.assertIn("confirm('Force stop this registered process tree?')", self.content)


if __name__ == "__main__":
    unittest.main()
