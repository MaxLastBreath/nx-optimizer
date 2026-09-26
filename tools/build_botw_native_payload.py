"""Rebuild our small ARM64 payload. Development dependency: keystone-engine."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/PatchInfo/Breath Of The Wild/NativeFPS-1.9.s"
OUTPUT = SOURCE.with_suffix(".json")


def build():
    from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
    source = SOURCE.read_text(encoding="utf-8")
    blocks = []
    for name, address, body in re.findall(
        r"// @block (\w+) (0x[0-9A-Fa-f]+)\n(.*?)(?=// @block|\Z)", source, re.S
    ):
        assembly = "\n".join(line.split("//")[0] for line in body.splitlines())
        code, _ = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN).asm(assembly, addr=int(address, 0))
        data = bytes(code)
        assert 0x15a1c80 <= int(address, 0) < int(address, 0) + len(data) <= 0x15a1fc0
        blocks.append({"name": name, "offset": address, "replacement": data.hex().upper()})
    return {"source_sha256": hashlib.sha256(source.encode()).hexdigest(), "blocks": blocks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build()
    if args.check:
        assert payload == json.loads(OUTPUT.read_text()), "Rebuild the payload after editing assembly"
    else:
        OUTPUT.write_text(json.dumps(payload, indent=4) + "\n", encoding="utf-8")
    for block in payload["blocks"]:
        print(block["name"], block["offset"], len(bytes.fromhex(block["replacement"])), "bytes")
