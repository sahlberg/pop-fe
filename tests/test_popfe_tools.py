import sys
import unittest
from pathlib import Path

from popfe_runtime import RuntimePaths


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class BackendToolIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.runtime = RuntimePaths.detect(
            platform=sys.platform,
            frozen=False,
            source_file=REPOSITORY_ROOT / "pop-fe.py",
            executable=sys.executable,
            cwd=Path("/"),
        )

    def test_required_repository_resources_resolve_outside_project_cwd(self):
        self.assertEqual(
            self.runtime.resource_path("PS3LOGO.DAT", required=True),
            REPOSITORY_ROOT / "PS3LOGO.DAT",
        )
        self.assertTrue(
            self.runtime.resource_path(
                "pspconfigs/Neo Planet/SLPS-00323.bin",
                required=True,
            ).is_file()
        )

    def test_python_helpers_use_absolute_repository_paths(self):
        sign_command = self.runtime.tool_command("sign3", "image.bin")
        cue_command = self.runtime.tool_command("cue2cu2", "image.cue")

        self.assertEqual(Path(sign_command[0]), Path(sys.executable).resolve())
        self.assertEqual(Path(sign_command[1]), REPOSITORY_ROOT / "sign3.py")
        self.assertEqual(
            Path(cue_command[1]),
            REPOSITORY_ROOT / "Cue2cu2" / "cue2cu2.py",
        )
        self.assertTrue(all(Path(path).is_absolute() for path in sign_command[:2]))
        self.assertTrue(all(Path(path).is_absolute() for path in cue_command[:2]))

    def test_backend_has_no_direct_conversion_helper_commands(self):
        source = (REPOSITORY_ROOT / "pop-fe.py").read_text(encoding="utf-8")
        deprecated_commands = (
            "['./atracdenc",
            "['ffmpeg'",
            "['ffmpeg.exe'",
            "['python3', './sign3.py'",
            "['python3','PSL1GHT/tools/ps3py/pkg.py'",
            "['pkg.exe'",
            "['xdelta3'",
            "['python3', 'Cue2cu2/cue2cu2.py'",
            "['chdman'",
            "['python3', 'binmerge/binmerge'",
            "['./lcp'",
            "['lcp.exe'",
            "['./psx-undither/build/psxund'",
            "['psxund.exe'",
        )

        for command in deprecated_commands:
            with self.subTest(command=command):
                self.assertNotIn(command, source)

    def test_cli_uses_runtime_workspace_instead_of_current_directory(self):
        source = (REPOSITORY_ROOT / "pop-fe.py").read_text(encoding="utf-8")
        self.assertIn(
            "popfe_runtime.application_work_dir('cli', 'pop-fe-work')",
            source,
        )
        self.assertIn("popfe_runtime.remove_work_dir(work_dir)", source)
        self.assertNotIn("subdir = 'pop-fe-work/'", source)
        self.assertNotIn("os.unlink('NORMAL01.iso')", source)

    def test_retroarch_thumbnail_runs_before_pbp_mutates_images(self):
        source = (REPOSITORY_ROOT / "pop-fe.py").read_text(encoding="utf-8")
        thumbnail = "if args.retroarch_thumbnail_dir:"
        pbp = "if args.retroarch_pbp_dir:"
        self.assertLess(source.index(thumbnail), source.index(pbp))


if __name__ == "__main__":
    unittest.main()
