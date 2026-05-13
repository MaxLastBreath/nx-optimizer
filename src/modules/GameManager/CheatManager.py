import ttkbootstrap as ttk
from modules.FrontEnd.CanvasMgr import Canvas_Create
from modules.FrontEnd.TextureMgr import TextureMgr
from modules.FrontEnd.ScrollableCanvas import ScrollableCanvas
from modules.GameManager.FileManager import FileManager
from modules.GameManager.PatchInfo import PatchInfo
from modules.load_elements import create_tab_buttons
from modules.config import load_user_choices
from modules.logger import log, superlog
from modules.scaling import *


def method_call_decorator(func):

    def wrapper(*args, **kwargs):

        cls: Cheats = args[0]

        # decide if cheats button should be removed or not.
        if cls._patchInfo.Cheats is False:
            for canvas in cls._manager.all_canvas:
                canvas.itemconfig("CheatButton", state="hidden")
            return
        else:
            for canvas in cls._manager.all_canvas:
                canvas.itemconfig("CheatButton", state="normal")

        result = func(*args, **kwargs)
        return result

    return wrapper


class Cheats:

    Canvas: ttk.Canvas | None = None
    _manager = None
    _patchInfo: PatchInfo = None
    _isInit: bool = False
    CheatVersion: ttk.StringVar | None = None
    CheatCombo: ttk.Combobox = None
    CheatsInfo: dict[str, ttk.StringVar] = {}
    versionvalues: list = []

    @classmethod
    def Initialize(cls, manager, patchinfo: PatchInfo):
        from modules.FrontEnd.FrontEnd import Manager

        Cheats._manager: Manager = manager
        Cheats._patchInfo: PatchInfo = patchinfo

        if Cheats.CheatVersion is None:
            Cheats.CheatVersion = ttk.StringVar(manager._window, "None")

        if Cheats._patchInfo.Cheats is False:
            return

        Cheats.LoadCheatVersions()
        Cheats.LoadCheatsConfig()

    @classmethod
    def Hide(cls):
        Cheats.Canvas.pack_forget()

    @classmethod
    def Show(cls):
        Cheats.Canvas.pack()

    @classmethod
    def CreateCanvas(cls, manager) -> ttk.Canvas:

        "Create Cheat Canvas, should be only ran a single time."

        if Cheats._isInit is True:
            raise "Cheat Canvas is Already Created"

        # Create Canvas
        canvas = ScrollableCanvas(
            manager._window,
            viewport=(20, 28, 1020, 500),
            columns=[(20, 1175)],
            width=scale(1200),
            height=scale(600),
        )

        canvas.pack(expand=1, fill="both")
        manager.cheatcanvas = canvas
        Cheats.Canvas = canvas
        manager.all_canvas.append(canvas)

        # Create UI elements.
        Cheats.__Cheat_UI_elements(canvas)
        create_tab_buttons(manager, canvas)

        load_user_choices(manager, manager.config)

        # Create a submit button
        Canvas_Create.create_button(
            master=manager._window,
            canvas=canvas,
            text="Apply Cheats",
            row=520,
            cul=39,
            width=9,
            padding=5,
            tags=["Button"],
            style="success",
            description_name="Apply Cheats",
            command=lambda: FileManager.submit("Cheats"),
        )

        # Create a Reset button
        Canvas_Create.create_button(
            master=manager._window,
            canvas=canvas,
            text="Reset Cheats",
            row=520,
            cul=277 + 6 + 2,
            width=8,
            padding=5,
            tags=["Button"],
            style="default",
            description_name="Reset Cheats",
            command=Cheats.ResetCheats,
        )

        # Read Cheats
        Canvas_Create.create_button(
            master=manager._window,
            canvas=canvas,
            text="Read Saved Cheats",
            row=520,
            cul=366 + 2,
            width=11,
            padding=5,
            tags=["Button"],
            style="default",
            description_name="Read Cheats",
            command=Cheats.LoadCheatsConfig,
        )

        # Backup
        Canvas_Create.create_button(
            master=manager._window,
            canvas=canvas,
            text="Backup",
            row=520,
            cul=479 + 2,
            width=7,
            padding=5,
            tags=["Button"],
            style="default",
            description_name="Backup",
            command=FileManager.backup,
        )

        Cheats.LoadCheatVersions()

        Cheats._isInit = True

        if manager._patchInfo.Cheats is False:
            return

        Cheats.loadCheats()
        Cheats.LoadCheatsConfig()

    @classmethod
    @method_call_decorator
    def loadCheats(cls):

        "Load Cheats on the canvas."

        row = 40
        col_idx = 0
        num_cols = 5
        col_stride = 240
        base_cul_tex = 30
        base_cul_sel = 195

        try:
            index = Cheats.versionvalues.index(Cheats.CheatVersion.get())
        except ValueError:
            log.warning("Cheat Version not detected Properly.")
            index = -1

        corrent_cheats = Cheats._patchInfo.LoadCheatsJson()[index].items()

        superlog.info(
            f"Loading Cheats for {Cheats._patchInfo.Name} Version {Cheats.CheatVersion.get()}"
        )

        current_cheats_dict = dict(corrent_cheats)
        sorted_cheats = dict(
            sorted(current_cheats_dict.items(), key=lambda item: item[0])
        )

        try:
            for key_var, value in Cheats.CheatsInfo.items():
                value = value.get()
                Cheats.old_cheats[key_var] = value
        except AttributeError as e:
            Cheats.old_cheats = {}

        Cheats.CheatsInfo = {}

        if hasattr(Cheats.Canvas, "reset_scroll"):
            Cheats.Canvas.reset_scroll()
        Cheats.Canvas.delete("cheats")

        for version_option_name, version_option_value in sorted_cheats.items():
            # Exclude specific keys from being displayed
            if version_option_name in ["Source", "nsobid", "offset", "version"]:
                continue

            # Create label
            if version_option_name not in [
                "Source",
                "Version",
                "Aversion",
                "Cheat Example",
            ]:

                cul_tex = base_cul_tex + col_idx * col_stride
                cul_sel = base_cul_sel + col_idx * col_stride

                version_option_var = Canvas_Create.create_checkbutton(
                    master=Cheats._manager._window,
                    canvas=Cheats.Canvas,
                    text=version_option_name,
                    variable="Off",
                    row=row,
                    cul=cul_tex,
                    drop_cul=cul_sel,
                    tags=["text", "scrollable"],
                    tag="cheats",
                    description_name=version_option_name,
                )

                # Create enable/disable dropdown menu
                try:
                    if Cheats.old_cheats.get(version_option_name) == "On":
                        version_option_var.set("On")
                except AttributeError as e:
                    Cheats.old_cheats = {}
                Cheats.CheatsInfo[version_option_name] = version_option_var
            else:
                continue

            col_idx += 1
            if col_idx >= num_cols:
                col_idx = 0
                row += 40

        if hasattr(Cheats.Canvas, "set_content_height"):
            Cheats.Canvas.update_idletasks()
            Cheats.Canvas.set_content_height(scale(row + 60))

    @classmethod
    @method_call_decorator
    def ResetCheats(cls):
        try:
            for key, value in Cheats.CheatsInfo.items():
                value.set("Off")
        except AttributeError as e:
            log.error(f"Error found from ResetCheats, the script will continue. {e}")

    @classmethod
    def __Cheat_UI_elements(cls, canvas):

        "Create UI Elements, Backgrounds etc."

        canvas.create_image(
            0,
            0,
            anchor="nw",
            image=TextureMgr.Request("image.jpg"),
            tags="background",
        )

        canvas.create_image(
            0,
            0,
            anchor="nw",
            image=TextureMgr.Request("Legacy_BG.png"),
            tags="overlay-1",
        )

        canvas.create_image(
            0,
            0,
            anchor="nw",
            image=TextureMgr.Request("BG_Left_Cheats.png"),
            tags="overlay",
        )

    @classmethod
    @method_call_decorator
    def LoadCheatVersions(cls):
        """Create a Cheat Version Combobox and load all cheats into a single array."""

        # Push every version in combobox
        Cheats.versionvalues = []
        for each in Cheats._patchInfo.LoadCheatsJson():
            for key, value in each.items():
                if key == "Aversion":
                    Cheats.versionvalues.append("Version - " + value)

        cls.LoadCheatVersionFromConfig()

        try:
            Cheats.versionvalues.index(Cheats.CheatVersion.get())
        except ValueError:
            Cheats.CheatVersion.set(Cheats.versionvalues[-1])

        if Cheats.Canvas is None:
            return  # return if we don't have a canvas.

        Cheats.Canvas.delete("CheatVersionDropDown")

        Cheats.CheatVersion = Canvas_Create.create_combobox(
            master=Cheats._manager._window,
            canvas=Cheats.Canvas,
            text="",
            values=Cheats.versionvalues,
            variable=Cheats.CheatVersion.get(),
            row=520,
            cul=130 + 2,
            drop_cul=130 + 2,
            tags=["text", "CheatVersionDropDown"],
            tag=None,
            description_name="CheatVersion",
            command=lambda e: Cheats.loadCheats(),
        )

    @classmethod
    @method_call_decorator
    def CreateCheats(cls):
        """Create Cheats, works with all games that support Cheats.."""

        superlog.info("Starting Cheat patcher.")

        Cheats.SaveCheatsConfig()
        selected_cheats = {}

        for option_name, option_var in Cheats.CheatsInfo.items():
            selected_cheats[option_name] = option_var.get()

        for version_option in Cheats._patchInfo.LoadCheatsJson():
            version = version_option.get("Version", "")

            mod_path = os.path.join(
                FileManager.contentID, "Cheat Manager Patch", "cheats"
            )

            log.warning(f"Applying Cheats in {mod_path}")

            # Create the directory if it doesn't exist
            os.makedirs(mod_path, exist_ok=True)

            filename = os.path.join(mod_path, f"{version}.txt")

            try:
                with open(filename, "w", encoding="utf-8") as file:
                    file.flush()
                    # file.write(version_option.get("Source", "") + "\n") - makes cheats not work
                    for key, value in version_option.items():
                        if key not in ["Source", "Aversion", "Version"] and selected_cheats[key] == "Off":  # fmt: skip
                            continue
                        if key in selected_cheats:
                            file.write(value + "\n")
            except Exception as e:
                log.debug(f"FAILED TO CREATE CHEAT PATCH. {e}")

        superlog.info("Applied cheats successfully.")

    @classmethod
    @method_call_decorator
    def LoadCheatsConfig(cls):
        """Load Config information for cheats."""

        config = configparser.ConfigParser()
        config.read(cls._manager.config, encoding="utf-8")

        try:
            for option_name, option_var in cls.CheatsInfo.items():
                option_value = config.get(
                    f"Cheats {Cheats._patchInfo.ID}", option_name, fallback="Off"
                )
                option_var.set(option_value)
        except AttributeError:
            pass

    @classmethod
    @method_call_decorator
    def SaveCheatsConfig(cls):
        """Save Current Cheats config"""

        config[f"Cheats {Cheats._patchInfo.ID}"] = {}

        for option_name, option_var in Cheats.CheatsInfo.items():
            config[f"Cheats {Cheats._patchInfo.ID}"][option_name] = option_var.get()

        config[f"Cheats {Cheats._patchInfo.ID}"][
            "Cheat_Version"
        ] = Cheats.CheatVersion.get()

        with open(Cheats._manager.config, "w", encoding="utf-8") as file:
            config.write(file)

    @classmethod
    @method_call_decorator
    def LoadCheatVersionFromConfig(cls):
        """Set Cheats Version to Cheats.CheatVersion() from config file and TitleID"""

        config = configparser.ConfigParser()
        config.read(cls._manager.config, encoding="utf-8")

        Cheats.CheatVersion.set(
            config.get(
                f"Cheats {Cheats._patchInfo.ID}", "Cheat_Version", fallback="None"
            )
        )
