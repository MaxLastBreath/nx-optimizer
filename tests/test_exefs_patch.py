import copy
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from modules.GameManager.ExefsPatch import load_patch, encode_ips32, encode_ipswitch, verify_main, export_patch


class ExefsPatchTests(unittest.TestCase):
    def setUp(self):
        self.patch = load_patch(ROOT / "src/PatchInfo/Breath Of The Wild/FPS-1.9.json")

    def test_ips32_addresses_include_nso_header_and_support_offsets_over_16mb(self):
        encoded = encode_ips32(self.patch)
        self.assertEqual(encoded[:5], b"IPS32")
        self.assertEqual(encoded[-4:], b"EEOF")
        records = []
        cursor = 5
        while encoded[cursor:cursor+4] != b"EEOF":
            offset, size = struct.unpack_from(">IH", encoded, cursor)
            cursor += 6
            records.append((offset, encoded[cursor:cursor+size]))
            cursor += size
        self.assertEqual(cursor + 4, len(encoded))
        self.assertEqual(records, [
            (0x1126acc, bytes.fromhex("21008052")),
            (0x1126ad8, bytes.fromhex("21008052")),
            (0x1126afc, bytes.fromhex("21008052")),
            (0x1126b08, bytes.fromhex("21008052")),
        ])

    def test_export_is_build_id_scoped_and_keeps_other_files(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / self.patch["mod_name"]
            destination.mkdir()
            user_file = destination / "user-note.md"
            user_file.write_text("keep", encoding="utf-8")
            output = export_patch(self.patch, destination)
            self.assertEqual(output.name, self.patch["build_id"] + ".pchtxt")
            self.assertEqual(output.read_bytes(), encode_ipswitch(self.patch))
            self.assertEqual(user_file.read_text(), "keep")
            self.assertFalse((destination / "romfs").exists())
            self.assertEqual(list((destination / "exefs").iterdir()), [output])
            export_patch(self.patch, destination)
            self.assertEqual(output.read_bytes(), encode_ipswitch(self.patch))

    def test_ipswitch_has_build_id_and_exact_instructions_without_double_shift(self):
        text = encode_ipswitch(self.patch).decode("ascii")
        self.assertEqual(text.splitlines(), [
            "@nsobid-" + self.patch["build_id"], "", "@flag offset_shift 0x100", "",
            "@enabled", "011269CC 21008052", "011269D8 21008052",
            "011269FC 21008052", "01126A08 21008052", "@stop",
        ])

    def test_format_migration_removes_only_our_previous_generated_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)
            old = export_patch(self.patch, destination, "ips")
            self.assertEqual(old.read_bytes(), encode_ips32(self.patch))
            unrelated = old.parent / "other.ips"
            unrelated.write_bytes(b"user patch")
            new = export_patch(self.patch, destination)
            self.assertFalse(old.exists())
            self.assertTrue(new.exists())
            self.assertEqual(unrelated.read_bytes(), b"user patch")
            restored = export_patch(self.patch, destination, "ips")
            self.assertFalse(new.exists())
            self.assertEqual(restored.read_bytes(), encode_ips32(self.patch))

    def test_modified_previous_format_is_not_overwritten_or_deleted(self):
        with tempfile.TemporaryDirectory() as temp:
            old = export_patch(self.patch, temp, "ips")
            old.write_bytes(b"user-edited")
            with self.assertRaisesRegex(ValueError, "differs"):
                export_patch(self.patch, temp)
            self.assertEqual(old.read_bytes(), b"user-edited")
            self.assertFalse(old.with_suffix(".pchtxt").exists())

    def test_invalid_records_are_rejected_before_creating_output(self):
        invalid = []
        for field, value in (("offset", "-0x4"), ("offset", "0x100000000"),
                             ("expected", "00"), ("replacement", "")):
            patch = copy.deepcopy(self.patch)
            patch["patches"][0][field] = value
            invalid.append(patch)
        patch = copy.deepcopy(self.patch)
        patch["patches"].append(patch["patches"][0])
        invalid.append(patch)
        with tempfile.TemporaryDirectory() as temp:
            for index, patch in enumerate(invalid):
                output = Path(temp) / str(index)
                with self.subTest(index=index), self.assertRaises(ValueError):
                    export_patch(patch, output)
                self.assertFalse(output.exists())

    def test_verify_main_rejects_wrong_version_and_modified_executable(self):
        header = bytearray(0x100)
        header[:4] = b"NSO0"
        header[0x40:0x60] = bytes.fromhex(self.patch["build_id"])
        patch = copy.deepcopy(self.patch)
        patch["main_sha256"] = hashlib.sha256(header).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "main"
            main.write_bytes(header)
            self.assertEqual(verify_main(patch, main), patch["build_id"])
            main.write_bytes(header + b"modified")
            with self.assertRaisesRegex(ValueError, "differs"):
                verify_main(patch, main)
            header[0x40] ^= 1
            main.write_bytes(header)
            with self.assertRaisesRegex(ValueError, "Unsupported Build ID"):
                verify_main(patch, main)
            main.write_bytes(b"PFS0" + bytes(0xfc))
            with self.assertRaisesRegex(ValueError, "NSO0"):
                verify_main(patch, main)


if __name__ == "__main__":
    unittest.main()
