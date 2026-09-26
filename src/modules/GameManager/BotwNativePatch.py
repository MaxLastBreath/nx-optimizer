"""Configurable BOTW 1.9 patches. Runtime generation uses only the standard library."""
import copy
import json
import math
from pathlib import Path
import struct

from modules.GameManager.ExefsPatch import encode_ips32

MOD_NAME = "!!!BOTW 1.9.0 Optimizer"
FPS_CONFIG = 0x015A1FC0
STATE = 0x01DB21E0


def emulator_graphics(emulator, scale="Keep current"):
    """Explicit enum mapping; no changes for settings left at Keep current."""
    if scale not in ("Keep current", "1x", "2x", "3x", "4x"):
        raise ValueError("Unknown emulator resolution scale")
    settings = {}
    if emulator.lower() == "ryujinx":
        if scale != "Keep current":
            settings["res_scale"] = int(scale[:-1])
    else:
        # Current Eden includes both 1/4x and 1.25x entries. Original Yuzu's
        # integer scale indices are different; scale - 1 is not an enum index.
        scales = {"1x": 3, "2x": 6, "3x": 7, "4x": 8} if "eden" in emulator.lower() else {
            "1x": 2, "2x": 4, "3x": 5, "4x": 6,
        }
        if scale != "Keep current":
            settings["resolution_setup"] = str(scales[scale])
    return settings


def branch(source, destination, link=True):
    distance = destination - source
    if distance % 4 or not -(1 << 27) <= distance < (1 << 27):
        raise ValueError("ARM64 branch is unaligned or out of range")
    return struct.pack("<I", (0x94000000 if link else 0x14000000) | ((distance // 4) & 0x03FFFFFF))


def record(offset, expected, replacement, description):
    return {"offset": f"0x{offset:08X}", "expected": expected.hex().upper(),
            "replacement": replacement.hex().upper(), "description": description}


def build_patch(base_patch, payload_path, fps=60, far_clip=25000, fov=50):
    if isinstance(fps, bool) or not isinstance(fps, int) or not 20 <= fps <= 120:
        raise ValueError("FPS must be an integer between 20 and 120")
    if isinstance(far_clip, bool) or not isinstance(far_clip, int) or not 1000 <= far_clip <= 35000:
        raise ValueError("Far clip must be an integer between 1000 and 35000")
    if isinstance(fov, bool) or not isinstance(fov, int) or not 20 <= fov <= 120:
        raise ValueError("FOV must be an integer between 20 and 120")
    if base_patch["build_id"] != "CD57B23FA4BBAD65803D9788C01821EE00000000000000000000000000000000":
        raise ValueError("The native payload supports only the verified BOTW 1.9.0 Build ID")
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    result = copy.deepcopy(base_patch)
    result["mod_name"] = MOD_NAME
    result["fps"] = fps
    result["settings"] = {"fps": fps, "far_clip": far_clip, "fov": fov}
    result["timing"] = "dynamic"
    result["status"] = "experimental - 45 FPS, normal game speed and wider FOV confirmed by user in Eden; broader physics/cutscene and other FPS testing pending"
    # Timer interval stays at 1. Disable NVN's integer-vblank cap so e.g. 45 FPS
    # is controlled by our clock-based limiter rather than rounded to 30 FPS.
    for item in result["patches"]:
        if int(item["offset"], 0) in (0x11269D8, 0x1126A08):
            item["replacement"] = "01008052"  # mov w1, #0
            item["description"] = "Uncapped presentation; custom clock-based limiter controls frame pacing."
    result["patches"].extend([
        record(0x112699C, bytes.fromhex("59E51194"), branch(0x112699C, 0x15A1C80),
               "Run the limiter once at the end of each framework frame."),
        record(0x151D484, bytes.fromhex("2020201E"), branch(0x151D484, 0x15A1E00),
               "Use measured elapsed time in the native VFR update before category multipliers."),
        record(FPS_CONFIG, bytes(20), struct.pack("<Iffff", fps, fov / 50, far_clip,
                                               math.radians(5), math.radians(120)),
               "FPS, FOV gain, far clip and FOV clamp parameters in unused text padding."),
    ])
    for block in payload["blocks"]:
        data = bytes.fromhex(block["replacement"])
        result["patches"].append(record(int(block["offset"], 0), bytes(len(data)), data,
                                         f"Native payload: {block['name']}"))
    if far_clip != 25000:
        result["patches"].append(record(0xC2DBD0, bytes.fromhex("007100BD"), branch(0xC2DBD0, 0x15A1EC0),
                                         "Override the active world camera's far clip, not shared constants or LOD distances."))
    if fov != 50:
        result["patches"].append(record(0xC2DBBC, bytes.fromhex("007500BD"), branch(0xC2DBBC, 0x15A1E80),
                                         "Scale the active world camera's FOV while retaining its relative zoom."))
    result["modules"] = [{
        "name": "sdk",
        "build_id": "574284B40C06CF1821A44857939083BEE5716820000000000000000000000000",
        "main_sha256": "1d187f29784cd0af46e9e123fc2a62c77b3b07c5a39c8633d90d6c80de64e4ad",
        "patches": [record(0x19CC64, bytes.fromhex("08240FB9"), bytes.fromhex("01240FB9"),
                           "Honor the requested native-window interval, including zero, instead of clamping to minimum vsync.")],
    }]
    encode_ips32(result)
    return result
