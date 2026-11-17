from pathlib import Path
import importlib.util
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "merge_migration_leaves.py"
spec = importlib.util.spec_from_file_location("merge_migration_leaves", SCRIPT)
merge_migration_leaves = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_migration_leaves)


def migration(directory, name, *dependencies):
    deps = "".join(f"        ({app!r}, {dep!r}),\n" for app, dep in dependencies)
    (directory / f"{name}.py").write_text(
        "from django.db import migrations\n\n\n"
        "class Migration(migrations.Migration):\n"
        f"    dependencies = [\n{deps}    ]\n"
        "    operations = []\n"
    )


class MergeMigrationLeavesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.core = self.root / "core" / "migrations"
        self.core.mkdir(parents=True)
        (self.core / "__init__.py").write_text("")
        migration(self.core, "0001_initial")
        migration(self.core, "002_short_name", ("core", "0001_initial"))
        migration(self.core, "0003_upstream", ("core", "002_short_name"))

    def test_single_leaf_needs_no_merge(self):
        self.assertEqual(merge_migration_leaves.main(self.root, "v1.0.0"), [])

    def test_fork_and_upstream_leaves_are_merged(self):
        migration(self.core, "0003_fork_feature", ("core", "002_short_name"))
        migration(self.core, "0004_upstream", ("core", "0003_upstream"),
                  ("other_app", "0009_elsewhere"))
        created = merge_migration_leaves.main(self.root, "v1.2.3")
        self.assertEqual([p.name for p in created], ["0005_merge_upstream_1_2_3.py"])
        text = created[0].read_text()
        self.assertIn("('core', '0003_fork_feature')", text)
        self.assertIn("('core', '0004_upstream')", text)
        self.assertNotIn("002_short_name", text)
        compile(text, str(created[0]), "exec")
        # The merge is itself the only leaf afterwards.
        self.assertEqual(merge_migration_leaves.main(self.root, "v1.2.3"), [])

    def test_other_apps_with_same_migration_names_are_ignored(self):
        migration(self.core, "0003_fork_feature", ("core", "002_short_name"),
                  ("accounts", "0001_initial"), ("accounts", "0003_upstream"))
        created = merge_migration_leaves.main(self.root, "v1.2.3")
        text = created[0].read_text()
        self.assertIn("('core', '0003_fork_feature')", text)
        self.assertIn("('core', '0003_upstream')", text)

    def test_frontend_dependencies_are_ignored(self):
        modules = self.root / "frontend" / "node_modules" / "x" / "migrations"
        modules.mkdir(parents=True)
        (modules / "0001_a.py").write_text("not python (")
        self.assertEqual(merge_migration_leaves.main(self.root, "v1.0.0"), [])


if __name__ == "__main__":
    unittest.main()
