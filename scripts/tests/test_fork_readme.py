import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "update_fork_readme.py"
spec = importlib.util.spec_from_file_location("update_fork_readme", SCRIPT)
readme_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readme_sync)


class ForkReadmeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.readme = Path(self.temp.name) / "README.md"
        self.upstream = "# Upstream README\n\nExisting instructions.\n"
        self.readme.write_text(self.upstream, encoding="utf-8")

    def test_adds_documentation_and_preserves_upstream_text(self):
        readme_sync.update_readme(self.readme)
        updated = self.readme.read_text(encoding="utf-8")
        self.assertTrue(updated.startswith(readme_sync.START))
        self.assertTrue(updated.endswith(self.upstream))
        self.assertIn(readme_sync.DOCUMENTATION.read_text(encoding="utf-8").strip(), updated)

    def test_replaces_only_managed_section(self):
        self.readme.write_text(
            "Introduction\n" + readme_sync.START + "\nOld usage\n" +
            readme_sync.END + "\n" + self.upstream,
            encoding="utf-8",
        )
        readme_sync.update_readme(self.readme)
        updated = self.readme.read_text(encoding="utf-8")
        self.assertTrue(updated.startswith("Introduction\n" + readme_sync.START))
        self.assertTrue(updated.endswith("\n" + self.upstream))
        self.assertNotIn("Old usage", updated)
        self.assertEqual(updated.count(readme_sync.START), 1)

    def test_repeated_updates_are_idempotent(self):
        readme_sync.update_readme(self.readme)
        first = self.readme.read_bytes()
        readme_sync.update_readme(self.readme)
        self.assertEqual(self.readme.read_bytes(), first)

    def test_malformed_markers_fail_without_changing_readme(self):
        for content in (
            readme_sync.START,
            readme_sync.END,
            readme_sync.END + readme_sync.START,
            readme_sync.START * 2 + readme_sync.END,
            readme_sync.START + readme_sync.END * 2,
        ):
            with self.subTest(content=content):
                self.readme.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    readme_sync.update_readme(self.readme)
                self.assertEqual(self.readme.read_text(encoding="utf-8"), content)

    def test_invalid_documentation_fails_without_changing_readme(self):
        documentation = Path(self.temp.name) / "documentation.md"
        for content in ("", " \n", readme_sync.START, readme_sync.END):
            with self.subTest(content=content):
                documentation.write_text(content, encoding="utf-8")
                with patch.object(readme_sync, "DOCUMENTATION", documentation):
                    with self.assertRaises(ValueError):
                        readme_sync.update_readme(self.readme)
                self.assertEqual(self.readme.read_text(encoding="utf-8"), self.upstream)

    def test_repository_readme_contains_current_documentation(self):
        readme = SCRIPT.parents[1] / "README.md"
        original = readme.read_text(encoding="utf-8")
        self.readme.write_text(original, encoding="utf-8")
        readme_sync.update_readme(self.readme)
        self.assertEqual(self.readme.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
