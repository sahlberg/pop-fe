import tempfile
import unittest
from pathlib import Path

from popfe_psp_import import FolderImportError, scan_psp_folder


class PspFolderImportTests(unittest.TestCase):
    def test_cue_companion_bin_and_nested_output_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Game.cue").write_text(
                'FILE "GAME.BIN" BINARY\n  TRACK 01 MODE2/2352\n',
                encoding="utf-8",
            )
            (root / "game.bin").write_bytes(b"disc")
            nested = root / "old output"
            nested.mkdir()
            (nested / "Other.chd").write_bytes(b"disc")

            result = scan_psp_folder(root)

            self.assertEqual([path.name for path in result.discs], ["Game.cue"])

    def test_ccd_companion_img_is_not_a_second_disc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Game.ccd").write_text("[CloneCD]\n", encoding="utf-8")
            (root / "Game.img").write_bytes(b"disc")

            result = scan_psp_folder(root)

            self.assertEqual([path.name for path in result.discs], ["Game.ccd"])

    def test_disc_order_is_natural_and_single_disc_mode_uses_first(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("Disc 10.chd", "Disc 2.chd", "Disc 1.chd"):
                (root / name).write_bytes(b"disc")

            all_discs = scan_psp_folder(root)
            one_disc = scan_psp_folder(root, import_all_discs=False)

            self.assertEqual(
                [path.name for path in all_discs.discs],
                ["Disc 1.chd", "Disc 2.chd", "Disc 10.chd"],
            )
            self.assertEqual([path.name for path in one_disc.discs], ["Disc 1.chd"])

    def test_disc_limit_adds_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(1, 7):
                (root / f"Disc {index}.chd").write_bytes(b"disc")

            result = scan_psp_folder(root)

            self.assertEqual(len(result.discs), 5)
            self.assertEqual(
                result.warnings,
                ("Found 6 discs; only the first 5 were loaded.",),
            )

    def test_local_assets_are_case_insensitive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Game.chd").write_bytes(b"disc")
            for name in (
                "icon0.png",
                "Pic0.Png",
                "PIC1.PNG",
                "snd0.at3",
                "manual.pdf",
                "logo.png",
            ):
                (root / name).write_bytes(b"asset")

            result = scan_psp_folder(root)

            self.assertEqual(
                {field: path.name for field, path in result.assets.items()},
                {
                    "icon0": "icon0.png",
                    "pic0": "Pic0.Png",
                    "pic1": "PIC1.PNG",
                    "snd0": "snd0.at3",
                    "manual": "manual.pdf",
                    "logo": "logo.png",
                },
            )

    def test_unrelated_asset_names_are_not_used(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Game.chd").write_bytes(b"disc")
            (root / "BOOT.PNG").write_bytes(b"asset")
            (root / "ICON1.PMF").write_bytes(b"asset")

            result = scan_psp_folder(root)

            self.assertEqual(result.assets, {})

    def test_folder_tags_are_removed_from_fallback_title(self):
        with tempfile.TemporaryDirectory(
            prefix="[PS1] Crash Bash [E-F-G-I-S] [SCES-02834]"
        ) as directory:
            root = Path(directory)
            (root / "Game.chd").write_bytes(b"disc")

            result = scan_psp_folder(root)

            self.assertIn("Crash Bash", result.fallback_title)
            self.assertNotIn("[PS1]", result.fallback_title)
            self.assertNotIn("[SCES-02834]", result.fallback_title)

    def test_invalid_or_empty_folder_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(FolderImportError, "No supported"):
                scan_psp_folder(root)
            with self.assertRaisesRegex(FolderImportError, "does not exist"):
                scan_psp_folder(root / "missing")

    def test_same_stem_prefers_descriptor_format(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Game.cue").write_text("", encoding="utf-8")
            (root / "Game.chd").write_bytes(b"disc")

            result = scan_psp_folder(root)

            self.assertEqual([path.name for path in result.discs], ["Game.cue"])


if __name__ == "__main__":
    unittest.main()
