import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "prepare_upstream_release.sh"


class ReleaseGitFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.upstream = self.root / "upstream"
        self.fork = self.root / "fork.git"
        self.source = self.root / "source"
        self.output = self.root / "output"
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "GITHUB_OUTPUT": str(self.output),
        }
        self.git(self.root, "init", "-b", "main", str(self.upstream))
        self.commit(self.upstream, "application.txt", "original\n")
        self.commit(self.upstream, "README.md", "# Upstream Dispatcharr\n")
        self.git(self.upstream, "tag", "v0.33.0")
        self.git(self.root, "clone", "--bare", str(self.upstream), str(self.fork))
        self.git(self.root, "clone", str(self.fork), str(self.source))
        self.git(self.source, "checkout", "-b", "docker")
        self.commit(self.source, "feature.txt", "XC output profiles\n")
        self.git(self.source, "push", "-u", "origin", "docker")
        self.git(self.source, "remote", "add", "upstream", str(self.upstream))
        self.original = self.git(self.source, "rev-parse", "HEAD").stdout.strip()

    def git(self, cwd, *args):
        repository = ["--git-dir=" + str(cwd)] if cwd == self.fork else []
        return subprocess.run(
            ["git", *repository, *args], cwd=cwd, env=self.env, check=True,
            capture_output=True, text=True,
        )

    def commit(self, cwd, name, content):
        (cwd / name).write_text(content)
        self.git(cwd, "add", name)
        self.git(cwd, "commit", "-m", "Update " + name)

    def release(self):
        self.commit(self.upstream, "application.txt", "new stable release\n")
        self.git(self.upstream, "tag", "-a", "v0.34.0", "-m", "Stable release")

    def prepare(self, tag="v0.34.0"):
        return subprocess.run(
            ["bash", str(SCRIPT), tag], cwd=self.source, env=self.env,
            capture_output=True, text=True,
        )


class UpstreamReleaseSyncTests(ReleaseGitFixture):
    def test_new_release_preserves_feature_without_publishing(self):
        self.release()
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("changed=true\n", self.output.read_text())
        self.assertIn("release_tag=v0.34.0\n", self.output.read_text())
        upstream_sha = self.git(self.upstream, "rev-parse", "HEAD").stdout.strip()
        self.assertIn("upstream_sha=" + upstream_sha, self.output.read_text())
        self.assertEqual((self.source / "feature.txt").read_text(), "XC output profiles\n")
        self.assertEqual((self.source / "application.txt").read_text(), "new stable release\n")
        readme = (self.source / "README.md").read_text()
        self.assertIn("# Dispatcharr with XC Output-Profile Links", readme)
        self.assertTrue(readme.endswith("# Upstream Dispatcharr\n"))
        self.assertEqual(self.git(self.source, "status", "--porcelain").stdout, "")
        self.assertEqual(
            self.git(self.fork, "rev-parse", "refs/heads/docker").stdout.strip(),
            self.original,
        )
        self.assertEqual(
            self.git(self.fork, "tag", "-l", "xc-profile-upstream/*").stdout, "",
        )

    def test_success_marker_skips_merge(self):
        self.git(self.source, "tag", "xc-profile-upstream/v0.34.0")
        self.git(self.source, "push", "origin", "refs/tags/xc-profile-upstream/v0.34.0")
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), "changed=false\n")
        self.assertEqual(self.git(self.source, "rev-parse", "HEAD").stdout.strip(), self.original)

    def test_conflict_fails_without_recording_success(self):
        self.commit(self.source, "application.txt", "fork-specific change\n")
        self.release()
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not be merged", result.stderr)
        self.assertFalse(self.output.exists())
        self.assertEqual(
            self.git(self.fork, "rev-parse", "refs/heads/docker").stdout.strip(),
            self.original,
        )

    def test_missing_upstream_tag_fails(self):
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_origin_error_is_not_treated_as_an_unpublished_release(self):
        self.git(self.source, "remote", "set-url", "origin", str(self.root / "missing.git"))
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_already_merged_release_without_marker_can_be_retried(self):
        self.release()
        self.assertEqual(self.prepare().returncode, 0)
        prepared = self.git(self.source, "rev-parse", "HEAD").stdout.strip()
        self.output.unlink()
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("changed=true\n", self.output.read_text())
        self.assertEqual(self.git(self.source, "rev-parse", "HEAD").stdout.strip(), prepared)

    def test_upstream_readme_updates_are_preserved(self):
        self.commit(self.upstream, "README.md", "# Updated upstream instructions\n")
        self.release()
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        readme = (self.source / "README.md").read_text()
        self.assertIn("# Dispatcharr with XC Output-Profile Links", readme)
        self.assertTrue(readme.endswith("# Updated upstream instructions\n"))

    def test_invalid_readme_markers_fail_without_success_outputs(self):
        self.commit(self.source, "README.md", "<!-- xc-profile-fork:start -->\n")
        self.release()
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one pair", result.stderr)
        self.assertFalse(self.output.exists())
        self.assertEqual(
            self.git(self.fork, "rev-parse", "refs/heads/docker").stdout.strip(),
            self.original,
        )

    def test_invalid_or_prerelease_tags_are_rejected(self):
        for tag in ("v0.34.0-rc1", "../main", "v0.34.0\nchanged=false", "$(false)"):
            with self.subTest(tag=tag):
                result = self.prepare(tag)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Unsupported stable release tag", result.stderr)
                self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
