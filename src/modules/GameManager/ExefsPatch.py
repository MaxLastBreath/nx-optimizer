"""Build-ID-scoped IPSwitch/IPS32 patches, independent of the GUI."""
import hashlib
import json
from pathlib import Path
import re
import struct


NSO_HEADER_SIZE = 0x100


def load_patch(path):
    with open(path, encoding="utf-8") as file:
        patch = json.load(file)
    if not re.fullmatch(r"[0-9A-Fa-f]{64}", patch["build_id"]):
        raise ValueError("A full NSO Build ID is required")
    if not re.fullmatch(r"[0-9A-Fa-f]{64}", patch["main_sha256"]):
        raise ValueError("A main SHA-256 is required")
    name = patch["mod_name"]
    if not name or name in (".", "..") or any(c in name for c in '/\\:'):
        raise ValueError("Invalid mod folder name")
    # Validate all records before producing any output.
    encode_ips32(patch)
    return patch


def encode_ips32(patch):
    """Offsets in the manifest are NSO memory offsets, without its 0x100 header."""
    result = bytearray(b"IPS32")
    previous_end = NSO_HEADER_SIZE
    records = sorted(patch["patches"], key=lambda item: int(item["offset"], 0))
    if not records:
        raise ValueError("Empty ExeFS patch")
    for item in records:
        offset = int(item["offset"], 0) + NSO_HEADER_SIZE
        expected = bytes.fromhex(item["expected"])
        replacement = bytes.fromhex(item["replacement"])
        if not expected or len(expected) != len(replacement):
            raise ValueError("Patch must replace an equal, nonzero number of bytes")
        if offset < previous_end or offset + len(replacement) > 0x100000000:
            raise ValueError("Overlapping or out-of-range patch offset")
        if len(replacement) > 0xffff or offset == int.from_bytes(b"EEOF", "big"):
            raise ValueError("Record cannot be represented in IPS32")
        result.extend(struct.pack(">IH", offset, len(replacement)))
        result.extend(replacement)
        previous_end = offset + len(replacement)
    result.extend(b"EEOF")
    return bytes(result)


def encode_ipswitch(patch):
    """Emit IPSwitch with memory-relative addresses and an explicit NSO shift.

    Eden nightly 5f142c7926 reported applying the IPS32 export but left the
    instructions unchanged in guest memory. This text format was confirmed
    working in the same game/build at 60 FPS.
    """
    encode_ips32(patch)  # Share range, size and overlap validation.
    build_id = patch["build_id"].upper()
    if not re.fullmatch(r"[0-9A-F]{64}", build_id):
        raise ValueError("A full NSO Build ID is required")
    lines = [f"@nsobid-{build_id}", "", "@flag offset_shift 0x100", "", "@enabled"]
    for item in sorted(patch["patches"], key=lambda item: int(item["offset"], 0)):
        replacement = bytes.fromhex(item["replacement"]).hex().upper()
        lines.append(f"{int(item['offset'], 0):08X} {replacement}")
    lines.extend(["@stop", ""])
    return "\n".join(lines).encode("ascii")


def module_patches(patch):
    """Yield independently Build-ID-scoped patches for main and companion NSOs."""
    result = [patch] + [patch | module for module in patch.get("modules", [])]
    identifiers = set()
    for module in result:
        identifier = module["build_id"].upper()
        if not re.fullmatch(r"[0-9A-F]{64}", identifier) or identifier in identifiers:
            raise ValueError("Invalid or duplicate module Build ID")
        identifiers.add(identifier)
    return result


def verify_main(patch, main_path):
    """Check the exact executable used for the port, without needing game keys."""
    with open(main_path, "rb") as file:
        header = file.read(NSO_HEADER_SIZE)
        if len(header) != NSO_HEADER_SIZE or header[:4] != b"NSO0":
            raise ValueError("Expected an extracted ExeFS main (NSO0), not an NSP or RomFS")
        build_id = header[0x40:0x60].hex().upper()
        if build_id != patch["build_id"].upper():
            raise ValueError(f"Unsupported Build ID {build_id}; this patch requires BOTW {patch['version']}")
        file.seek(0)
        hasher = hashlib.sha256()
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
        digest = hasher.hexdigest()
        if digest != patch["main_sha256"].lower():
            raise ValueError("Build ID matches, but main differs from the executable used for this port")
    return build_id


def export_patch(patch, destination, patch_format="pchtxt"):
    """Export one format and migrate only an exact copy of our previous format."""
    encoders = {"pchtxt": encode_ipswitch, "ips": encode_ips32}
    if patch_format not in encoders:
        raise ValueError(f"Unknown patch format: {patch_format}")
    destination = Path(destination)
    exefs = destination / "exefs"
    other_format = "ips" if patch_format == "pchtxt" else "pchtxt"
    outputs = []
    # Validate every module and migration before changing any files.
    for module in module_patches(patch):
        build_id = module["build_id"].upper()
        encoded = encoders[patch_format](module)
        previous = exefs / f"{build_id}.{other_format}"
        if previous.exists() and previous.read_bytes() != encoders[other_format](module):
            raise ValueError(f"{previous} differs from the generated patch; use a separate output folder")
        outputs.append((exefs / f"{build_id}.{patch_format}", encoded, previous))
    exefs.mkdir(parents=True, exist_ok=True)
    for output, encoded, previous in outputs:
        output.write_bytes(encoded)
        if previous.exists():
            previous.unlink()
    if patch.get("timing") == "dynamic":
        timing_notes = (
            f"Clock-based limit: {patch['fps']} FPS. Native simulation time uses\n"
            "measured frame duration, with long loading stalls clamped to 100 ms.\n"
            f"Graphics settings: {json.dumps(patch['settings'], sort_keys=True)}\n"
            "Both the main and SDK patch files must be enabled.\n"
            f"Emulator settings: {json.dumps(patch.get('emulator_settings', {}), sort_keys=True)}\n"
            "Emulator settings are written by Apply, not by an extracted mod.\n"
        )
        validation_notes = (
            "Validated with executable hashes and ARM64 tests of the limiter,\n"
            "native timing and register preservation. The user confirmed 45 FPS\n"
            "with normal game speed and a wider FOV in Eden after the SDK fix.\n"
            "Physics/cutscenes, far-distance effects and other FPS targets still\n"
            "require broader gameplay testing.\n"
        )
    else:
        timing_notes = (
            "This is a fixed 60 FPS patch using the game's native timing. It does\n"
            "not include UltraCam, graphics changes or arbitrary/dynamic FPS.\n"
            "Sustained 60 FPS is required for the intended game speed.\n"
        )
        validation_notes = (
            "Validated: executable hash, original instructions, both patched ARM64\n"
            "setInterval entry points, native timing ratio at 60 FPS. The IPSwitch\n"
            "export was confirmed at 60 FPS by the user in Eden nightly 5f142c7926.\n"
            "Broader physics, menu and cutscene testing is still needed.\n"
        )
    (destination / "README.md").write_text(
        f"# BOTW {patch['version']} - {patch['fps']} FPS\n\n"
        f"Status: {patch['status']}.\n\n"
        f"Title ID: `{patch['title_id']}`\n\n"
        f"Build ID: `{patch['build_id']}`\n\n"
        f"Format: {'IPSwitch (.pchtxt) for Eden' if patch_format == 'pchtxt' else 'IPS32 (.ips), for Ryujinx; do not use this format with the tested Eden nightly'}.\n\n"
        "Place this mod folder in the emulator's mod directory for BOTW.\n"
        "Keep emulator speed at 100% and enable only one FPS mod. Disable the\n"
        "1.6 UltraCam / !!!BOTW Optimizer mod when playing 1.9.0.\n\n"
        + timing_notes + "Disable this mod to restore the original behavior.\n\n"
        + validation_notes,
        encoding="utf-8",
    )
    return outputs[0][0]
