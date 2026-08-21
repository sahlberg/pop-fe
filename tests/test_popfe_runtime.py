import os
import tempfile
import unittest
from pathlib import Path

from popfe_runtime import MissingResourceError, MissingToolError, RuntimePaths


class RuntimePathsTests(unittest.TestCase):
    def make_runtime(self, root, **overrides):
        root = Path(root)
        defaults = {
            "platform": "darwin",
            "frozen": False,
            "source_file": root / "source" / "pop-fe.py",
            "executable": root / "python",
            "home": root / "home",
            "environ": {},
            "cwd": root / "working directory",
        }
        defaults.update(overrides)
        return RuntimePaths.detect(**defaults)

    def test_source_resources_are_relative_to_source_file(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.make_runtime(directory)

            self.assertEqual(
                runtime.resource_root,
                Path(directory).resolve() / "source",
            )
            self.assertEqual(
                runtime.resource_path("PS3LOGO.DAT"),
                Path(directory).resolve() / "source" / "PS3LOGO.DAT",
            )

    def test_frozen_resources_use_pyinstaller_meipass(self):
        with tempfile.TemporaryDirectory() as directory:
            resources = Path(directory) / "bundle" / "Resources"
            runtime = self.make_runtime(
                directory,
                frozen=True,
                meipass=resources,
            )

            self.assertEqual(runtime.resource_root, resources.resolve())

    def test_resource_path_rejects_escape_and_reports_missing_resource(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.make_runtime(directory)

            with self.assertRaises(ValueError):
                runtime.resource_path("../outside")
            with self.assertRaises(MissingResourceError):
                runtime.resource_path("missing.dat", required=True)

    def test_macos_user_directories_follow_platform_conventions(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.make_runtime(directory)
            home = Path(directory).resolve() / "home"

            self.assertEqual(
                runtime.config_dir,
                home / "Library" / "Application Support" / "Pop-FE",
            )
            self.assertEqual(
                runtime.log_dir,
                home / "Library" / "Logs" / "Pop-FE",
            )
            self.assertEqual(
                runtime.cache_dir,
                home / "Library" / "Caches" / "Pop-FE",
            )
            self.assertEqual(
                runtime.preference_path("pop-fe-psp.config"),
                runtime.config_dir / "pop-fe-psp.config",
            )

    def test_linux_user_directories_honor_xdg_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            runtime = self.make_runtime(
                directory,
                platform="linux",
                environ={
                    "XDG_CONFIG_HOME": str(root / "xdg-config"),
                    "XDG_STATE_HOME": str(root / "xdg-state"),
                    "XDG_CACHE_HOME": str(root / "xdg-cache"),
                },
            )

            self.assertEqual(runtime.config_dir, root / "xdg-config" / "pop-fe")
            self.assertEqual(runtime.log_dir, root / "xdg-state" / "pop-fe")
            self.assertEqual(runtime.cache_dir, root / "xdg-cache" / "pop-fe")

    def test_work_directories_are_unique_and_cleaned_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.make_runtime(directory)
            first = runtime.create_work_dir("psp")
            second = runtime.create_work_dir("psp")

            self.assertNotEqual(first, second)
            self.assertEqual(first.parent, runtime.cache_dir)
            self.assertTrue(first.is_dir())
            self.assertTrue(second.is_dir())

            runtime.remove_work_dir(first)
            self.assertFalse(first.exists())
            with self.assertRaises(ValueError):
                runtime.remove_work_dir(Path(directory))

    def test_new_log_path_is_unique_and_creates_log_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.make_runtime(directory)

            first = runtime.new_log_path("psp")
            second = runtime.new_log_path("psp")

            self.assertTrue(runtime.log_dir.is_dir())
            self.assertNotEqual(first, second)
            self.assertEqual(first.parent, runtime.log_dir)
            self.assertEqual(first.suffix, ".log")

    def test_frozen_tool_lookup_prefers_bundled_absolute_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resources = root / "resources"
            helper = resources / "tools" / "ffmpeg"
            helper.parent.mkdir(parents=True)
            helper.write_bytes(b"helper")
            helper.chmod(0o755)
            runtime = self.make_runtime(
                directory,
                frozen=True,
                meipass=resources,
            )

            resolved = runtime.tool_path(
                "ffmpeg",
                path_search=lambda _name: "/usr/local/bin/ffmpeg",
            )

            self.assertEqual(resolved, helper.resolve())
            self.assertTrue(resolved.is_absolute())

    def test_frozen_tool_lookup_never_falls_back_to_path(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.make_runtime(directory, frozen=True)

            self.assertIsNone(
                runtime.tool_path(
                    "chdman",
                    path_search=lambda _name: "/usr/local/bin/chdman",
                )
            )
            with self.assertRaises(MissingToolError):
                runtime.tool_path("chdman", required=True, path_search=lambda _: None)

    def test_source_tool_lookup_supports_repository_and_path_helpers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "source"
            helper = source_root / "atracdenc" / "src" / "atracdenc"
            helper.parent.mkdir(parents=True)
            helper.write_bytes(b"helper")
            helper.chmod(0o755)
            runtime = self.make_runtime(directory)

            self.assertEqual(runtime.tool_path("atracdenc"), helper.resolve())
            self.assertEqual(
                runtime.tool_path(
                    "xdelta3",
                    path_search=lambda name: (
                        "/opt/tools/xdelta3" if name == "xdelta3" else None
                    ),
                ),
                Path("/opt/tools/xdelta3"),
            )

    def test_tool_command_uses_runtime_python_for_source_script(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            script = root / "source" / "sign3.py"
            script.parent.mkdir(parents=True)
            script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            runtime = self.make_runtime(directory, executable=root / "python3")

            self.assertEqual(
                runtime.tool_command("sign3", "image.bin"),
                [str(root / "python3"), str(script), "image.bin"],
            )

    def test_tool_command_executes_native_helper_directly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            helper = root / "resources" / "tools" / "ffmpeg"
            helper.parent.mkdir(parents=True)
            helper.write_bytes(b"helper")
            helper.chmod(0o755)
            runtime = self.make_runtime(
                directory,
                frozen=True,
                meipass=root / "resources",
            )

            self.assertEqual(
                runtime.tool_command("ffmpeg", "-version"),
                [str(helper), "-version"],
            )

    @unittest.skipUnless(os.name == "posix", "POSIX executable mode test")
    def test_non_executable_bundle_helper_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resources = root / "resources"
            helper = resources / "tools" / "ffmpeg"
            helper.parent.mkdir(parents=True)
            helper.write_bytes(b"helper")
            helper.chmod(0o644)
            runtime = self.make_runtime(
                directory,
                frozen=True,
                meipass=resources,
            )

            with self.assertRaises(MissingToolError):
                runtime.tool_path("ffmpeg", required=True)

    def test_windows_tools_use_exe_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resources = root / "resources"
            helper = resources / "tools" / "xdelta3.exe"
            helper.parent.mkdir(parents=True)
            helper.write_bytes(b"helper")
            runtime = self.make_runtime(
                directory,
                platform="win32",
                frozen=True,
                meipass=resources,
            )

            self.assertEqual(runtime.tool_path("xdelta3"), helper.resolve())


if __name__ == "__main__":
    unittest.main()
