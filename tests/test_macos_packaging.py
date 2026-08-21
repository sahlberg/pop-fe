import json
import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MACOS_PACKAGING = REPOSITORY_ROOT / "packaging" / "macos"
LOCK_FILE = MACOS_PACKAGING / "dependencies.lock.json"


class MacOSDependencyLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))

    def test_target_is_apple_silicon_macos_14_or_newer(self):
        self.assertEqual(self.lock["schema_version"], 1)
        self.assertEqual(
            self.lock["target"],
            {
                "platform": "macos",
                "architecture": "arm64",
                "minimum_version": "14.0",
            },
        )

    def test_all_runtime_helpers_are_locked(self):
        expected_outputs = {
            "atracdenc",
            "binmerge",
            "chdman",
            "cue2cu2",
            "ffmpeg",
            "lcp",
            "pkg",
            "psxund",
            "sign3",
            "xdelta3",
        }
        locked_outputs = {
            dependency["output"]
            for dependency in self.lock["dependencies"].values()
            if "output" in dependency
        }
        self.assertEqual(locked_outputs, expected_outputs)

    def test_downloaded_archives_have_sha256_and_https_urls(self):
        sha256 = re.compile(r"^[0-9a-f]{64}$")
        for name, dependency in self.lock["dependencies"].items():
            if dependency["source_type"] != "archive":
                continue
            with self.subTest(dependency=name):
                self.assertTrue(dependency["url"].startswith("https://"))
                self.assertRegex(dependency["sha256"], sha256)
                self.assertTrue(dependency["filename"])

    def test_submodules_have_immutable_revisions(self):
        revision = re.compile(r"^[0-9a-f]{40}$")
        for name, dependency in self.lock["dependencies"].items():
            if dependency["source_type"] != "git-submodule":
                continue
            with self.subTest(dependency=name):
                self.assertRegex(dependency["revision"], revision)
                self.assertTrue((REPOSITORY_ROOT / dependency["path"]).exists())

    def test_every_dependency_records_license_and_source(self):
        for name, dependency in self.lock["dependencies"].items():
            with self.subTest(dependency=name):
                self.assertTrue(dependency["license"])
                self.assertTrue(dependency["source_url"].startswith("https://"))


class MacOSBuildScriptTests(unittest.TestCase):
    def test_build_scripts_do_not_depend_on_homebrew(self):
        source = (MACOS_PACKAGING / "build-helpers.sh").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("/opt/homebrew", source)
        self.assertNotIn("brew install", source)

    def test_verifier_rejects_homebrew_and_temporary_paths(self):
        source = (MACOS_PACKAGING / "verify-mach-o.sh").read_text(
            encoding="utf-8"
        )
        for forbidden_path in (
            "/opt/homebrew",
            "/usr/local",
            "/private/tmp",
            "/Users/",
        ):
            with self.subTest(path=forbidden_path):
                self.assertIn(forbidden_path, source)
        self.assertIn('otool -l "$candidate"', source)

    def test_python_extensions_have_local_rpaths_removed_before_freezing(self):
        source = (MACOS_PACKAGING / "build-helpers.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("strip_local_rpaths", source)
        self.assertIn("install_name_tool -delete_rpath", source)
        self.assertIn('verify-mach-o.sh" "$pkgcrypt_extension"', source)

    def test_python_312_compatibility_patch_uses_setuptools(self):
        patch = (
            MACOS_PACKAGING / "patches" / "ps3py-setuptools.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("from setuptools import setup, Extension", patch)
        self.assertIn("-from distutils.core", patch)

    def test_helper_build_prefers_pyenv_and_allows_ci_override(self):
        source = (MACOS_PACKAGING / "build-helpers.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('PYTHON_BIN="${PYTHON_BIN:-}"', source)
        self.assertIn("command -v pyenv", source)
        self.assertIn("pyenv which python3", source)
        self.assertIn('sys.version_info[:2] != (3, 12)', source)
        self.assertIn('platform.machine() != "arm64"', source)


if __name__ == "__main__":
    unittest.main()
