import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/upstream-release-repair.yml"
FAKE_GH = """#!/usr/bin/env python3
import os
from pathlib import Path
import sys

endpoint = sys.argv[2]
tag = "v0.34.0"
if os.environ.get("MOCK_API_FAILURE"):
    sys.exit("Simulated API failure")
if "matching-refs/tags/xc-profile-upstream/" in endpoint:
    if os.environ.get("MOCK_PUBLISHED"):
        print("refs/tags/xc-profile-upstream/" + tag)
elif "matching-refs/tags/xc-profile-repair-attempt/" in endpoint:
    if os.environ.get("MOCK_ATTEMPT"):
        print("refs/tags/xc-profile-repair-attempt/" + tag)
elif endpoint.endswith("/git/ref/heads/docker"):
    print("a" * 40)
elif endpoint.endswith("/git/refs"):
    Path(os.environ["MOCK_MARKER"]).write_text("reserved")
else:
    sys.exit("Unexpected API call: " + endpoint)
"""


class ReleaseRepairPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "release").mkdir()
        (self.root / "release/upstream-release.txt").write_text("v0.34.0\n")
        fake = self.root / "gh"
        fake.write_text(FAKE_GH)
        fake.chmod(0o755)
        self.output = self.root / "output"
        self.summary = self.root / "summary"
        self.marker = self.root / "marker"
        self.env = {
            **os.environ,
            "PATH": str(self.root) + os.pathsep + os.environ["PATH"],
            "RUNNER_TEMP": str(self.root),
            "GITHUB_OUTPUT": str(self.output),
            "GITHUB_STEP_SUMMARY": str(self.summary),
            "GITHUB_REPOSITORY": "smefa/Dispatcharr",
            "COPILOT_TOKEN": "fixture-token",
            "EVENT_NAME": "workflow_run",
            "RUN_ID": "123",
            "MOCK_MARKER": str(self.marker),
        }
        workflow = WORKFLOW.read_text()
        reserve = workflow.split("      - name: Reserve repair\n", 1)[1]
        self.script = textwrap.dedent(
            reserve.split("        run: |\n", 1)[1].split("\n\n  repair:", 1)[0],
        )

    def reserve(self, **env):
        return subprocess.run(
            ["bash", "-c", self.script], env={**self.env, **env},
            text=True, capture_output=True,
        )

    def test_new_release_reserves_before_allowing_agent(self):
        result = self.reserve()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.marker.exists())
        self.assertEqual(
            self.output.read_text(), "run_id=123\ntag=v0.34.0\nrepair=true\n",
        )

    def test_existing_attempt_does_not_repeat_automatically(self):
        result = self.reserve(MOCK_ATTEMPT="true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.marker.exists())
        self.assertFalse(self.output.exists())
        self.assertIn("already attempted", self.summary.read_text())

    def test_manual_retry_is_explicitly_allowed(self):
        result = self.reserve(MOCK_ATTEMPT="true", EVENT_NAME="workflow_dispatch")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.marker.exists())
        self.assertIn("repair=true", self.output.read_text())

    def test_missing_secret_fails_without_consuming_attempt(self):
        result = self.reserve(COPILOT_TOKEN="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("COPILOT_REPAIR_TOKEN", result.stdout)
        self.assertFalse(self.marker.exists())
        self.assertFalse(self.output.exists())

    def test_published_release_never_launches_agent(self):
        result = self.reserve(MOCK_PUBLISHED="true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.marker.exists())
        self.assertFalse(self.output.exists())
        self.assertIn("already been published", self.summary.read_text())

    def test_api_failure_is_not_treated_as_an_unused_attempt(self):
        result = self.reserve(MOCK_API_FAILURE="true")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.marker.exists())
        self.assertFalse(self.output.exists())
