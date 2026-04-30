from __future__ import annotations
from datetime import datetime
from modules.FrontEnd.FrontEndMode import NxMode
from modules.FrontEnd.ProgressBar import ProgressBar
from modules.GameManager.LaunchManager import LaunchManager
from modules.GameManager.ModCreator import ModCreator
from modules.GameManager.DragFile import DragFile
from modules.TOTK_Optimizer_Modules import *
from configuration.settings import *
from tkinter import messagebox
from modules.config import *
import ttkbootstrap as ttk
import subprocess
import shutil
import time

from run_config import __ROOT__


class FileManager:

    _window: ttk.Window = None
    _manager: any = None
    _emu_blacklist = ["citra-emu", "lime3ds-emu", "steam"]
    _dragfile: DragFile = None
    _emulist: list[str] = []
    _emuselect: str = None
    _wrongconfigwarn = True

    home_directory = os.path.expanduser("~")
    os_platform = platform.system()

    is_extracting = False

    _emuglobal: str = None
    _emuconfig: str = None
    _gameconfig: str = None
    nand: str = None
    sdmc: str = None
    load: str = None
    contentID: str = None

    @classmethod
    # Initialize our Window here.
    def Initialize(filemgr, Window, Mgr):
        from modules.FrontEnd.FrontEnd import Manager  # avoid Circular Imports.

        filemgr._manager : Manager = Mgr
        filemgr._window = Window
        filemgr._dragfile = DragFile(Window, Mgr)

    @classmethod
    # fmt: off
    def __Warn_LegacySaves(filemgr, OldPath, NewPath):
        message = (
            f"WARNING: Your QT Config Save Directory may not be correct!\n"
            f"Your saves could be in danger.\n"
            f"Your current Legacy directory: {NewPath}\n"
            f"Your QT Config Save Directory: {OldPath}\n"
            f"Do you want to create a backup of your save file?"
        )
        response = messagebox.askyesno("Warning", message, icon=messagebox.WARNING)
        if response:
            filemgr.backup()
            filemgr._wrongconfigwarn = False
            log.info("Sucessfully backed up save files, in backup folder. "
                    "Please delete qt-config in USER folder! "
                    "Or correct the user folder paths, then use the backup file to recover your saves!")
            pass
        else:
            filemgr._wrongconfigwarn = False
            log.info("Warning has been declined, "
                    "no saves have been moved!")
    
    @classmethod
    # fmt: off
    def read_configpath(filemgr):
        if NxMode.isLegacy():
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE_LOCAL_OPTIMIZER, encoding="utf-8")
            Legacy_path = config.get('Paths', 'Legacypath', fallback="Appdata")
            return Legacy_path
        if NxMode.isRyujinx():
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE_LOCAL_OPTIMIZER, encoding="utf-8")
            ryujinx_path = config.get('Paths', 'ryujinxpath', fallback="Appdata")
            return ryujinx_path

    @classmethod
    # fmt: off
    def __LoopSearch(filemgr) -> str:
        GameID = filemgr._manager._patchInfo.ID

        filemgr._emulist = []

        if (filemgr.os_platform == "Windows"):
            SpecialDir = "AppData/Roaming"
        elif filemgr.os_platform == "Linux":
            SpecialDir = ".local/share"

        userDir = os.path.join(filemgr.home_directory, SpecialDir)
        for folder in os.listdir(userDir):
            FolderPath = os.path.join(userDir, folder)
            if os.path.exists(os.path.join(FolderPath, "load", GameID)):
                filemgr._emulist.append(folder)
                superlog.info(f"Found Legacy Emu folder at: {FolderPath}")
                continue
        
        if len(filemgr._emulist) < 1: # Fallback to citron
            base_directory = os.path.join(filemgr.home_directory, SpecialDir, "citron")
        else:
            EmuDir = None
            if (filemgr._emuselect is not None) : 
                EmuDir = os.path.join(filemgr.home_directory, SpecialDir, filemgr._emuselect)
            base_directory = EmuDir if EmuDir is not None else os.path.join(filemgr.home_directory, SpecialDir, filemgr._emulist[0])

        return base_directory
    
    @classmethod
    # fmt: off
    def __LoopSearchLinuxConfig(filemgr) -> str:
        SpecialDir = ".config"
        userDir = os.path.join(filemgr.home_directory, SpecialDir)

        for folder in os.listdir(userDir):

            if folder in filemgr._emu_blacklist:
                continue

            base_directory = os.path.join(userDir, folder)
            lookupfile = os.path.join(base_directory, "qt-config.ini")

            if os.path.exists(lookupfile):
                log.info(f"Found Config File {lookupfile}")
                return lookupfile

        log.error("Didn't find a Legacy Emulator")

        return None
        
    @classmethod
    # fmt: off
    def __PopulateRyujinx(filemgr):
        patchinfo = filemgr._manager._patchInfo
        portablefolder = os.path.normpath(os.path.join(os.path.dirname(filemgr.read_configpath()), "portable/"))

        base_directory = filemgr.home_directory
        if (filemgr.os_platform == "Windows"):
            base_directory = os.path.join(filemgr.home_directory, "AppData", "Roaming", "Ryujinx")
        elif filemgr.os_platform == "Darwin":
            base_directory = os.path.join(filemgr.home_directory, "Library", "Application Support", "Ryujinx")
        if filemgr.os_platform == "Linux":
            base_directory = os.path.join(filemgr.home_directory, ".config", "Ryujinx")
            flatpak = os.path.join(filemgr.home_directory, ".var", "app", "org.ryujinx.Ryujinx", "config", "Ryujinx")
            if(os.path.exists(flatpak)):
                base_directory = flatpak
        if (os.path.exists(portablefolder)):
            base_directory = portablefolder

        filemgr._emuglobal = base_directory
        filemgr._emuconfig = os.path.join(base_directory, "Config.json")
        filemgr.nand = os.path.join(base_directory, "bis", "user", "save")
        filemgr.load = os.path.join(base_directory, "mods", "contents")
        filemgr.sdmc = os.path.join(base_directory, "sdcard")
        filemgr.contentID = os.path.join(base_directory, "mods", "contents", patchinfo.ID)
        filemgr._gameconfig = os.path.join(base_directory, "games", f"{patchinfo.ID}", "Config.json")
    
    @classmethod
    # fmt: off
    def __PopulateLegacy(filemgr):
        portablefolder = os.path.normpath(os.path.join(os.path.dirname(filemgr.read_configpath()), "user/"))

        base_directory = filemgr.home_directory
        patchinfo = filemgr._manager._patchInfo

        if (os.path.exists(portablefolder) and portablefolder != "AppData"):
            base_directory = portablefolder
        else: 
            base_directory = filemgr.__LoopSearch()
        
        log.info(portablefolder)

        # Config FIle BS
        if (filemgr.os_platform == "Linux"):
            filemgr._emuconfig = filemgr.__LoopSearchLinuxConfig()
            if (filemgr._emuconfig == None): 
                NxMode.switch()
                return
        else:
            filemgr._emuconfig = os.path.join(base_directory, "config/qt-config.ini")

        filemgr._emuglobal = base_directory
        filemgr.nand = os.path.normpath(os.path.join(base_directory, "nand"))
        filemgr.load = os.path.join(base_directory, "load")
        filemgr.sdmc = os.path.join(base_directory, "sdmc")

        if os.path.exists(filemgr._emuconfig):
            config_parser = configparser.ConfigParser()
            config_parser.read(filemgr._emuconfig, encoding="utf-8")
        
            NEW_nand_dir = os.path.normpath(config_parser.get('Data%20Storage', 'nand_directory', fallback=filemgr.nand)).replace('"', "")
            filemgr.load = os.path.normpath(config_parser.get('Data%20Storage', 'load_directory', fallback=filemgr.load)).replace('"', "")
            filemgr.sdmc = os.path.normpath(config_parser.get('Data%20Storage', 'sdmc_directory', fallback=filemgr.sdmc)).replace('"', "")

            if (os.path.exists(portablefolder) and NEW_nand_dir != filemgr.nand and filemgr._wrongconfigwarn):
                filemgr.__Warn_LegacySaves(NEW_nand_dir, filemgr.nand)
            filemgr.nand = NEW_nand_dir

        filemgr.contentID = os.path.join(filemgr.load, patchinfo.ID)
        filemgr._gameconfig = os.path.join(os.path.dirname(filemgr._emuconfig), "custom")

    @classmethod
    def __TransferMods(filemgr):
        """Transfer mod files to the emulator/switch location(s)..."""

        patchinfo = filemgr._manager._patchInfo
        source = patchinfo.GetModPath()

        if filemgr.is_extracting is False:
            destination = os.path.join(filemgr.contentID, patchinfo.ModName)
            os.makedirs(destination, exist_ok=True)
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            destination = os.path.join(os.getcwd(), "Extracted Files", patchinfo.ModName)
            os.makedirs(destination, exist_ok=True)
            shutil.copytree(source, destination, dirs_exist_ok=True)

        log.info(f"Copying Mod Folder. {source} to {destination}")

    @classmethod
    def DetectOS(filemgr):
        """Detects the current OS... Used only for Debugging."""

        if filemgr.os_platform == "Linux":
            superlog.info("Detected a Linux based SYSTEM!")
        elif filemgr.os_platform == "Windows":
            superlog.info("Detected a Windows based SYSTEM!")
            if NxMode.isLegacy():
                if os.path.exists(filemgr._emuconfig):
                    log.info("a qt-config.ini file found!")
                else:
                    log.warning(
                        "qt-config.ini not found, the script will assume default appdata directories, "
                        "please reopen Legacy for consistency and make sure TOTK is present..!"
                    )
        elif filemgr.os_platform == "Darwin":
            log.info("Detected a MacOS based SYSTEM!")

    @classmethod
    # fmt: off
    def checkpath(filemgr):

        '''The Primary Logic the TOTK Optimizer uses to find each emulator.'''

        # Populate Paths for Emulators
        if NxMode.isLegacy():
            filemgr.__PopulateLegacy()
        if NxMode.isRyujinx():
            filemgr.__PopulateRyujinx()

    @classmethod
    def backup(filemgr):
        """Backup save files for a specific game, for Ryujinx it fetches all games."""

        filemgr.__SelectEmulator()

        if NxMode.isLegacy():
            testforuserdir = os.path.join(
                filemgr.nand, "user", "save", "0000000000000000"
            )
            target_folder = filemgr._manager._patchInfo.ID
            GameName = filemgr._manager._patchInfo.Name

            log.info(testforuserdir)

            # checks each individual folder ID for each user and finds the ones with saves for the selected game. Then backups the saves!
            try:
                for root, dirs, files in os.walk(testforuserdir):
                    if target_folder in dirs:
                        folder_to_backup = os.path.join(root, target_folder)
                print(f"Attemping to backup {folder_to_backup}")
            except UnboundLocalError as e:
                log.error(f"No Folder to backup Found.")
                return

        # Create the 'backup' folder inside the mod manager directory if it doesn't exist
        elif NxMode.isRyujinx():
            folder_to_backup = filemgr.nand

        backup_folder_path = os.path.join(__ROOT__, "backup", GameName)

        try:
            os.makedirs(backup_folder_path, exist_ok=True)
        except PermissionError as e:
            log.error(
                f"The Optimizer doesn't have permission to create or copy folders, please move it to a different location then {os.getcwd()}"
            )
            return

        backup_file = f"{GameName} {datetime.now().strftime('%Y-%m-%d %H.%M.%S')}.zip"

        # Construct the full path for the backup file inside the 'backup' folder
        backup_file_path = os.path.join(backup_folder_path, backup_file)

        try:
            # Check if the folder exists before creating the backup
            if os.path.exists(folder_to_backup):
                shutil.make_archive(backup_file_path, "zip", folder_to_backup)
                os.rename(backup_file_path + ".zip", backup_file_path)
                messagebox.showinfo(
                    "Backup", f"Backup created successfully: {backup_file}"
                )
            else:
                messagebox.showerror("Backup Error", "Folder to backup not found.")

        except Exception as e:
            log.error(f"Backup Error", f"Error creating backup: {e}")
            messagebox.showerror("Backup Error", f"Error creating backup: {e}")

    @classmethod
    def clean_shaders(filemgr):
        answer = messagebox.askyesno(
            title="Legacy Shader Warning.",
            message="Are you sure you want to delete your shaders?\n"
            "This could Improve performance.",
        )
        emu_dir = filemgr._emuglobal
        if NxMode.isLegacy():
            shaders = os.path.join(emu_dir, f"shader/{filemgr._manager._patchInfo.ID}")
        if NxMode.isRyujinx():
            shaders = os.path.join(
                emu_dir, f"games/{filemgr._manager._patchInfo.ID}/cache/shader"
            )
        if answer is True:
            try:
                shutil.rmtree(shaders)
                log.info(f"The shaders have been successfully {shaders}")
            except FileNotFoundError as e:
                log.info("No shaders have been found. Potentially already removed.")
        if answer is False:
            log.info("Shaders deletion declined.")

    @classmethod
    def UltraCam_ConfigPath(filemgr) -> str:
        PatchInfo = filemgr._manager._patchInfo
        SdCard = filemgr.sdmc

        if filemgr.is_extracting is True:
            Folder = os.path.join(os.getcwd(), "Extracted Files")
            os.makedirs(Folder, exist_ok=True)
            return os.path.join(Folder, PatchInfo.ModName, PatchInfo.ConfigPath)
        if PatchInfo.isSDconfig is True:
            return os.path.join(SdCard, PatchInfo.ConfigPath)
        else:
            return os.path.join(filemgr.contentID, PatchInfo.ModName, PatchInfo.ConfigPath)

    @classmethod
    def Copyright(filemgr):
        directory = filemgr.contentID
        modName = filemgr._manager._patchInfo.ModName
        ModFolder = os.path.join(directory, modName)

        if (os.path.exists(ModFolder)):
            readme = os.path.join(ModFolder, "README.txt")
            PatchInfo = filemgr._manager._patchInfo

            Context = ("Mod Patch Generated by NX Optimizer\n"
            "- https://www.nxoptimizer.com/\n\n"

            "Having issues?\n"
            "- https://www.nxoptimizer.com/discord/\n\n"

            "Support NX Optimizer and future development of these mods\n"
            "- https://www.nxoptimizer.com/ko-fi/\n"
            "- https://www.nxoptimizer.com/patreon/\n\n"

            "Copyright @MaxLastBreath\n\n"
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"{PatchInfo.ModFolder} Version {PatchInfo.ModVersion} : Supported Game Versions {PatchInfo.Versions}\n"
            )
            
            with open(readme, "w+", encoding="utf-8") as file:
                file.write(Context)

    @classmethod
    def __SelectEmulator(filemgr):
        if (not NxMode.isLegacy() or filemgr.is_extracting):
            return
        
        if (len(filemgr._emulist) > 1):
            
            Dialogue = ttk.Toplevel()
            Dialogue.title(f"Select {NxMode.get()} Emulator")
            screen_width = filemgr._window.winfo_screenwidth()
            screen_height = filemgr._window.winfo_screenheight()

            x_coordinate = (screen_width - Dialogue.winfo_reqwidth()) // 2
            y_coordinate = (screen_height - Dialogue.winfo_reqheight()) // 2
            Dialogue.geometry(f"+{x_coordinate}+{y_coordinate}")

            canvas = ttk.Canvas(Dialogue, width=scale(400), height=scale(40 * len(filemgr._emulist) + 40 + 40))
            canvas.pack()

            row = 40

            Canvas_Create.create_label(
                    Dialogue, 
                    canvas, 
                    f"Please select which Emulator to install to :", 
                    row = row,
                    color = html_color["red"]
                )
            
            row +=40

            def Wee(event, Emu):
                log.error(f"WEEE {Emu}")
                filemgr._emuselect = Emu
                Dialogue.destroy()

            count = 0

            for emu in filemgr._emulist:
                count+=1
                Canvas_Create.create_label(
                        Dialogue, 
                        canvas,
                        f"{count}: {emu}",
                        color=html_color["purple"],
                        row = row, 
                        command=lambda e, emu=emu: Wee(e, emu)
                    )
                row +=40

            Dialogue.wait_window()
            filemgr.checkpath()

    @classmethod
    def submit(filemgr, mode: str | None = None):

        superlog.info(f"STARTING {mode}")
        filemgr.__SelectEmulator()

        filemgr.mod_blacklist = []
        filemgr.mod_whitelist = []

        def timer(value):
            ProgressBar.progress_bar["value"] = value
            filemgr._window.update_idletasks()

        def run_tasklists(tasklist):
            com = 100 // len(tasklist)
            for task in tasklist:
                timer(com)
                com += com
                task
                time.sleep(0.05)

            ProgressBar.End(filemgr._manager)

        def run_tasks():
            if mode == "Cheats":
                superlog.info("Starting TASKs for Cheat Patch..")
                tasklist = [Create_Mod_Patch("Cheats")]

                if get_setting("cheat-backup") in ["On"]:
                    tasklist.append(filemgr.backup())

                run_tasklists(tasklist)

                superlog.info(
                    "Tasks have been COMPLETED. Feel free to Launch the game."
                )
                return
            if mode == None:
                superlog.info("Starting TASKs for Normal Patch..")

                def stop_extracting():
                    filemgr.is_extracting = False

                tasklist = [
                    Exe_Running(),
                    filemgr.__TransferMods(),
                    Create_Mod_Patch(),
                    Disable_Mods(),
                    stop_extracting(),
                    filemgr.Copyright()
                ]

                if get_setting("auto-backup") in ["On"]:
                    tasklist.append(filemgr.backup())
                
                run_tasklists(tasklist)

                superlog.info(
                    "Tasks have been COMPLETED. Feel free to Launch the game."
                )
                return

        def Create_Mod_Patch(mode: str | None = None):
            save_user_choices(filemgr._manager, filemgr._manager.config)

            patchInfo = filemgr._manager._patchInfo
            modDir = filemgr.contentID
            modName = filemgr._manager._patchInfo.ModName

            if mode == "Cheats":
                ProgressBar.string.set("Creating Cheat Patches.")
                ModCreator.CreateCheats()
                return

            elif mode == None:
                log.info(f"Generating mod at {modDir}")
                os.makedirs(modDir, exist_ok=True)

                # Update progress bar
                ProgressBar.string.set("NX-Optimizer Patching...")

                filemgr.mod_whitelist.append(modName)
                ini_file_path = filemgr.UltraCam_ConfigPath()

                log.warning(f"Creating {modName} config File Path... {ini_file_path}\n")

                ini_file_directory = os.path.dirname(ini_file_path)
                os.makedirs(ini_file_directory, exist_ok=True)

                log.info(f"Opening {modName} config file...")
                
                keys_list = set()

                for cfg in filemgr._manager.UserConfigs:
                    data = filemgr._manager.UserConfigs[cfg]
                    
                    if isinstance(data, list):
                        keys_list.update(data)
                    else:
                        keys_list.add(data)

                for configName in keys_list:
                    config = configparser.ConfigParser()
                    config.optionxform = lambda option: option

                    if (configName != "Keys"):
                        configFile = os.path.join(ini_file_path, configName + ".ini")
                    else:
                        configFile = ini_file_path ## compatibility for old patches

                    if os.path.exists(configFile):
                        config.read(configFile, encoding="utf-8")

                    log.info(f"Starting {modName} Patcher... Patching {configFile}")

                    ## TOTK UC BEYOND AUTO PATCHER
                    try:
                        ModCreator.UCAutoPatcher(filemgr._manager, config, configName)
                        ModCreator.UCResolutionPatcher(filemgr, filemgr._manager, config, configName)
                        ModCreator.UCAspectRatioPatcher(filemgr._manager, config, configName)
                    except Exception as e:
                        log.error(f"Failed to patch {modName} config with Error : {e}")

                    log.info(f"Starting {modName} Patcher has finished running...")

                    ## WRITE IN CONFIG FILE FOR UC 2.0
                    with open(configFile, "w+", encoding="utf-8") as configfile:
                        config.write(configfile)

        def Exe_Running():

            if (filemgr.os_platform != "Windows"):
                log.info("Platform is not Windows, No need to check for Executable running.")
                return
            
            is_Program_Opened = LaunchManager.is_process_running(
                NxMode.get() + ".exe"
            )

            message = (
                f"{NxMode.get()}.exe is Running, \n"
                f"The Optimizer Requires {NxMode.get()}.exe to be closed."
                f"\nDo you wish to close {NxMode.get()}.exe?"
            )
            if is_Program_Opened is True:
                response = messagebox.askyesno(
                    "Warning", message, icon=messagebox.WARNING
                )
                if response is True:
                    subprocess.run(
                        ["taskkill", "/F", "/IM", f"{NxMode.get()}.exe"],
                        check=True,
                    )
            if is_Program_Opened is False:
                log.info(f"{NxMode.get()}.exe is closed, working as expected.")

        def Disable_Mods():
            ProgressBar.string.set(f"Disabling old mods...")
            log.info("Disabling Outdated Mods...")

            # Convert the lists to sets, removing any duplicates.
            filemgr.mod_blacklist = set(filemgr.mod_blacklist)
            filemgr.mod_whitelist = set(filemgr.mod_whitelist)
            
            # Run the Main code to Enable and Disable necessary Mods, the remove ensures the mods are enabled.
            if NxMode.isLegacy():
                
                # read config to pass into disabled keys h
                emuconfig = configparser.ConfigParser()
                emuconfig.read(filemgr._emuconfig, encoding="utf-8")

                for item in filemgr.mod_blacklist:
                    modify_disabled_key(
                        filemgr._emuconfig,
                        filemgr.contentID,
                        emuconfig,
                        filemgr._manager._patchInfo.IDtoNum(),
                        item,
                        action="add"
                    )

                for item in filemgr.mod_whitelist:
                    modify_disabled_key(
                        filemgr._emuconfig,
                        filemgr.contentID,
                        emuconfig,
                        filemgr._manager._patchInfo.IDtoNum(),
                        item,
                        action="remove"
                    )

            # fmt: off
            if (NxMode.isRyujinx() and not filemgr.is_extracting):
                enable_ryujinx_mods(filemgr.mod_blacklist, filemgr.mod_whitelist)

        ProgressBar.Run(filemgr._window, run_tasks)
