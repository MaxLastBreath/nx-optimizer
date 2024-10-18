from configuration.settings import *
from configuration.settings_config import Setting
from modules.TOTK_Optimizer_Modules import *  # imports all needed files.
from modules.GameManager.GameManager import Game_Manager
from modules.GameManager.PatchInfo import PatchInfo
from modules.GameManager.FileManager import FileManager
from modules.GameManager.LaunchManager import LaunchManager
from modules.GameManager.CheatManager import Cheats
from modules.FrontEnd.TextureMgr import TextureMgr
from modules.FrontEnd.Localization import Localization
from modules.load_elements import create_tab_buttons, load_UI_elements
import threading, webbrowser, os, copy
import ttkbootstrap as ttk


def increase_row(row, cul_sel, cul_tex):
    row += 40
    if row >= 480:
        row = 160
        cul_tex += 180
        cul_sel += 180
    return row, cul_sel, cul_tex


class Manager:

    _patchInfo: PatchInfo = None
    _window: ttk.Window
    _Cheats: Cheats = None

    patches: list[PatchInfo] = []
    all_canvas: list[ttk.Canvas] = []
    PageBtns: list[ImageButton] = []

    old_cheats: dict = {}
    benchmarks: dict = {}

    constyle: ttk.Style
    os_platform: str = platform.system()

    Curr_Benchmark = None
    is_Ani_running: bool = False
    is_Ani_Paused: bool = False
    tooltip_active: bool = False
    LabelText: None
    warn_again: str = "yes"

    mode = "Ryujinx"
    ModeType: ImageButton

    def __init__(Manager, window):
        """
        Initializes the frontend canvas UI.\n
        This also Initializes Game_Manager, FileManager, Canvas_Create and Settings.\n
        The following is being set and done :\n
        Reads each game's patch Info. Creates an array of each available game through the Game_Manager.\n
        Load's the current game's Information.\n
        Handles the entire UI framework, all the canvas, images and ETC.
        """

        Manager._window = window

        Game_Manager.LoadPatches()
        FileManager.Initialize(window, Manager)
        TextureMgr.Initialize()  # load all images.
        Manager.patches = Game_Manager.GetPatches()

        # Save the config string in class variable config
        Manager.config = localconfig

        # Game from config should be chosen here.
        Manager._patchInfo = Manager.patches[2]
        Manager._patchInfo = Game_Manager.GetJsonByID(
            load_config_game(Manager, Manager.config)
        )

        Cheats.Initialize(Manager, Manager._patchInfo)
        Manager._Cheats = Cheats  # Store class because circular bs

        # Load Patch Info for current game.
        Manager.ultracam_beyond = Manager._patchInfo.LoadJson()

        # Load Localization
        Manager.description = Localization.GetJson()
        Manager.constyle = Style(theme=theme.lower())
        Manager.constyle.configure("TButton", font=btnfont)

        # ULTRACAM 2.0 PATCHES ARE SAVED HERE.
        Manager.UserChoices = {}
        Manager.setting = Setting(Manager)

        # Read the Current Emulator Mode.
        Manager.mode = config.get("Mode", "managermode", fallback="Legacy")

        # Force to Ryujinx default
        if platform.system() == "Darwin":
            Manager.mode = "Ryujinx"

        # Local text variable
        Manager.cheat_version = ttk.StringVar(value="Version - 1.2.1")

        # Load Canvas
        # Load_ImagePath(Manager)
        Manager.load_canvas()

        log.warning(f"Emulator {Manager.mode}")
        Manager.switchmode(True)

        # Window protocols
        Manager._window.protocol(
            "WM_DELETE_WINDOW", lambda: Canvas_Create.on_closing(Manager._window)
        )

    def warning(Manager, e):
        messagebox.showwarning(f"{e}")

    def LoadNewGameInfo(Manager):
        """Loads new Game info from the combobox (dropdown Menu)."""
        for item in Manager.patches:
            if Manager.PatchName.get() == item.Name:
                Manager._patchInfo = item
                Cheats.Initialize(Manager, item)
                Manager.ultracam_beyond = Manager._patchInfo.LoadJson()
                pos_dict = copy.deepcopy(Manager.Back_Pos)

                # DeletePatches and Load New Patches.
                Manager.DeletePatches()
                Manager.LoadPatches(Manager.all_canvas[0], pos_dict)
                Manager.toggle_pages("main")

                # Save the selected game in the config file and load options for that game.
                save_config_game(Manager, Manager.config)
                load_user_choices(Manager, Manager.config)

                Cheats.loadCheats()  # load the new cheats.
                Cheats.LoadCheatsConfig()

    def ChangeName(Manager):
        Manager.all_canvas[0].itemconfig(
            Manager.LabelText[0], text=Manager._patchInfo.Name
        )
        Manager.all_canvas[0].itemconfig(
            Manager.LabelText[1], text=Manager._patchInfo.Name
        )

    def LoadPatches(Manager, canvas, pos_dict):
        keys = Manager.ultracam_beyond.get("Keys", [""])

        for name in keys:
            dicts = keys[name]

            patch_var = None
            patch_list = dicts.get("Name_Values", [""])
            patch_values = dicts.get("Values")
            patch_name = dicts.get("Name")
            patch_auto = dicts.get("Auto")
            section_auto = dicts.get("Section")
            patch_description = dicts.get("Description")
            patch_default_index = dicts.get("Default")
            pos = pos_dict[section_auto]
            if patch_auto is True:
                Manager.UserChoices[name] = ttk.StringVar(
                    master=Manager._window, value="auto"
                )
                continue

            if dicts["Class"].lower() == "dropdown":
                patch_var = Canvas_Create.create_combobox(
                    master=Manager._window,
                    canvas=canvas,
                    text=patch_name,
                    values=patch_list,
                    variable=patch_list[patch_default_index],
                    row=pos[0],
                    cul=pos[1],
                    drop_cul=pos[2],
                    width=100,
                    tags=["dropdown", "patchinfo"],
                    tag=section_auto,
                    text_description=patch_description,
                )
                new_pos = increase_row(pos[0], pos[1], pos[2])
                pos[0] = new_pos[0]
                pos[1] = new_pos[1]
                pos[2] = new_pos[2]

            if dicts["Class"].lower() == "scale":
                patch_type = dicts.get("Type")
                patch_increments = dicts.get("Increments")
                patch_var = Canvas_Create.create_scale(
                    master=Manager._window,
                    canvas=canvas,
                    text=patch_name,
                    scale_from=patch_values[0],
                    scale_to=patch_values[1],
                    type=patch_type,
                    row=pos[0],
                    cul=pos[1],
                    drop_cul=pos[2],
                    width=100,
                    increments=float(patch_increments),
                    tags=["scale", "patchinfo"],
                    tag=section_auto,
                    text_description=patch_description,
                )
                if patch_type == "f32":
                    print(f"{patch_name} - {patch_default_index}")
                    patch_var.set(float(patch_default_index))
                else:
                    patch_var.set(patch_default_index)

                canvas.itemconfig(patch_name, text=f"{float(patch_default_index)}")
                new_pos = increase_row(pos[0], pos[1], pos[2])
                pos[0] = new_pos[0]
                pos[1] = new_pos[1]
                pos[2] = new_pos[2]

            if dicts["Class"].lower() == "bool":
                patch_var = Canvas_Create.create_checkbutton(
                    master=Manager._window,
                    canvas=canvas,
                    text=patch_name,
                    variable="Off",
                    row=pos[3],
                    cul=pos[4],
                    drop_cul=pos[5],
                    tags=["bool", "patchinfo"],
                    tag=section_auto,
                    text_description=patch_description,
                )
                if patch_default_index:
                    patch_var.set("On")
                new_pos = increase_row(pos[3], pos[4], pos[5])
                pos[3] = new_pos[0]
                pos[4] = new_pos[1]
                pos[5] = new_pos[2]

            if patch_var is None:
                continue
            Manager.UserChoices[name] = patch_var

            # Change Name and Load Image.
            Manager.ChangeName()
            Canvas_Create.Change_Background_Image(
                Manager.all_canvas[0],
                os.path.join(Manager._patchInfo.Folder, "image.jpg"),
            )

    def DeletePatches(Manager):
        Manager.UserChoices.clear()
        Manager.all_canvas[0].delete("patchinfo")

    def create_canvas(Manager):

        # clear list.
        Manager.UserChoices = {}

        # Create Canvas
        Manager.maincanvas = ttk.Canvas(
            Manager._window, width=scale(1200), height=scale(600)
        )

        canvas = Manager.maincanvas
        Manager.maincanvas.pack()
        Manager.all_canvas.append(Manager.maincanvas)

        Manager.selected_options = {}

        # Load UI Elements
        load_UI_elements(Manager, Manager.maincanvas)
        create_tab_buttons(Manager, Manager.maincanvas)

        # Create Text Position
        row = 40
        cul_tex = 60
        cul_sel = 220

        # Used for 2nd column.
        row_2 = 160
        cul_tex_2 = 400
        cul_sel_2 = 550

        # Run Scripts for checking OS and finding location
        FileManager.checkpath(Manager.mode)
        FileManager.DetectOS(Manager.mode)

        # FOR DEBUGGING PURPOSES
        def onCanvasClick(event):
            print(f"CRODS = X={event.x} + Y={event.y} + {event.widget}")

        Manager.maincanvas.bind("<Button-3>", onCanvasClick)
        # Start of CANVAS options.

        # Create preset menu.
        presets = {"Saved": {}}
        values = list(presets.keys())
        Manager.selected_preset = Canvas_Create.create_combobox(
            master=Manager._window,
            canvas=canvas,
            text="OPTIMIZER PRESETS:",
            variable=values[0],
            values=values,
            row=row,
            cul=cul_tex - 20,
            tags=["text"],
            tag="Optimizer",
            description_name="Presets",
            command=lambda event: apply_selected_preset(Manager),
        )

        # Setting Preset - returns variable.

        # value = ["No Change"]
        # for item in Manager.Legacy_settings:
        #     value.append(item)

        # Manager.selected_settings = Canvas_Create.create_combobox(
        #                                                     master=Manager._window, canvas=canvas,
        #                                                     text="Legacy SETTINGS:",
        #                                                     variable=value[0], values=value,
        #                                                     row=row, cul=340, drop_cul=480,
        #                                                     tags=["text"], tag="Legacy",
        #                                                     description_name="Settings"
        #                                                 )

        value = []
        for item in Manager.patches:
            value.append(item.Name)

        Manager.PatchName = Canvas_Create.create_combobox(
            master=Manager._window,
            canvas=canvas,
            text="Select Game:",
            variable=Manager._patchInfo.Name,
            values=value,
            row=row,
            cul=340,
            drop_cul=430,
            tags=["text"],
            tag="GameSelect",
            description_name="GameSelect",
            command=lambda e: Manager.LoadNewGameInfo(),
        )

        row += 40
        # Create a label for Legacy.exe selection
        backupbutton = cul_sel
        command = lambda e: Manager.select_Legacy_exe()

        def browse():
            Manager.select_Legacy_exe()

        text = "SELECT EXECUTABLE"
        Canvas_Create.create_label(
            master=Manager._window,
            canvas=canvas,
            text=text,
            description_name="Browse",
            row=row,
            cul=cul_tex - 20,
            tags=["text"],
            tag=["Select-EXE"],
            outline_tag="outline",
            command=command,
        )

        Offset = 170

        btn = Canvas_Create.image_Button(
            canvas=canvas,
            row=row - 5,
            cul=cul_tex + Offset,
            name="browse",
            anchor="c",
            img_1=TextureMgr.Request("browse.png"),
            img_2=TextureMgr.Request("browse_a.png"),
            command=lambda e: browse(),
            tags=["Button"],
        )

        # Reset to Appdata
        def appdata():
            FileManager.checkpath(Manager.mode)
            superlog.info("Successfully Defaulted to Appdata!")
            save_user_choices(Manager, Manager.config, "appdata", None)

        btn = Canvas_Create.image_Button(
            canvas=canvas,
            row=row - 5,
            cul=cul_tex + Offset + 92,
            name="appdata",
            anchor="c",
            img_1=TextureMgr.Request("autosearch.png"),
            img_2=TextureMgr.Request("autosearch_a.png"),
            command=lambda e: browse(),
            tags=["Button"],
        )

        backupbutton = cul_sel + 165

        # Create a Backup button
        btn = Canvas_Create.image_Button(
            canvas=canvas,
            row=row - 5,
            cul=cul_tex + Offset + 92 * 2,
            name="backup",
            anchor="c",
            img_1=TextureMgr.Request("backup.png"),
            img_2=TextureMgr.Request("backup_a.png"),
            command=lambda e: FileManager.backup(),
            tags=["Button"],
        )

        btn = Canvas_Create.image_Button(
            canvas=canvas,
            row=row - 5,
            cul=cul_tex + Offset + 92 * 3,
            name="shaders",
            anchor="c",
            img_1=TextureMgr.Request("shaders.png"),
            img_2=TextureMgr.Request("shaders_a.png"),
            command=lambda e: FileManager.clean_shaders,
            tags=["Button"],
        )

        row += 40

        # Graphics & Extra & More - the -20 is extra
        page_1 = Canvas_Create.image_Button(
            canvas=canvas,
            row=row - 35,
            cul=cul_tex - 10 - 20,
            name="main",
            img_1=TextureMgr.Request("graphics.png"),
            img_2=TextureMgr.Request("graphics_active.png"),
            command=lambda e: Manager.toggle_pages("main"),
            Type=ButtonToggle.StaticDynamic,
            isOn=True,
        )

        page_2 = Canvas_Create.image_Button(
            canvas=canvas,
            row=row - 35,
            cul=cul_tex + 190 - 10,
            name="extra",
            img_1=TextureMgr.Request("extra.png"),
            img_2=TextureMgr.Request("extra_active.png"),
            command=lambda e: Manager.toggle_pages("extra"),
            Type=ButtonToggle.StaticDynamic,
        )

        Manager.PageBtns.append(page_1)
        Manager.PageBtns.append(page_2)

        # BIG TEXT.
        Manager.LabelText = Canvas_Create.create_label(
            master=Manager._window,
            canvas=canvas,
            text="Tears Of The Kingdom",
            font=bigfont,
            color=BigTextcolor,
            description_name="Mod Improvements",
            anchor="c",
            row=row,
            cul=575,
            tags=["Big-Text", "Middle-Text"],
        )

        row += 40

        ##              AUTO PATCH INFO STARTS HERE ALL CONTROLLED IN JSON FILE.
        ##              THIS IS FOR ULTRACAM BEYOND GRAPHICS AND PERFORMANCE (2.0)
        ##              REMOVED DFPS, SINCE ULTRACAM BEYOND DOES IT ALL AND SO MUCH BETTER.

        pos_dict = {
            "main": [row, cul_tex, cul_sel, row_2, cul_tex_2, cul_sel_2],
            "extra": [row, cul_tex, cul_sel, row_2, cul_tex_2, cul_sel_2],
        }

        Manager.Back_Pos = copy.deepcopy(pos_dict)

        Manager.LoadPatches(canvas, pos_dict)

        row = pos_dict["main"][0]
        row_2 = pos_dict["main"][3]

        Canvas_Create.image_Button(
            canvas=canvas,
            row=510,
            cul=25,
            img_1=TextureMgr.Request("apply.png"),
            img_2=TextureMgr.Request("apply_active.png"),
            command=lambda event: FileManager.submit(),
        )

        Manager.ModeType = Canvas_Create.image_Button(
            canvas=canvas,
            row=20,
            cul=620,
            img_1=TextureMgr.Request("Switch_Button.png"),
            img_2=TextureMgr.Request("Switch_Button_2.png"),
            command=lambda event: Manager.switchmode(),
            Type=ButtonToggle.Dynamic,
        )

        # reverse scale.
        Canvas_Create.image_Button(
            canvas=canvas,
            row=510,
            cul=25 + int(TextureMgr.Request("apply.png").width() / sf),
            img_1=TextureMgr.Request("launch.png"),
            img_2=TextureMgr.Request("launch_active.png"),
            command=lambda event: LaunchManager.launch_GAME(Manager, FileManager),
        )

        # extract
        Canvas_Create.image_Button(
            canvas=canvas,
            row=510,
            cul=25 + int(7 + int(TextureMgr.Request("launch.png").width() / sf) * 2),
            img_1=TextureMgr.Request("extract.png"),
            img_2=TextureMgr.Request("extract_active.png"),
            command=lambda event: Manager.extract_patches(),
        )

        Canvas_Create.image_Button(
            canvas=canvas,
            row=560,
            cul=1010,
            anchor="c",
            img_1=TextureMgr.Request("optimizer_logo.png"),
            img_2=TextureMgr.Request("optimizer_logo_active.png"),
            command=lambda event: Manager.open_browser("Kofi"),
        )

        # Load Saved User Options.
        Manager.toggle_pages("main")
        load_user_choices(Manager, Manager.config)
        return Manager.maincanvas

    def update_scaling_variable(Manager, something=None):
        Manager.fps_var.set(Manager.fps_var_new.get())

    def select_Legacy_exe(Manager):
        if Manager.os_platform == "Windows":
            Legacy_path = filedialog.askopenfilename(
                title=f"Please select {Manager.mode}.exe",
                filetypes=[("Executable files", "*.exe"), ("All Files", "*.*")],
            )

            executable_name = Legacy_path
            if executable_name.endswith("Ryujinx.exe") or executable_name.endswith(
                "Ava.exe"
            ):
                if Manager.mode == "Legacy":
                    Manager.switchmode(True)
            else:
                if Manager.mode == "Ryujinx":
                    Manager.switchmode(True)

            if Legacy_path:
                # Save the selected Legacy.exe path to a configuration file
                save_user_choices(Manager, Manager.config, Legacy_path)
                home_directory = os.path.dirname(Legacy_path)
                fullpath = os.path.dirname(Legacy_path)
                if any(item in os.listdir(fullpath) for item in ["user", "portable"]):
                    superlog.info(
                        f"Successfully selected {Manager.mode}.exe! And a portable folder was found at {home_directory}!"
                    )
                    FileManager.checkpath(Manager.mode)
                    return Legacy_path
                else:
                    superlog.info(
                        f"Portable folder for {Manager.mode} not found defaulting to appdata directory!"
                    )
                    FileManager.checkpath(Manager.mode)
                    return Legacy_path
            else:
                FileManager.checkpath(Manager.mode)
                return None

        if Manager.os_platform == "Linux":
            Legacy_path = filedialog.askopenfilename(
                title=f"Please select {Manager.mode}.AppImage",
                filetypes=[
                    ("Select AppImages or Executable: ", "*.*"),
                    ("All Files", "*.*"),
                ],
            )

            executable_name = Legacy_path

            if executable_name.startswith("Ryujinx") or executable_name.startswith(
                "Ryujinx.ava"
            ):
                if Manager.mode == "Legacy":
                    Manager.switchmode(True)
            else:
                if Manager.mode == "Ryujinx":
                    Manager.switchmode(True)

            save_user_choices(Manager, Manager.config, Legacy_path)
        return Legacy_path

    def show_main_canvas(Manager):
        Canvas_Create.is_Ani_Paused = True
        Manager.cheatcanvas.pack_forget()
        Manager.maincanvas.pack()

    def toggle_pages(Manager, ShowPage: str):
        Manager.maincanvas.itemconfig(ShowPage, state="normal")

        for button in Manager.PageBtns:
            if button.Name != ShowPage:
                Manager.maincanvas.itemconfig(button.Name, state="hidden")
                log.info(f"Hiding {button.Name}")
                button.set(False)
                button.ToggleImg(WidgetState.Leave)
            else:
                button.ToggleImg(WidgetState.Enter)

    def show_cheat_canvas(Manager):
        Canvas_Create.is_Ani_Paused = False
        if Manager._patchInfo.Cheats is False:
            return

        for canvas in Manager.all_canvas:
            if canvas is not Cheats.Canvas:
                canvas.pack_forget()

        Cheats.Show()

        Manager.ani = threading.Thread(
            name="cheatbackground",
            target=lambda: Canvas_Create.canvas_animation(
                Manager._window, Cheats.Canvas
            ),
        )

        if not Manager.is_Ani_running == True:
            Manager.is_Ani_running = True
            Manager.ani.start()

    def open_browser(Manager, web, event=None):
        url = "https://ko-fi.com/maxlastbreath#"
        if web == "Kofi":
            url = "https://ko-fi.com/maxlastbreath#"
        elif web == "Github":
            url = "https://github.com/MaxLastBreath/TOTK-mods"
        elif web == "Discord":
            url = "https://discord.gg/7MMv4yGfhM"
        webbrowser.open(url)

    def load_canvas(Manager):
        # Main
        Manager.create_canvas()
        Cheats.CreateCanvas(Manager)
        Cheats.Hide()
        load_benchmark(Manager)

    def switchmode(Manager, Force=False):
        if Force is True:
            if Manager.mode == "Ryujinx":
                Manager.ModeType.set(False)
            else:
                Manager.ModeType.set(True)
            Manager.ModeType.ToggleImg(WidgetState.Leave)
            superlog.info(f"Switched to {Manager.mode}")
            FileManager.checkpath(Manager.mode)
            return

        if Manager.ModeType.get() is True:
            Manager.mode = "Ryujinx"
            for canvas in Manager.all_canvas:
                canvas.itemconfig("Legacy", state="hidden")
                canvas.itemconfig("Ryujinx", state="normal")

        elif Manager.os_platform != "Darwin":
            Manager.mode = "Legacy"
            for canvas in Manager.all_canvas:
                canvas.itemconfig("Legacy", state="normal")
                canvas.itemconfig("Ryujinx", state="hidden")

        superlog.info(f"Switched to {Manager.mode}")
        FileManager.checkpath(Manager.mode)

    def fetch_var(Manager, var, dict, option):
        if not dict.get(option, "") == "":
            var.set(dict.get(option, ""))

    def extract_patches(Manager):
        FileManager.is_extracting = True
        FileManager.submit()
