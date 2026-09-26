import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from modules.GameManager.BotwNativePatch import build_patch, emulator_graphics, FPS_CONFIG
from modules.GameManager.ExefsPatch import load_patch, export_patch, module_patches

FOLDER = ROOT / "src/PatchInfo/Breath Of The Wild"


class NativePatchTests(unittest.TestCase):
    def setUp(self):
        self.base = load_patch(FOLDER / "FPS-1.9.json")

    def build(self, **settings):
        return build_patch(self.base, FOLDER / "NativeFPS-1.9.json", **settings)

    def test_45fps_exports_both_required_modules(self):
        original = copy.deepcopy(self.base)
        patch = self.build(fps=45)
        self.assertEqual(self.base, original)
        self.assertEqual(patch["fps"], 45)
        self.assertEqual(len(module_patches(patch)), 2)
        records = {int(p["offset"], 0): bytes.fromhex(p["replacement"]) for p in patch["patches"]}
        self.assertEqual(struct.unpack_from("<I", records[FPS_CONFIG])[0], 45)
        self.assertEqual(records[0x11269d8], bytes.fromhex("01008052"))
        sdk = module_patches(patch)[1]
        self.assertEqual(sdk["patches"][0]["offset"], "0x0019CC64")
        self.assertEqual(sdk["patches"][0]["replacement"], "01240FB9")
        with tempfile.TemporaryDirectory() as temp:
            export_patch(patch, temp)
            files = sorted((Path(temp) / "exefs").glob("*.pchtxt"))
            self.assertEqual({f.stem for f in files}, {p["build_id"] for p in module_patches(patch)})
            self.assertIn("0019CC64 01240FB9", next(f.read_text() for f in files if f.stem == sdk["build_id"]))

    def test_camera_changes_are_optional_and_target_camera_stores(self):
        baseline = self.build()
        addresses = {int(p["offset"], 0) for p in baseline["patches"]}
        self.assertNotIn(0xc2dbbc, addresses)
        self.assertNotIn(0xc2dbd0, addresses)
        custom = self.build(fov=65, far_clip=5000)
        records = {int(p["offset"], 0): p for p in custom["patches"]}
        self.assertEqual(records[0xc2dbbc]["expected"], "007500BD")
        self.assertEqual(records[0xc2dbd0]["expected"], "007100BD")
        values = struct.unpack("<Iffff", bytes.fromhex(records[FPS_CONFIG]["replacement"]))
        self.assertAlmostEqual(values[1], 1.3, places=6)
        self.assertEqual(values[2], 5000)
        self.assertNotIn(0x16a15cc, records)  # Do not replace a shared engine constant.

    def test_invalid_settings_do_not_silently_truncate_or_clamp(self):
        for values in ({"fps": 0}, {"fps": 121}, {"fps": 45.5}, {"fps": True},
                       {"fov": 121}, {"fov": 19}, {"far_clip": 0}, {"far_clip": 50000}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.build(**values)

    def test_all_render_distance_presets_reach_the_native_parameter(self):
        options = json.loads((FOLDER / "Options-Native-1.9.json").read_text())["NativeFPS"]["render distance"]
        for distance in options["Values"]:
            with self.subTest(distance=distance):
                patch = self.build(far_clip=distance)
                records = {int(p["offset"], 0): p for p in patch["patches"]}
                values = struct.unpack("<Iffff", bytes.fromhex(records[FPS_CONFIG]["replacement"]))
                self.assertEqual(values[2], distance)
                self.assertEqual(0xc2dbd0 in records, distance != 25000)

    def test_unknown_executable_is_rejected(self):
        self.base["build_id"] = "0" * 64
        with self.assertRaises(ValueError):
            self.build()

    def test_duplicate_module_ids_are_rejected_before_writing(self):
        patch = self.build()
        patch["modules"][0]["build_id"] = patch["build_id"]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "mod"
            with self.assertRaises(ValueError):
                export_patch(patch, target)
            self.assertFalse(target.exists())

    def test_emulator_graphics_enum_mapping(self):
        self.assertEqual(emulator_graphics("eden"), {})
        self.assertEqual(emulator_graphics("eden", "2x"), {"resolution_setup": "6"})
        self.assertEqual(emulator_graphics("yuzu", "2x"), {"resolution_setup": "4"})
        self.assertEqual(emulator_graphics("ryujinx", "2x"), {"res_scale": 2})
        with self.assertRaises(ValueError):
            emulator_graphics("eden", "1.25x")


if __name__ == "__main__":
    unittest.main()
