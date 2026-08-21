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

    def test_application_specs_bundle_all_resources_and_helpers(self):
        common = (MACOS_PACKAGING / "spec_common.py").read_text(
            encoding="utf-8"
        )
        for helper in self.locked_helper_outputs():
            with self.subTest(helper=helper):
                self.assertIn(f'"{helper}"', common)
        for resource in (
            "libcrypt",
            "ppf",
            "ps3configs",
            "pspconfigs",
            "romhacks",
        ):
            with self.subTest(resource=resource):
                self.assertIn(f'"{resource}"', common)
        self.assertNotIn('collect_all("tkinterdnd2")', common)
        self.assertNotIn("collect_submodules", common)
        self.assertIn('collect_data_files("pytubefix"', common)
        self.assertIn('node_root / "bin" / "node"', common)
        runtime_requirements = (
            MACOS_PACKAGING / "requirements-runtime.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("nodejs-wheel-binaries==24.19.0", runtime_requirements)

    def test_gui_specs_are_arm64_macos_14_application_bundles(self):
        for filename, identifier in (
            ("pop-fe-psp.spec", "io.github.sahlberg.pop-fe.psp"),
            ("pop-fe-ps3.spec", "io.github.sahlberg.pop-fe.ps3"),
        ):
            source = (MACOS_PACKAGING / filename).read_text(encoding="utf-8")
            with self.subTest(spec=filename):
                self.assertIn('target_arch="arm64"', source)
                self.assertIn("BUNDLE(", source)
                self.assertIn(identifier, source)
        common = (MACOS_PACKAGING / "spec_common.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"LSMinimumSystemVersion": "14.0"', common)
        self.assertIn('"LSArchitecturePriority": ["arm64"]', common)

    def test_application_build_prefers_pyenv_python_with_tk(self):
        source = (MACOS_PACKAGING / "build-apps.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("pyenv prefix", source)
        self.assertIn("3.12.13", source)
        self.assertIn("import tkinter", source)
        self.assertIn("tkinter.TkVersion < 8.6", source)
        self.assertIn('rm -rf "$DIST_ROOT/Pop-FE PSP"', source)
        self.assertIn("popfe_build_version.py", source)
        self.assertIn('POPFE_VERSION="$VERSION"', source)

    def test_application_smoke_exercises_cli_both_guis_and_signatures(self):
        source = (MACOS_PACKAGING / "smoke-apps.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('"$CLI" --help', source)
        self.assertIn('node" --version', source)
        self.assertEqual(source.count("POPFE_GUI_SMOKE_TEST=1"), 2)
        self.assertEqual(source.count("codesign --verify --deep --strict"), 2)

    def test_cli_is_a_versioned_single_file_executable(self):
        spec = (MACOS_PACKAGING / "pop-fe-cli.spec").read_text(encoding="utf-8")
        source = (REPOSITORY_ROOT / "pop-fe.py").read_text(encoding="utf-8")
        self.assertIn("a.binaries", spec)
        self.assertIn("a.datas", spec)
        self.assertNotIn("COLLECT(", spec)
        self.assertIn("popfe_build_version", source)
        self.assertIn("action='version'", source)
        for gui_spec in ("pop-fe-psp.spec", "pop-fe-ps3.spec"):
            with self.subTest(spec=gui_spec):
                self.assertIn(
                    'GENERATED = ROOT / "build" / "macos" / "generated"',
                    (MACOS_PACKAGING / gui_spec).read_text(encoding="utf-8"),
                )

    def test_dmg_scripts_sign_stage_and_smoke_every_target(self):
        sign = (MACOS_PACKAGING / "sign-apps.sh").read_text(encoding="utf-8")
        create = (MACOS_PACKAGING / "create-dmg.sh").read_text(encoding="utf-8")
        smoke = (MACOS_PACKAGING / "smoke-dmg.sh").read_text(encoding="utf-8")
        readme = (MACOS_PACKAGING / "README-macOS.txt").read_text(
            encoding="utf-8"
        )
        installer = (MACOS_PACKAGING / "Install CLI.command").read_text(
            encoding="utf-8"
        )

        self.assertIn('codesign --force --sign - --timestamp=none "$target"', sign)
        self.assertEqual(sign.count("codesign --verify --deep --strict"), 2)
        self.assertIn("hdiutil create", create)
        self.assertIn("shasum -a 256", create)
        self.assertIn("Applications", create)
        self.assertIn("hdiutil attach", smoke)
        self.assertIn("hdiutil detach", smoke)
        self.assertEqual(smoke.count("POPFE_GUI_SMOKE_TEST=1"), 2)
        self.assertIn("Privacy & Security", readme)
        self.assertIn("Open Anyway", readme)
        self.assertNotIn("xattr", readme)
        self.assertIn("$HOME/.local/bin", installer)
        self.assertNotIn("sudo", installer)

    def test_python_requirements_are_exactly_pinned(self):
        requirement_files = (
            MACOS_PACKAGING / "requirements-build.txt",
            MACOS_PACKAGING / "requirements-runtime.txt",
        )
        for requirement_file in requirement_files:
            with self.subTest(requirements=requirement_file.name):
                requirements = [
                    line.strip()
                    for line in requirement_file.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.startswith("#")
                ]
                self.assertTrue(requirements)
                self.assertTrue(all("==" in line for line in requirements))

    @staticmethod
    def locked_helper_outputs():
        lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        return sorted(
            dependency["output"]
            for dependency in lock["dependencies"].values()
            if "output" in dependency
        )


if __name__ == "__main__":
    unittest.main()
