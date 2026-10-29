import importlib.util
from pathlib import Path
import subprocess

from test_upstream_release_sync import ReleaseGitFixture


SPEC = importlib.util.spec_from_file_location(
    "release_repair", Path(__file__).resolve().parents[1] / "release_repair.py",
)
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


class ReleaseRepairTests(ReleaseGitFixture):
    def setUp(self):
        super().setUp()
        (self.upstream / ".github").mkdir()
        self.commit(self.upstream, ".github/config.yml", "trusted: true\n")
        self.git(self.upstream, "tag", "v0.34.0")
        self.artifact = self.root / "artifact"
        self.publisher = self.root / "publisher"
        self.git(self.source, "config", "user.name", "Test")
        self.git(self.source, "config", "user.email", "test@example.com")
        # Helpers use a separate subprocess environment from the fixture.
        self.git(self.source, "config", "commit.gpgsign", "false")

    def publisher_checkout(self):
        self.git(self.root, "clone", "--branch", "docker", str(self.fork), str(self.publisher))
        self.git(self.publisher, "remote", "add", "upstream", str(self.upstream))
        self.git(self.publisher, "config", "user.name", "Test")
        self.git(self.publisher, "config", "user.email", "test@example.com")

    def test_merge_bundle_preserves_both_parents_without_publishing(self):
        state = repair.prepare(self.source, "v0.34.0")
        (self.source / "application.txt").write_text("repaired application\n")
        repair.package(self.source, state, self.artifact)
        self.publisher_checkout()
        candidate = repair.validate(
            self.publisher, "v0.34.0", self.artifact / "repair.bundle",
        )
        self.assertEqual(
            self.git(self.source, "rev-parse", "HEAD").stdout.strip(), candidate,
        )
        self.assertEqual(
            self.git(self.fork, "rev-parse", "refs/heads/docker").stdout.strip(),
            self.original,
        )
        self.assertEqual(
            self.git(self.publisher, "show", f"{candidate}:feature.txt").stdout,
            "XC output profiles\n",
        )

    def test_agent_can_resolve_application_conflict(self):
        self.commit(self.source, "application.txt", "fork application\n")
        self.git(self.upstream, "tag", "-d", "v0.34.0")
        self.commit(self.upstream, "application.txt", "upstream application\n")
        self.git(self.upstream, "tag", "v0.34.0")
        state = repair.prepare(self.source, "v0.34.0")
        self.assertIn("<<<<<<<", (self.source / "application.txt").read_text())
        (self.source / "application.txt").write_text("combined application\n")
        repair.package(self.source, state, self.artifact)
        self.assertTrue((self.artifact / "repair.bundle").exists())

    def test_workflow_edits_are_rejected(self):
        state = repair.prepare(self.source, "v0.34.0")
        (self.source / ".github/config.yml").write_text("trusted: false\n")
        with self.assertRaisesRegex(RuntimeError, "changed .github"):
            repair.package(self.source, state, self.artifact)

    def test_unresolved_markers_are_rejected(self):
        state = repair.prepare(self.source, "v0.34.0")
        (self.source / "application.txt").write_text(
            "<<<<<<< HEAD\nfork\n=======\nupstream\n>>>>>>> release\n",
        )
        with self.assertRaises(subprocess.CalledProcessError):
            repair.package(self.source, state, self.artifact)

    def test_publisher_rejects_bundle_with_changed_workflows(self):
        state = repair.prepare(self.source, "v0.34.0")
        repair.package(self.source, state, self.artifact)
        self.commit(self.source, ".github/config.yml", "trusted: false\n")
        self.git(self.source, "update-ref", repair.REPAIR_REF, "HEAD")
        self.git(self.source, "bundle", "create", str(self.artifact / "repair.bundle"),
                 repair.REPAIR_REF, f"^{state['base']}")
        self.publisher_checkout()
        with self.assertRaisesRegex(RuntimeError, "changed .github"):
            repair.validate(self.publisher, "v0.34.0", self.artifact / "repair.bundle")

    def test_publisher_rejects_concurrently_changed_docker_branch(self):
        state = repair.prepare(self.source, "v0.34.0")
        repair.package(self.source, state, self.artifact)
        self.publisher_checkout()
        self.commit(self.publisher, "concurrent.txt", "another change\n")
        with self.assertRaises(subprocess.CalledProcessError):
            repair.validate(self.publisher, "v0.34.0", self.artifact / "repair.bundle")

    def test_no_change_after_existing_merge_is_not_a_repair(self):
        self.git(self.source, "fetch", "upstream", "v0.34.0")
        self.git(self.source, "merge", "--no-ff", "FETCH_HEAD", "-m", "Already merged")
        state = repair.prepare(self.source, "v0.34.0")
        with self.assertRaisesRegex(RuntimeError, "no repair"):
            repair.package(self.source, state, self.artifact)

    def test_invalid_tag_cannot_be_used_as_git_argument(self):
        with self.assertRaises(ValueError):
            repair.prepare(self.source, "--upload-pack=invalid")

    def test_workflow_conflicts_require_human_intervention(self):
        (self.source / ".github").mkdir()
        self.commit(self.source, ".github/config.yml", "fork: true\n")
        with self.assertRaisesRegex(RuntimeError, "require human review"):
            repair.prepare(self.source, "v0.34.0")

    def test_published_release_never_gets_a_repair(self):
        self.git(self.source, "tag", "xc-profile-upstream/v0.34.0")
        self.git(self.source, "push", "origin", "refs/tags/xc-profile-upstream/v0.34.0")
        with self.assertRaisesRegex(RuntimeError, "already been published"):
            repair.prepare(self.source, "v0.34.0")

    def test_agent_created_commit_is_rejected(self):
        state = repair.prepare(self.source, "v0.34.0")
        self.git(self.source, "commit", "-m", "Unapproved agent commit")
        with self.assertRaisesRegex(RuntimeError, "must not create commits"):
            repair.package(self.source, state, self.artifact)

    def test_publisher_requires_upstream_ancestry(self):
        self.commit(self.source, "application.txt", "not an upstream merge\n")
        self.git(self.source, "update-ref", repair.REPAIR_REF, "HEAD")
        self.artifact.mkdir()
        self.git(self.source, "bundle", "create", str(self.artifact / "repair.bundle"),
                 repair.REPAIR_REF, f"^{self.original}")
        self.publisher_checkout()
        with self.assertRaises(subprocess.CalledProcessError):
            repair.validate(self.publisher, "v0.34.0", self.artifact / "repair.bundle")
