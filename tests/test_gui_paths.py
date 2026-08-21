import tempfile
import unittest
from pathlib import Path

from popfe_gui import write_exception_log
from popfe_runtime import RuntimePaths


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class GuiPathTests(unittest.TestCase):
    def test_gui_sources_do_not_write_relative_preferences_or_theme_files(self):
        for filename in ("pop-fe-psp.py", "pop-fe-ps3.py"):
            source = (REPOSITORY_ROOT / filename).read_text(encoding="utf-8")
            with self.subTest(filename=filename):
                self.assertNotIn("with open('pop-fe-psp.config'", source)
                self.assertNotIn("with open('pop-fe-ps3.config'", source)
                self.assertNotIn("disc_id, 'pop-fe-psp-work'", source)
                self.assertIn("popfe_runtime.resource_path", source)
                self.assertIn("popfe_runtime.application_work_dir", source)
                self.assertIn("PREFERENCES_PATH", source)

    def test_gui_exception_log_uses_macos_log_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            runtime = RuntimePaths.detect(
                platform="darwin",
                frozen=False,
                source_file=REPOSITORY_ROOT / "pop-fe.py",
                executable=root / "python3",
                home=root / "home",
                environ={},
                cwd=root / "cwd",
            )

            try:
                raise RuntimeError("conversion failed")
            except RuntimeError as error:
                log_path = write_exception_log(
                    runtime,
                    "psp",
                    type(error),
                    error,
                    error.__traceback__,
                )

            self.assertEqual(log_path.parent, runtime.log_dir)
            contents = log_path.read_text(encoding="utf-8")
            self.assertIn("conversion failed", contents)
            self.assertIn("RuntimeError", contents)
            self.assertIn("Platform: darwin", contents)


if __name__ == "__main__":
    unittest.main()
