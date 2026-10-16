from modules.FrontEnd.FrontEndMode import NxMode
from configuration.settings import *
from modules.config import *
from tkinter import filedialog
import os, subprocess


class LaunchManager:

    def is_process_running(process_name):
        try:
            cmd = 'tasklist /fi "imagename eq {}"'.format(process_name)
            output = subprocess.check_output(cmd, shell=True).decode()
            if process_name.lower() in output.lower():
                return True
            else:
                return False
        except Exception as e:
            log.warning(f"Couldn`t detect if {process_name} is running.")

    @classmethod
    def select_game_file(cls, manager, command: None = None) -> str:
        from modules.FrontEnd.FrontEnd import Manager

        manager: Manager = manager

        # Open a file dialog to browse and select Legacy.exe
        game_path = filedialog.askopenfilename(
            title=f"Please select {manager._patchInfo.Name}.",
            filetypes=[
                ("Nintendo Gamefile", ["*.nsp", "*.xci", "*.NSP", "*.XCI"]),
                ("All Files", "*.*"),
            ],
        )

        if game_path:
            config = configparser.ConfigParser()
            config.read(localconfig, encoding="utf-8")

            if not config.has_section("Paths"):
                config.add_section("Paths")

            config.set("Paths", f"{manager._patchInfo.ID}", game_path)
        else:
            return
        with open(localconfig, "w", encoding="utf-8") as configfile:
            config.write(configfile, space_around_delimiters=False)
        return game_path

    @classmethod
    def launch_GAME(cls, manager, filemgr):
        from modules.GameManager.FileManager import FileManager
        from modules.FrontEnd.FrontEnd import Manager

        filemgr: FileManager = filemgr
        manager: Manager = manager

        config = configparser.ConfigParser()
        config.read(localconfig, encoding="utf-8")
        Game_PATH = config.get("Paths", f"{manager._patchInfo.ID}", fallback="None")

        if not os.path.exists(Game_PATH):
            log.warning(
                f"Game not found in {Game_PATH}\n Please select your game file."
            )
            Game_PATH = cls.select_game_file(manager)

        superlog.info(f"Launching game {Game_PATH}")

        if NxMode.isLegacy():
            if cls.is_process_running("yuzu.exe"):
                log.warning("Legacy is already running in the background.")
                return

            Legacypath = filemgr.read_configpath()
            if os.path.exists(Legacypath):
                Legacy_PATH = Legacypath
            else:
                Legacy_PATH = manager.select_Legacy_exe()

            cmd = [f"{Legacy_PATH}", "-u", "1", "-f", "-g", f"{Game_PATH}"]

        if NxMode.isRyujinx():
            if cls.is_process_running("Ryujinx.exe"):
                log.warning("Ryujinx is already running in the background.")
                return

            ryujinx_path = filemgr.read_configpath()
            if os.path.exists(ryujinx_path):
                Ryujinx_PATH = ryujinx_path
            else:
                Ryujinx_PATH = manager.select_Legacy_exe()
                if Ryujinx_PATH is None:
                    log.warning("Ryujinx wasn't found.")
                    return
            
            if (read_ryujinx_version(FileManager._emuconfig) >= 60):
                cmd = [f'{Ryujinx_PATH}', "--no-gui", "--fullscreen", f'{Game_PATH}']
            else:
                cmd = [f"{Ryujinx_PATH}", "-f", f"{Game_PATH}"]
        log.info(f"Launching : {cmd}")
        subprocess.Popen(cmd)
