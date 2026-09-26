"""Verify configurable BOTW patches against local ExeFS and execute ARM64 regression cases."""
import argparse
import hashlib
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from modules.GameManager.ExefsPatch import load_patch, verify_main, module_patches, encode_ipswitch
from modules.GameManager.BotwNativePatch import build_patch, STATE


def image(path):
    import lz4.block
    raw = path.read_bytes()
    flags = struct.unpack_from("<I", raw, 0xc)[0]
    _, data_address, data_size, bss_size = struct.unpack_from("<4I", raw, 0x30)
    memory = bytearray((data_address + data_size + bss_size + 0xfff) & ~0xfff)
    for index in range(3):
        offset, address, size = struct.unpack_from("<III", raw, 0x10+16*index)
        stored = struct.unpack_from("<I", raw, 0x60+4*index)[0] if flags & (1 << index) else size
        data = raw[offset:offset+stored]
        if flags & (1 << index):
            data = lz4.block.decompress(data, uncompressed_size=size)
        assert len(data) == size
        if flags & (1 << (index+3)):
            assert hashlib.sha256(data).digest() == raw[0xa0+32*index:0xc0+32*index]
        memory[address:address+size] = data
    return memory


def patched_image(original, patch):
    memory = bytearray(original)
    for item in patch["patches"]:
        address = int(item["offset"], 0)
        expected = bytes.fromhex(item["expected"])
        assert memory[address:address+len(expected)] == expected, item["description"]
    # Exercise the actual exported text format with its explicit header shift.
    prefixed = bytearray(0x100) + memory
    shift = 0
    enabled = False
    for line in encode_ipswitch(patch).decode().splitlines():
        if line.startswith("@flag offset_shift "):
            shift = int(line.split()[-1], 0)
        elif line == "@enabled":
            enabled = True
        elif line == "@stop":
            break
        elif line and not line.startswith("@") and enabled:
            offset, value = line.split()
            address = int(offset, 16) + shift
            data = bytes.fromhex(value)
            prefixed[address:address+len(data)] = data
    return prefixed[0x100:]


def verify(main_path, sdk_path):
    from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
    from unicorn.arm64_const import (UC_ARM64_REG_PC, UC_ARM64_REG_SP, UC_ARM64_REG_LR,
                                    UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X8,
                                    UC_ARM64_REG_X19, UC_ARM64_REG_X20, UC_ARM64_REG_X21,
                                    UC_ARM64_REG_X22, UC_ARM64_REG_X29,
                                    UC_ARM64_REG_S0, UC_ARM64_REG_NZCV)
    folder = ROOT / "src/PatchInfo/Breath Of The Wild"
    base = load_patch(folder / "FPS-1.9.json")
    verify_main(base, main_path)
    main_image = image(main_path)
    sdk_patch = module_patches(build_patch(base, folder / "NativeFPS-1.9.json"))[1]
    verify_main(sdk_patch, sdk_path)
    sdk_image = image(sdk_path)
    sdk_patched = patched_image(sdk_image, sdk_patch)
    # Both caves are alignment padding, outside the game's actual code/BSS.
    raw = main_path.read_bytes()
    assert struct.unpack_from("<I", raw, 0x18)[0] == 0x15a1c64
    mod0 = struct.unpack_from("<I", main_image, 4)[0]
    assert mod0 + struct.unpack_from("<i", main_image, mod0+8)[0] == 0x1db2200
    assert not any(main_image[0x15a1c64:0x15a2000])
    assert not any(main_image[0x1db21d8:0x1db2200])

    obj, stack, stop = 0x4000000, 0x500f000, 0x6000000

    def machine(memory, base_address=0):
        uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        uc.mem_map(base_address, len(memory))
        uc.mem_write(base_address, bytes(memory))
        uc.mem_map(obj, 0x10000)
        uc.mem_map(0x5000000, 0x100000)
        uc.mem_map(stop, 0x1000)
        return uc

    preserved = (UC_ARM64_REG_X19, UC_ARM64_REG_X20, UC_ARM64_REG_X21,
                 UC_ARM64_REG_X22, UC_ARM64_REG_X29)

    def run(uc, address, endpoint=stop):
        uc.reg_write(UC_ARM64_REG_SP, stack)
        uc.reg_write(UC_ARM64_REG_LR, stop)
        for index, reg in enumerate(preserved):
            uc.reg_write(reg, 0x1000+index)
        uc.emu_start(address, endpoint, count=4000)
        assert uc.reg_read(UC_ARM64_REG_PC) == endpoint
        assert uc.reg_read(UC_ARM64_REG_SP) == stack
        for index, reg in enumerate(preserved):
            assert uc.reg_read(reg) == 0x1000+index

    # Reproduce the native-window minimum that prevented the first 45 FPS test.
    for memory, patched in ((sdk_image, False), (sdk_patched, True)):
        for requested in (0, 1, 2, 3):
            uc = machine(memory)
            uc.mem_write(obj+0x4c, struct.pack("<II", 1, 3))
            uc.reg_write(UC_ARM64_REG_X0, obj)
            uc.reg_write(UC_ARM64_REG_X1, requested)
            run(uc, 0x19cc50)
            actual = struct.unpack("<I", uc.mem_read(obj+0xf24, 4))[0]
            assert actual == (requested if patched else max(1, requested))
    print("PASS: SDK minimum-interval regression (8 cases)")

    for fps, address_base in [(v, 0) for v in (20, 30, 40, 45, 60, 90, 120)] + [(45, 0x71000000)]:
        patch = build_patch(base, folder / "NativeFPS-1.9.json", fps=fps)
        memory = patched_image(main_image, patch)
        uc = machine(memory, address_base)
        clock = {"ticks": 19200000, "sleeps": []}

        def system_call(uc, address, size, _):
            address -= address_base
            if address == 0x159ff00:
                uc.reg_write(UC_ARM64_REG_X0, clock["ticks"])
            elif address == 0x15a0c20:
                uc.reg_write(UC_ARM64_REG_X0, 19200000)
            elif address == 0x15a0a10:
                ticks = uc.reg_read(UC_ARM64_REG_X0)
                uc.reg_write(UC_ARM64_REG_X0, (ticks*1000000000+19199999)//19200000)
            elif address == 0x15a0a00:
                ns = uc.reg_read(UC_ARM64_REG_X0)
                clock["sleeps"].append(ns)
                clock["ticks"] += max(1, (ns*19200000+999999999)//1000000000)
            else:
                return
            uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_LR))

        uc.hook_add(UC_HOOK_CODE, system_call)
        # Initialize the VFR object's pointer tables as its constructor does.
        # The first table exposes the current-frame values for this test thread.
        for table, target in ((0xf0, 0x8c), (0x60, 0x3c), (0x108, 0x98), (0x120, 0xa4), (0x138, 0xb0)):
            for thread in range(3):
                uc.mem_write(obj+table+8*thread, struct.pack("<Q", obj+target))
        uc.mem_write(obj+0x158, struct.pack("<f", 1/30))
        run(uc, address_base+0x15a1c80)
        for _ in range(10):
            previous = clock["ticks"]
            clock["ticks"] += 10000
            run(uc, address_base+0x15a1c80)
            assert abs(clock["ticks"] - previous - 19200000//fps) <= 1
            ratio = struct.unpack("<f", uc.mem_read(address_base+STATE+8, 4))[0]
            assert abs(ratio - 30/fps) < 1e-5
            uc.mem_write(obj+0x150, struct.pack("<I", 2))
            uc.reg_write(UC_ARM64_REG_X0, obj)
            uc.reg_write(UC_ARM64_REG_X1, 1)
            run(uc, address_base+0x151d3d0)
            assert abs(struct.unpack("<f", uc.mem_read(obj+0x3c, 4))[0] - 30/fps) < 1e-5
        # Half-speed and paused categories remain native VFR behavior.
        for scale in (0.0, 0.5, 1.0):
            uc.mem_write(obj+0x78, struct.pack("<I", 1))
            uc.mem_write(obj+0x80, struct.pack("<Q", obj+0x2000))
            uc.mem_write(obj+0x88, struct.pack("<I", 1))
            uc.mem_write(obj+0x2000, struct.pack("<IffI", 1, scale, scale, 0))
            uc.reg_write(UC_ARM64_REG_X0, obj)
            uc.reg_write(UC_ARM64_REG_X1, 1)
            run(uc, address_base+0x151d3d0)
            # Native VFR clamps category multipliers to 0.01, even when zero
            # is requested. Preserve that behavior rather than inventing a pause.
            factor = max(0.01, scale)
            assert abs(struct.unpack("<f", uc.mem_read(obj+0x8c, 4))[0] - factor) < 1e-5
            assert abs(struct.unpack("<f", uc.mem_read(obj+0x98, 4))[0] - factor*30/fps) < 1e-5
            assert abs(struct.unpack("<f", uc.mem_read(obj+0xb0, 4))[0] - factor/fps) < 1e-5
        for elapsed in (1920000, 19200000):
            clock["ticks"] += elapsed
            sleeps = len(clock["sleeps"])
            run(uc, address_base+0x15a1c80)
            assert len(clock["sleeps"]) == sleeps
            assert abs(struct.unpack("<f", uc.mem_read(address_base+STATE+8, 4))[0]-3) < 1e-5
        print(f"PASS: {fps} FPS @ {address_base:#x}, pacing, VFR, pause/categories, stalls, register/stack preservation")

    for fov in (20, 50, 65, 90, 120):
        patch = build_patch(base, folder / "NativeFPS-1.9.json", fov=fov, far_clip=5000)
        memory = patched_image(main_image, patch)
        for source_fov in (2, 10, 50, 100):
            uc = machine(memory)
            uc.reg_write(UC_ARM64_REG_X8, obj)
            uc.reg_write(UC_ARM64_REG_S0, struct.unpack("<I", struct.pack("<f", math.radians(source_fov)))[0])
            uc.reg_write(UC_ARM64_REG_NZCV, 0xA0000000)
            run(uc, 0xc2dbbc, 0xc2dbc0)
            result = struct.unpack("<f", uc.mem_read(obj+0x74, 4))[0]
            expected = source_fov if fov == 50 else min(120, max(5, source_fov*fov/50))
            assert abs(math.degrees(result)-expected) < 1e-4
            assert uc.reg_read(UC_ARM64_REG_X8) == obj
            assert uc.reg_read(UC_ARM64_REG_NZCV) == 0xA0000000
            run(uc, 0xc2dbd0, 0xc2dbd4)
            assert struct.unpack("<f", uc.mem_read(obj+0x70, 4))[0] == 5000
    print("PASS: world camera FOV/zoom/clamps and far plane (20 input combinations)")
    for distance in (1000, 5000, 12500, 25000, 35000):
        patch = build_patch(base, folder / "NativeFPS-1.9.json", far_clip=distance)
        uc = machine(patched_image(main_image, patch))
        uc.reg_write(UC_ARM64_REG_X8, obj)
        uc.reg_write(UC_ARM64_REG_S0, struct.unpack("<I", struct.pack("<f", 24000))[0])
        run(uc, 0xc2dbd0, 0xc2dbd4)
        expected = 24000 if distance == 25000 else distance
        assert struct.unpack("<f", uc.mem_read(obj+0x70, 4))[0] == expected
    print("PASS: original Render Distance presets, including DEFAULT passthrough and experimental 35000")
    print("CPU tests supplement, but do not replace, gameplay verification.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--sdk", type=Path)
    args = parser.parse_args()
    if not __debug__:
        parser.error("Run without -O: verification uses assertions")
    verify(args.main, args.sdk or args.main.with_name("sdk"))
