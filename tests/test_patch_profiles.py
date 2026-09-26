import configparser
import importlib
import logging
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class PatchProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Loading patch metadata must not require a monitor/GPU in these tests.
        logger = types.ModuleType("modules.logger")
        logger.log = logger.superlog = logging.getLogger("profile-tests")
        with patch.dict(sys.modules, {"modules.logger": logger}):
            cls.games = importlib.import_module("modules.GameManager.GameManager").Game_Manager
            cls.qt = importlib.import_module("modules.qt_config")

    def setUp(self):
        self.saved = self.games.GamePatches
        self.games.GamePatches = []

    def tearDown(self):
        self.games.GamePatches = self.saved

    def test_versions_have_separate_selection_and_options_but_same_title(self):
        self.games.CreatePatchInfo(ROOT / "src/PatchInfo/Breath Of The Wild")
        base = self.games.GetJsonByID("01007ef00011e000")
        newer = self.games.GetJsonByID("01007ef00011e000@1.9.0-native")
        self.assertIsNot(base, newer)
        self.assertEqual(base.ID, newer.ID)
        self.assertEqual(base.Versions, ["1.6.0"])
        self.assertEqual(newer.Versions, ["1.9.0"])
        self.assertIsNone(base.ExefsPatch)
        self.assertEqual(newer.ExefsPatch, "FPS-1.9.json")
        self.assertIn("freecam", base.LoadJson()["Keys"])
        self.assertEqual(newer.LoadJson()["NativeFPS"]["fps"]["Values"], [20, 120])
        self.assertFalse(newer.Cheats)
        self.assertFalse(newer.ResolutionScale)
        self.assertFalse(newer.Support_Benchmark)
        self.assertEqual(newer.LoadPresetsJson()["60 FPS"]["fps"], 60)

    def test_repeated_discovery_does_not_duplicate_variants(self):
        folder = ROOT / "src/PatchInfo/Breath Of The Wild"
        first = self.games.CreatePatchInfo(folder)
        self.assertIs(self.games.CreatePatchInfo(folder), first)
        self.assertEqual(len(self.games.GamePatches), 2)

    def test_retired_fixed_selection_resolves_to_the_only_19_profile(self):
        self.games.CreatePatchInfo(ROOT / "src/PatchInfo/Breath Of The Wild")
        current = self.games.GetJsonByID("01007EF00011E000@1.9.0-native")
        self.assertIs(self.games.GetJsonByID("01007ef00011e000@1.9.0-fps"), current)
        self.assertEqual([p for p in self.games.GamePatches if p.Versions == ["1.9.0"]], [current])

    def test_configurable_profile_exposes_real_native_and_emulator_settings(self):
        self.games.CreatePatchInfo(ROOT / "src/PatchInfo/Breath Of The Wild")
        configurable = self.games.GetJsonByID("01007EF00011E000@1.9.0-native")
        options = configurable.LoadJson()["NativeFPS"]
        self.assertEqual(set(options), {"fps", "fov", "render distance", "emulator scale"})
        self.assertEqual(options["emulator scale"]["Name"], "Resolution Scale")
        self.assertEqual(options["fps"]["Values"], [20, 120])
        self.assertEqual(configurable.NativePayload, "NativeFPS-1.9.json")
        self.assertIn("!!!BOTW 1.9.0 60 FPS", configurable.ConflictingMods)

    def test_render_distance_matches_original_presets(self):
        self.games.CreatePatchInfo(ROOT / "src/PatchInfo/Breath Of The Wild")
        original = self.games.GetJsonByID("01007EF00011E000").LoadJson()["Keys"]["render distance"]
        current = self.games.GetJsonByID("01007EF00011E000@1.9.0-native").LoadJson()["NativeFPS"]["render distance"]
        for key in ("Name", "Class", "Name_Values", "Values", "Default"):
            self.assertEqual(current[key], original[key])

    def test_old_far_clip_values_migrate_without_overwriting_new_choices(self):
        self.games.CreatePatchInfo(ROOT / "src/PatchInfo/Breath Of The Wild")
        profile = self.games.GetJsonByID("01007EF00011E000@1.9.0-native")
        for old, expected in (("1000", "0"), ("5000", "1"), ("12500", "2"),
                              ("25000", "3"), ("6000", "1"), ("invalid", "3"), ("nan", "3")):
            with self.subTest(old=old):
                config = configparser.ConfigParser()
                config[profile.SelectionID] = {"fps": "45", "far clip": old}
                profile.MigrateUserConfig(config, profile.LoadJson())
                self.assertEqual(config[profile.SelectionID]["render distance"], expected)
                self.assertEqual(config[profile.SelectionID]["fps"], "45")
                config[profile.SelectionID]["render distance"] = "4"
                profile.MigrateUserConfig(config, profile.LoadJson())
                self.assertEqual(config[profile.SelectionID]["render distance"], "4")

    def test_install_can_disable_old_ultracam_and_enable_new_patch(self):
        title = int("01007EF00011E000", 16)
        old, new = "!!!BOTW 1.9.0 60 FPS", "!!!BOTW 1.9.0 Optimizer"
        config = configparser.ConfigParser()
        config["DisabledAddOns"] = {
            "1\\title_id": str(title),
            "1\\disabled\\1\\d": new,
            "1\\disabled\\size": "1",
        }
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / old).mkdir()
            (directory / new).mkdir()
            config_file = directory / "qt-config.ini"
            self.qt.add_entry(config_file, directory, config, title, old)
            self.qt.find_and_remove_entry(config_file, directory, config, title, new)
            loaded = configparser.ConfigParser()
            loaded.read(config_file)
            self.assertEqual(self.qt.get_d_values(loaded, "1"), [old])
            self.assertEqual(self.qt.find_title_id_index(loaded, str(title)), "1")


if __name__ == "__main__":
    unittest.main()
