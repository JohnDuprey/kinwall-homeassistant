import tempfile
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from sync_release import image_ready, sync_release


class ReleaseSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "kinwall").mkdir()
        self.config = self.root / "kinwall/config.yaml"
        self.changelog = self.root / "kinwall/CHANGELOG.md"
        self.config.write_text('name: Kinwall\nversion: "1.2.0"\nimage: ghcr.io/johnduprey/kinwall\n')
        self.changelog.write_text("# Changelog\n\nIntro.\n\n## 1.2.0\n\nOld notes.\n")
        self.release = {
            "tag_name": "v1.3.0", "draft": False, "prerelease": False,
            "body": "## Features\n\n- A new feature.\n\n```md\n# Keep this\n```",
        }

    def sync(self, ready=True):
        with patch("sync_release.image_ready", return_value=ready) as image:
            result = sync_release(self.root, self.release)
        return result, image

    def test_updates_both_files_and_preserves_history(self):
        result, image = self.sync()
        self.assertEqual(result, "1.3.0")
        image.assert_called_once_with("1.3.0")
        self.assertIn('version: "1.3.0"', self.config.read_text())
        notes = self.changelog.read_text()
        self.assertLess(notes.index("## 1.3.0"), notes.index("## 1.2.0"))
        self.assertIn("#### Features", notes)
        self.assertIn("```md\n# Keep this\n```", notes)
        self.assertIn("compare/v1.2.0...v1.3.0", notes)
        self.assertTrue(notes.endswith("Old notes.\n"))
        self.assertIsNone(self.sync()[0])

    def test_unpublished_image_leaves_both_files_unchanged(self):
        before = (self.config.read_text(), self.changelog.read_text())
        self.assertIsNone(self.sync(ready=False)[0])
        self.assertEqual(before, (self.config.read_text(), self.changelog.read_text()))

    def test_ignores_drafts_prereleases_same_and_older_versions(self):
        for changes in ({"draft": True}, {"prerelease": True},
                        {"tag_name": "v1.3.0-rc.1"}, {"tag_name": "v1.2.0"},
                        {"tag_name": "v1.1.9"}, {"tag_name": "latest"},
                        {"tag_name": "v1.3.0\nchanged=true"}):
            with self.subTest(changes=changes):
                self.release.update(changes)
                result, image = self.sync()
                self.assertIsNone(result)
                image.assert_not_called()
                self.release = {"tag_name": "v1.3.0", "draft": False, "prerelease": False, "body": ""}

    def test_missing_notes_still_link_to_release(self):
        self.release["body"] = None
        self.sync()
        self.assertIn("releases/tag/v1.3.0", self.changelog.read_text())

    def test_compares_versions_numerically(self):
        self.config.write_text('version: "1.9.0"\n')
        self.release["tag_name"] = "v1.10.0"
        self.assertEqual(self.sync()[0], "1.10.0")

    def test_existing_changelog_entry_is_not_duplicated(self):
        self.changelog.write_text("# Changelog\n\n## 1.3.0\n\nReviewed notes.\n\n## 1.2.0\n")
        self.sync()
        self.assertEqual(self.changelog.read_text().count("## 1.3.0"), 1)
        self.assertIn("Reviewed notes.", self.changelog.read_text())

    def test_malformed_config_fails_without_changing_changelog(self):
        self.config.write_text("name: Kinwall\n")
        before = self.changelog.read_text()
        with self.assertRaises(ValueError):
            self.sync()
        self.assertEqual(before, self.changelog.read_text())


class ImageTests(unittest.TestCase):
    def test_requires_both_linux_architectures(self):
        for arches, expected in ((["amd64"], False), (["arm64"], False),
                                 (["amd64", "arm64", "unknown"], True)):
            manifests = [{"platform": {"os": "linux", "architecture": arch}} for arch in arches]
            with self.subTest(arches=arches), patch("sync_release.subprocess.run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, json.dumps({"manifests": manifests}))
                self.assertEqual(image_ready("1.3.0"), expected)

    def test_unpublished_image_is_deferred(self):
        with patch("sync_release.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 1, "", "not found")
            self.assertFalse(image_ready("1.3.0"))


if __name__ == "__main__":
    unittest.main()
