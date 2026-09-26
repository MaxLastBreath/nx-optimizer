"""Execute original/patched BOTW 1.9 ARM64 routines with Unicorn (local ExeFS required)."""
import argparse
import hashlib
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from modules.GameManager.ExefsPatch import load_patch, verify_main, encode_ips32, encode_ipswitch


def verify(main_path):
    import lz4.block
    from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
    from unicorn.arm64_const import (UC_ARM64_REG_PC, UC_ARM64_REG_SP, UC_ARM64_REG_LR,
                                    UC_ARM64_REG_X0, UC_ARM64_REG_X1,
                                    UC_ARM64_REG_X19, UC_ARM64_REG_X20)

    patch = load_patch(ROOT / "src/PatchInfo/Breath Of The Wild/FPS-1.9.json")
    verify_main(patch, main_path)
    raw = main_path.read_bytes()
    flags = struct.unpack_from("<I", raw, 0xc)[0]
    memory = bytearray(0x2000000)
    for index in range(3):
        offset, address, size = struct.unpack_from("<III", raw, 0x10+16*index)
        stored_size = struct.unpack_from("<I", raw, 0x60+4*index)[0] if flags & (1 << index) else size
        data = raw[offset:offset+stored_size]
        if flags & (1 << index):
            data = lz4.block.decompress(data, uncompressed_size=size)
        assert len(data) == size
        if flags & (1 << (index+3)):
            assert hashlib.sha256(data).digest() == raw[0xa0+32*index:0xc0+32*index]
        memory[address:address+size] = data
    for record in patch["patches"]:
        offset = int(record["offset"], 0)
        expected = bytes.fromhex(record["expected"])
        assert memory[offset:offset+len(expected)] == expected, record["description"]
    # The actual game initializes VFRMgr with interval 2 (30 FPS baseline).
    assert memory[0x127e740:0x127e744] == bytes.fromhex("41008052")

    patched_memory = bytearray(memory)
    ips = encode_ips32(patch)
    cursor = 5
    while ips[cursor:cursor+4] != b"EEOF":
        offset, size = struct.unpack_from(">IH", ips, cursor)
        cursor += 6
        offset -= 0x100
        patched_memory[offset:offset+size] = ips[cursor:cursor+size]
        cursor += size

    # Independently apply the exported IPSwitch text to an NSO-header-prefixed
    # image, as Eden does. Both formats must produce identical guest code.
    text_image = bytearray(0x100) + memory
    enabled = False
    shift = 0
    records = 0
    for line in encode_ipswitch(patch).decode("ascii").splitlines():
        if line.startswith("@nsobid-"):
            assert line[8:] == patch["build_id"]
        elif line.startswith("@flag offset_shift "):
            shift = int(line.split()[-1], 0)
        elif line == "@enabled":
            enabled = True
        elif line == "@stop":
            break
        elif line and enabled:
            offset, value = line.split()
            address = int(offset, 16) + shift
            data = bytes.fromhex(value)
            text_image[address:address+len(data)] = data
            records += 1
    assert records == len(patch["patches"])
    assert text_image[0x100:] == patched_memory
    print("PASS: IPSwitch and IPS32 exports produce identical guest instructions")

    stack, obj, graphics, stop = 0x500f000, 0x4000000, 0x4002000, 0x6000000

    def machine(patched):
        uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        uc.mem_map(0, len(memory))
        uc.mem_write(0, bytes(patched_memory if patched else memory))
        uc.mem_map(obj, 0x10000)
        uc.mem_map(0x5000000, 0x100000)
        uc.mem_map(stop, 0x1000)
        uc.reg_write(UC_ARM64_REG_SP, stack)
        uc.reg_write(UC_ARM64_REG_LR, stop)
        return uc

    checks = 0
    for patched in (False, True):
        for wrapper, this in ((0x11269b8, obj), (0x11269e8, obj+0x218)):
            for requested in (1, 2, 3):
                for clamp in (0, 1):
                    uc = machine(patched)
                    timer = obj + 0x228
                    uc.mem_write(obj+0x130, struct.pack("<Q", graphics))
                    uc.mem_write(timer+0xc, struct.pack("<I", 3))
                    uc.mem_write(timer+0x3c, bytes([clamp]))
                    uc.reg_write(UC_ARM64_REG_X0, this)
                    uc.reg_write(UC_ARM64_REG_X1, requested)
                    uc.reg_write(UC_ARM64_REG_X19, 0x1919)
                    uc.reg_write(UC_ARM64_REG_X20, 0x2020)
                    uc.emu_start(wrapper, stop, count=200)
                    expected = 1 if patched else requested
                    assert struct.unpack("<I", uc.mem_read(timer+0x1c, 4))[0] == expected
                    assert uc.mem_read(graphics+0xa0, 1)[0] == expected
                    assert uc.reg_read(UC_ARM64_REG_PC) == stop
                    assert uc.reg_read(UC_ARM64_REG_SP) == stack
                    assert uc.reg_read(UC_ARM64_REG_X19) == 0x1919
                    assert uc.reg_read(UC_ARM64_REG_X20) == 0x2020
                    checks += 1
    print(f"PASS: {checks} ARM64 wrapper cases; both entry points preserve stack/registers and set matching timer/presentation intervals")

    for interval in (1, 2, 3):
        uc = machine(True)
        uc.mem_write(obj+0x150, struct.pack("<I", 2))
        uc.reg_write(UC_ARM64_REG_X0, obj)
        uc.reg_write(UC_ARM64_REG_X1, interval)
        uc.emu_start(0x151d3d0, stop, count=500)
        assert uc.reg_read(UC_ARM64_REG_PC) == stop
        dt = struct.unpack("<f", uc.mem_read(obj+0x30, 4))[0]
        effective = struct.unpack("<f", uc.mem_read(obj+0x3c, 4))[0]
        assert dt == effective == interval / 2
        print(f"PASS: native VFR update, interval {interval} -> delta ratio {dt}")
    print("These isolated CPU tests do not replace gameplay testing.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", type=Path, required=True)
    args = parser.parse_args()
    if not __debug__:
        parser.error("Run without -O: verification uses assertions")
    verify(args.main)
