# BOTW 1.9.0: configurable FPS and graphics

The experimental BOTW 1.9.0 profile provides a **20-120 FPS limiter with measured frame
time**, world-camera **FOV and Render Distance**, and **Resolution Scale** for
the Switch version of BOTW 1.9.0. The user confirmed **45 FPS with normal game
speed and a visibly wider FOV** in Eden nightly `5f142c7926`.

There is one profile for 1.9.0, including 60 FPS as a selectable limit. It is
separate from UltraCam 1.6.0. Broader physics, menu, cutscene and other framerate
testing remains pending; the profile is experimental.

## Using NX Optimizer

Run from source (`python run.py` in `src`, with the dependencies from
`src/dependencies.py` installed), or use a build that includes the BOTW 1.9.0
profiles listed below.

In **Select Game**, choose:

- **Breath of The Wild**: existing UltraCam for **1.6.0**.
- **BOTW 1.9.0 - FPS + Graphics (Experimental)**: configurable FPS and graphics.

Choose **Extract** to export a standalone mod to `Extracted Files`, or **Apply**
to install it to the selected emulator. The 1.9 profile exports **IPSwitch
(`.pchtxt`) for Eden/Legacy**, or IPS32 (`.ips`) for Ryujinx, together with
instructions. There is no UltraCam executable or INI. Its selection/settings
are saved separately from the 1.6 profile.

Keep emulator speed at **100%**. Enable only one FPS mod. When using 1.9.0,
disable the old `!!!BOTW Optimizer` / UltraCam mod (Apply requests this through
the emulator's existing mod configuration). Check this manually when installing
an exported folder or if your emulator uses a different mod manager.

### Configurable profile

| Setting | Range / behavior |
| --- | --- |
| FPS limit | Integer 20-120, including 45; clock-based limiter with measured simulation time |
| World camera FOV | 20-120; 50 preserves original behavior; other values scale the freshly calculated world-camera angle relative to 50 |
| Render Distance | Original presets: VERY LOW (1000), LOW (5000), MEDIUM (12500), DEFAULT (25000), experimental (35000) |
| Resolution Scale | Emulator scaling: Keep current, 1x, 2x, 3x, 4x |

Shared defaults match the original BOTW 1.6 UI: **60 FPS, FOV 50, Render Distance
DEFAULT (25000), Resolution Scale 1x**. Select **Default** under Optimizer Presets
to reset all four settings. Previously saved custom choices still take precedence
on startup until you explicitly reset them.

The configurable mod is named `!!!BOTW 1.9.0 Optimizer` and needs **both its
main and SDK patch files**. Disable any previously exported `!!!BOTW 1.9.0 60 FPS` mod and
UltraCam when using it. Apply manages these known conflicts; manual installation
requires selecting the enabled mod in the emulator.

FOV scaling preserves relative aiming/cutscene zoom, with resulting angles
clamped to 5-120 degrees. Render Distance uses the same preset labels and numeric
values as the original BOTW profile. It adjusts the world camera's far clipping
plane (previously labelled Far clip distance), not object streaming or LOD.
**DEFAULT is 25000** and preserves the game's own far-plane handling. The native framebuffer resolution, native FXAA/DR
disabling, shadows, free camera and other UltraCam features are not ported.

**Resolution Scale**, which was also available in the original application,
affects the emulator's per-game configuration through **Apply**. **Extract**
writes instructions with the requested scale but does not change emulator
configuration. The default is **1x**, matching the original 1.6 profile;
Keep current is available as an explicit choice. Scaling multiplies the game's output.
Current Eden's indices are mapped explicitly, including its 1/4x and 1.25x entries.
The extra emulator AA/AF controls from the initial build have been removed;
their saved values are ignored and existing emulator AA/AF settings are preserved.

### Upgrading an earlier build

The redundant fixed-60 profile has been removed. Its saved selection ID resolves
to the configurable profile. Existing configurable-profile settings are retained;
otherwise the FPS default is 60. The old fixed-profile dropdown index is not
imported as an FPS value.

Saved numeric `far clip` values are mapped to the nearest Render Distance preset
when no new preset has been saved yet. For example, 5000 becomes LOW and 25000
becomes DEFAULT. Existing Render Distance choices take precedence.

## Export without GUI dependencies

Python 3.10+ and extracted ExeFS files are sufficient; no game keys are needed
by this exporter. Export the configurable profile with its default 60 FPS:

```powershell
python tools/export_botw_fps.py --main "C:\path\to\exefs\main" --output "C:\path\to\mods"
```

Or choose settings, including those used in the user's test:

```powershell
python tools/export_botw_fps.py --main "C:\path\to\exefs\main" --output "C:\path\to\mods" --fps 45 --fov 65 --far-clip 5000
```

The exporter also verifies the sibling **`sdk`** executable. If it is in
another folder, supply `--sdk "C:\path\to\sdk"`. Both files must match the known
Build IDs and hashes before the exporter writes anything. Without graphics
arguments, the defaults are original FOV/Render Distance (50/25000).
`--far-clip` remains available as a numeric CLI option (1000-35000).

The default format is `pchtxt`; use `--format ips` for Ryujinx. The exporter
verifies the Build ID and SHA-256 before exporting. The graphical profile
uses a known Build ID in the IPSwitch header / IPS filename; the emulator chooses whether it matches
the loaded executable. The GUI does not infer the installed version from an NSP.

Supported executable:

- Title ID: `01007EF00011E000`
- Version: `1.9.0`
- Build ID: `CD57B23FA4BBAD65803D9788C01821EE00000000000000000000000000000000`
- ExeFS main SHA-256: `f6f0b20bb1f2b67d164c24871cd473147eef1d285f12e7bd492e3126c6022e27`
- SDK Build ID: `574284B40C06CF1821A44857939083BEE5716820000000000000000000000000`
- SDK SHA-256: `1d187f29784cd0af46e9e123fc2a62c77b3b07c5a39c8633d90d6c80de64e4ad`

Other builds, including Switch 2 executables, are not covered by this patch.
Disable/remove the exported mod to restore original behavior.

## Fix for the initial export staying at 30 FPS

The initial IPS32-only export did not take effect in the tested Eden nightly,
despite its log saying `Applying IPS patch`. A read-only inspection of the
running game's memory confirmed that all four target instructions were still
original. Switching the same four writes to **IPSwitch** produced 60 FPS in the
user's subsequent test. This was a format/loading issue, not a change in patch
addresses or an additional frame limiter.

Version `0.1.1-experimental` therefore defaults to IPSwitch for Eden. Re-exporting
to the same folder removes the previous `.ips` only if its contents exactly
match this generator's patch; unrelated or user-edited patches are preserved.
Restart emulation after updating the files.

## Internal interval patch seed

The generator retains the initial four-instruction interval patch as its internal
seed and a regression reference, not as a separate user-facing profile. The seed
passes interval **1** to the timer and presentation code; the current generator
then modifies presentation and adds the limiter/SDK/camera hooks described below.

| NSO memory offset | Original bytes | New bytes |
| --- | --- | --- |
| `0x011269CC` | `F303012A` (`mov w19, w1`) | `21008052` (`mov w1, #1`) |
| `0x011269D8` | `E103132A` (`mov w1, w19`) | `21008052` |
| `0x011269FC` | `F303012A` | `21008052` |
| `0x01126A08` | `E103132A` | `21008052` |

The manifest is `src/PatchInfo/Breath Of The Wild/FPS-1.9.json`.
IPSwitch uses memory offsets with `@flag offset_shift 0x100`; IPS32 file offsets
include the same NSO header (`memory offset + 0x100`). No original
game executables or keys are included in the repository or generated mod.

Relevant 1.9 code locations:

- Framework/interface entry points: `0x011269B8`, `0x011269E8`.
- Native timer setter: `0x01126C70` (accepts interval 1, unlike the old 1.6 clamp).
- Presentation wrapper: `0x00E9AF20`.
- VFR update: `0x0151D3D0`, corresponding to 1.6's `0x01C01180`.
- VFR initialization: caller at `0x0127E740` passes baseline interval **2**.
- VFR update computes **interval / 2**: 1 -> 0.5, 2 -> 1.0, 3 -> 1.5.

## Configurable implementation

`src/modules/GameManager/BotwNativePatch.py` builds the configurable patch from
the interval seed manifest and our own ARM64 payload. Runtime generation needs only
the standard Python library; the game files are never bundled.

- The framework's final tick call at `0x0112699C` runs a clock-based limiter
  once per frame. It sleeps using the native tick/time APIs and returns a tick
  matching the original call's ABI.
- The native VFR update at `0x0151D484` receives measured elapsed time scaled
  to the game's 30 FPS simulation baseline. Category/time-scale processing is
  retained. Long stalls are capped at 100 ms to avoid a large simulation jump.
- Presentation is requested with interval zero so fractional-refresh targets
  such as 45 FPS are controlled by the software limiter.
- The **SDK patch at `0x0019CC64`** makes its native-window setter honor that
  request instead of clamping it to its minimum. The first configurable trial
  was still displaying 30 FPS without this companion patch, even while memory
  inspection showed the limiter and VFR correctly computing the 45 FPS step.
  After adding it, the user confirmed 45 FPS and normal game speed.
- Camera stores at `0x00C2DBBC` (FOV) and `0x00C2DBD0` (far clip) affect the
  active world camera. Defaults omit these hooks; shared constants used by other
  game logic are not changed.
- Code uses verified zero-filled padding in the last text page, starting at
  `0x015A1C80`. Timing state occupies padding at `0x01DB21E0`, before the game's
  BSS start at `0x01DB2200`. Every patch is scoped to its exact module Build ID.

Assembly source: `src/PatchInfo/Breath Of The Wild/NativeFPS-1.9.s`.
Rebuild its checked-in JSON payload after changing the assembly:

```powershell
python -m pip install keystone-engine
python tools/build_botw_native_payload.py
python tools/build_botw_native_payload.py --check
```

## Verification

Run the generator tests:

```powershell
python -m unittest discover -s tests -v
```

To repeat the executable/instruction checks and execute the original/patched
ARM64 routines using your own local dump:

```powershell
python -m pip install lz4 unicorn
python tools/verify_botw_fps.py --main "C:\path\to\exefs\main"
python tools/verify_botw_native.py --main "C:\path\to\exefs\main"
```

This executes 24 timer/presentation cases (both entry points, requested intervals
1/2/3, timer clamp enabled/disabled, original/patched) and three native VFR cases.
The tests check preserved stack and callee-saved registers, verify equivalence
of the generated IPSwitch and IPS32 writes, and apply the records to the emulated
memory. They do not simulate the whole Switch/GPU or verify an emulator's loader.

The configurable verifier additionally checks both module hashes, original
instructions, code/state padding, the SDK minimum-interval regression, timing
at 20/30/40/45/60/90/120 FPS, a relocated image, slow frames, long stalls,
native category multipliers, and camera FOV/zoom/clamps and far-plane writes.
UI smoke testing also covered the 1.6/1.9 profiles, retired-selection handling,
Render Distance migration, persisted settings,
two-module export, no emulator changes on Extract, and per-game graphics/conflict
handling on Apply in an isolated configuration.

For broader gameplay testing, check the FPS counter together with actual game
speed, running/climbing, combat/physics, menus, map and a cutscene. Report the
emulator/version, FPS and any speed/physics differences; these tests are needed
before treating this profile as stable.
