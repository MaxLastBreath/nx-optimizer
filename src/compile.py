import platform
import subprocess
import os
import shutil
import urllib.request
from PIL import Image
from configuration.settings import *

latest_version = Version.strip("manager-")
program_name = "NX Optimizer"

if __name__ == "__main__":
    if platform.system() == "Windows":
        command = [
            "pyinstaller",
            "run.py",
            "--onefile",
            "--clean",
            "--log-level=WARN",
            f"--name={program_name} {latest_version}",
            "--add-data",
            "GUI;GUI",
            "--add-data",
            "Localization;Localization",
            "--add-data",
            "PatchInfo;PatchInfo",
            "--icon",
            "GUI/LOGO.ico",
            "--collect-all",
            "tkinterdnd2"
        ]
        subprocess.run(command, shell=True)

    elif platform.system() == "Linux":
        arch = platform.machine()
        if arch == "aarch64":
            program_name += " Arm64"
        shutil.rmtree("AppDir", ignore_errors=True)
        command = [
            "pyinstaller",
            "--onedir",
            "--name=nx-optimizer",
            "--distpath=AppDir/usr/lib",
            "run.py",
            "--add-data",
            "GUI:GUI",
            "--add-data",
            "Localization:Localization",
            "--add-data",
            "PatchInfo:PatchInfo",
            "--hidden-import=PIL",
            "--hidden-import=PIL._tkinter_finder",
            "--hidden-import=PIL._tkinter",
            "--hidden-import=ttkbootstrap",
            "--collect-all",
            "tkinterdnd2"
        ]
        subprocess.run(command, check=True)

        os.symlink("usr/lib/nx-optimizer/nx-optimizer", "AppDir/AppRun")
        Image.open("GUI/LOGO.png").resize((256, 256)).save("AppDir/nx-optimizer.png")
        with open("AppDir/nx-optimizer.desktop", "w") as desktop:
            desktop.write(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=NX Optimizer\n"
                "Exec=nx-optimizer\n"
                "Icon=nx-optimizer\n"
                "Categories=Game;\n"
            )

        appimagetool = shutil.which("appimagetool")
        if appimagetool is None:
            appimagetool = f"./appimagetool-{arch}.AppImage"
            urllib.request.urlretrieve(
                f"https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-{arch}.AppImage",
                appimagetool,
            )
            os.chmod(appimagetool, 0o755)

        os.makedirs("dist", exist_ok=True)
        subprocess.run(
            [appimagetool, "AppDir", f"dist/{program_name} {latest_version}.AppImage"],
            check=True,
            env={**os.environ, "ARCH": arch, "APPIMAGE_EXTRACT_AND_RUN": "1"},
        )

    elif platform.system() == "Darwin":
        command = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--noconfirm",
            f"--name={program_name}",
            "run.py",
            "--add-data",
            "Localization:Localization",
            "--add-data",
            "GUI:GUI",
            "--add-data",
            "PatchInfo:PatchInfo",
            "--icon",
            "GUI/LOGO.icns",
            "--hidden-import=PIL",
            "--hidden-import=PIL._tkinter_finder",
            "--hidden-import=ttkbootstrap",
            "--collect-all",
            "tkinterdnd2"
        ]
        subprocess.run(command, check=True)
        if os.path.exists(f"dist/{program_name}"):
            os.remove(f"dist/{program_name}")
