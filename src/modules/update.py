import subprocess
from configuration.settings import Version
from packaging.version import parse
from tkinter import messagebox
from modules.logger import log
import requests, shutil, platform, sys, glob, os

textver = Version.strip("manager-")
GITHUB = "nx-optimizer"
OWNER = "MaxLastBreath"


def show_confirmation_dialog(remote_version_str):
    result = messagebox.askyesno(
        "Confirmation",
        f"Mod Manager version {remote_version_str} was found, do you want to apply the update?",
    )
    return result


# Check For Update
def check_for_updates():
    try:
        log.info("Checking for Updates!")
        url = f"https://api.github.com/repos/{OWNER}/{GITHUB}/releases/latest"
        response = requests.get(url)
        if response.status_code == 200:
            response.raise_for_status()
            release_info = response.json()
            remote_version_str = release_info["tag_name"].strip("manager-")
            remote_version = parse(remote_version_str)

            if remote_version > parse(textver):
                confirmation_result = show_confirmation_dialog(remote_version_str)
                if confirmation_result:
                    download_update(release_info["assets"])
                else:
                    return
            else:
                log.info("No Updates Found. Your app is up to date.")
    except requests.exceptions.ConnectionError as e:
        log.warning(
            "No internet connection or api limit reached. You won't be able to check for Updates."
        )


def download_update(assets):
    current_platform = platform.system()

    for asset in assets:
        asset_name = asset["name"]
        asset_url = asset["browser_download_url"]

        if current_platform == "Linux" and asset_name.endswith(".AppImage"):
            log.info(f"Downloading {asset_name}")
            try:
                response = requests.get(asset_url)
                response.raise_for_status()
            except requests.RequestException as e:
                log.error(f"Error downloading asset: {e}")
                return

            with open(asset_name, "wb") as f:
                f.write(response.content)

            log.info("Asset downloaded successfully.")

        elif current_platform == "Windows" and asset_name.endswith(".exe"):
            log.info(f"Downloading {asset_name}")
            try:
                response = requests.get(asset_url)
                response.raise_for_status()
            except requests.RequestException as e:
                log.error(f"Error downloading asset: {e}")
                return

            with open(asset_name, "wb") as f:
                f.write(response.content)

            log.info("Asset downloaded successfully.")
        apply_update(assets)


def apply_update(assets):
    log.info("Applying Update...")
    current_platform = platform.system()
    updated_executable = None

    for asset in assets:
        asset_name = asset["name"]
        if current_platform == "Windows" and asset_name.endswith(".exe"):
            updated_executable = asset_name
            break

    if updated_executable is None:
        log.info("No Windows executable found in the assets.")
        return

    try:
        old_executable = sys.argv[0]
        if os.path.exists(old_executable):
            os.rename(old_executable, f"{old_executable}.tmp")
            log.warning("Old executable deleted.")

        if sys.platform.startswith("linux"):
            name = "NX Optimizer.AppImage"
            os.chmod(updated_executable, 0o755)
        elif sys.platform.startswith("win"):
            name = "NX Optimizer.exe"
            pass
        else:
            name = updated_executable
        os.rename(updated_executable, name)
        # Rename for consistency
        os.execl(name, *sys.argv)
    except Exception as e:
        log.error(f"Error applying update: {e}")
        return

    log.info("Update Applied. Exiting...")
    sys.exit()


def delete_old_exe():
    exe_to_rename = os.environ.get("APPIMAGE", sys.argv[0])
    current = os.path.basename(exe_to_rename)

    # Skip if running from Python script
    if current.endswith(".py") or current == "run.py":
        return

    # Skip if not an executable
    if not (current.endswith(".exe") or current.endswith(".AppImage")):
        return

    executable_directory = os.path.dirname(os.path.abspath(exe_to_rename))
    if sys.platform.startswith("linux"):
        name = "NX Optimizer.AppImage"
    elif sys.platform.startswith("win"):
        name = "NX Optimizer.exe"
    else:
        name = "NX Optimizer.exe"

    for file in os.listdir(executable_directory):
        if file == "NX Optimizer.exe" or file == "NX Optimizer.AppImage":
            return

    try:
        os.rename(exe_to_rename, name)
        subprocess.Popen([os.path.abspath(name)])
    except Exception as e:
        log.error(e)
    try:
        matching_files = glob.glob(os.path.join(executable_directory, "*.exe.tmp"))
        matching_files += glob.glob(os.path.join(executable_directory, "*appimage.tmp"))

        for file_path in matching_files:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    except Exception as e:
        log.error(f"Error: {e}")
