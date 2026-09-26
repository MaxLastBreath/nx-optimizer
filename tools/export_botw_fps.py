"""Export the experimental BOTW 1.9.0 patch without GUI dependencies."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from modules.GameManager.ExefsPatch import load_patch, verify_main, export_patch, module_patches
from modules.GameManager.BotwNativePatch import build_patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", type=Path, required=True, help="Extracted BOTW 1.9.0 ExeFS main to verify")
    parser.add_argument("--output", type=Path, required=True, help="Parent folder in which to create the mod")
    parser.add_argument("--format", choices=("pchtxt", "ips"), default="pchtxt",
                        help="pchtxt for Eden/Legacy (default); ips for Ryujinx")
    parser.add_argument("--fps", type=int, default=60, help="Frame limit (20-120 FPS; default: 60)")
    parser.add_argument("--far-clip", type=int, default=25000, help="Render Distance / world camera far plane (1000-35000; default: 25000)")
    parser.add_argument("--fov", type=int, default=50, help="World camera FOV, relative to the original 50 degrees (20-120)")
    parser.add_argument("--sdk", type=Path, help="ExeFS sdk; defaults to main's sibling sdk")
    args = parser.parse_args()
    try:
        patch = load_patch(ROOT / "src/PatchInfo/Breath Of The Wild/FPS-1.9.json")
        verify_main(patch, args.main)
        patch = build_patch(
            patch, ROOT / "src/PatchInfo/Breath Of The Wild/NativeFPS-1.9.json",
            fps=args.fps, far_clip=args.far_clip, fov=args.fov,
        )
        verify_main(module_patches(patch)[1], args.sdk or args.main.with_name("sdk"))
        output = export_patch(patch, args.output / patch["mod_name"], args.format)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Exported: {output}")
    print(f"Status: {patch['status']}")


if __name__ == "__main__":
    main()
