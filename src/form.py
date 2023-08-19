import tkinter as tk
import configparser
import threading
import os
import sys
import shutil
import requests
import ttkbootstrap as ttk
import time
import webbrowser
import re
from tkinter import TclError, filedialog, messagebox, Toplevel
from idlelib.tooltip import Hovertip
from ttkbootstrap.constants import *
from ttkbootstrap import Style
from PIL import Image, ImageTk, ImageFilter, ImageOps
from configparser import NoOptionError
from modules.canvas import Canvas
from modules.qt_config import modify_disabled_key, get_config_parser
from modules.checkpath import checkpath, DetectOS
from modules.backup import backup
from modules.config import save_user_choices, load_user_choices
from configuration.settings import *
from configuration.settings_config import Setting

class Manager:
    def __init__(self, window):
        # Define the Manager window.
        self.window = window

        # Configure Style.
        self.constyle = Style(theme=theme.lower())
        self.constyle.configure("TButton", font=btnfont)

        # Set Classes.
        self.on_canvas = Canvas()
        self.setting = Setting()

        # Append all canvas in Manager class.
        self.all_canvas = []

        # Load the Config.
        self.config = localconfig
        config = configparser.ConfigParser()
        config.read(localconfig)

        # Read the Current Emulator Mode.
        self.mode = config.get("Mode", "managermode", fallback="Yuzu")

        # Set neccesary variables.
        self.Yuzudir = None
        self.is_Ani_running = False
        self.is_Ani_Paused = False
        self.tooltip_active = False
        self.warn_again = "yes"
        self.title_id = title_id
        self.old_cheats = {}
        self.cheat_version = tk.StringVar(value="Version - 1.2.00")

        # Load Json Files.
        self.dfps_options = load_json("DFPS.json", dfpsurl)
        self.description = load_json("Description.json", descurl)
        self.presets = load_json("preset.json", presetsurl)
        self.version_options = load_json("Version.json", versionurl)
        self.cheat_options = load_json("Cheats.json", cheatsurl)

        # Local text variable
        self.switch_text = ttk.StringVar()
        self.switch_text.set("Switch to Ryujinx")

        # Load Canvas
        self.Load_ImagePath()
        self.load_canvas()
        self.switchmode("false")

        # Window Protocols.
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.bind("<FocusIn>", self.focus)
        self.window.bind("<FocusOut>", self.unfocus)

    def focus(self, event):
        self.is_Ani_Paused = False
    def unfocus(self, event):
        self.is_Ani_Paused = True
    def warning(self, e):
        messagebox.showwarning(f"{e}")
    def createcanvas(self):
        # Create Canvas
        self.maincanvas = tk.Canvas(self.window, width=scale(1200), height=scale(600))
        canvas = self.maincanvas
        self.maincanvas.pack()
        self.all_canvas.append(self.maincanvas)

        # Load UI Elements
        self.load_UI_elements(self.maincanvas)
        self.create_tab_buttons(self.maincanvas)

        # Create Text Position
        row = scale(40)
        cul_tex = scale(40)
        cul_sel = scale(180)

        # Run Scripts for checking OS and finding location
        checkpath(self, self.mode)
        DetectOS(self, self.mode)

        # FOR DEBUGGING PURPOSES
        def onCanvasClick(event):
            print (f"CRODS = X={event.x} + Y={event.y} + {event.widget}")
        self.maincanvas.bind("<Button-3>", onCanvasClick)
        # Start of CANVAS options.

        # Create preset menu.
        presets = {"Saved": {}} | load_json("preset.json", presetsurl)
        values = list(presets.keys())
        self.selected_preset = self.on_canvas.create_combobox(
                                                            master=self.window, canvas=canvas,
                                                            text="Select Preset:",
                                                            variable=values[0], values=values,
                                                            row=row, cul=cul_tex,
                                                            tags=["text"], tag="Yuzu",
                                                            description_name="Presets",
                                                            command=self.apply_selected_preset
                                                        )

        # Setting Preset - returns variable.
        value = ["No Change", "Steamdeck", "AMD", "Nvidia", "High End Nvidia"]
        self.selected_settings = self.on_canvas.create_combobox(
                                                            master=self.window, canvas=canvas,
                                                            text="Select Settings:",
                                                            variable=value[0], values=value,
                                                            row=row, cul=340, drop_cul=480,
                                                            tags=["text"], tag="yuzu",
                                                            description_name="Setting"
                                                        )

        row += scale(40)
        # Create a label for yuzu.exe selection
        backupbutton = cul_sel
        self.selectexe_outline = self.maincanvas.create_text(cul_tex + 1, row + 1, text="Select yuzu.exe:", anchor="w", fill=outlinecolor, font=textfont, tags=["outline"])
        self.selectexe = self.maincanvas.create_text(cul_tex, row, text="Select yuzu.exe:", anchor="w", fill=textcolor, font=textfont, tags=["text"])
        self.read_description(canvas, "Browse", self.selectexe)

        if self.os_platform == "Windows":
            self.on_canvas.create_button(
                                        master=self.window, canvas=canvas,
                                        btn_text="Browse",
                                        row=row, cul=cul_sel, width=6,
                                        tags=["text", "Button"],
                                        description_name="Browse",
                                        command=self.select_yuzu_exe
                                        )


            # Reset to Appdata
            def yuzu_appdata():
                checkpath(self, self.mode)
                print("Successfully Defaulted to Appdata!")
                save_user_choices(self, self.config, "appdata", None)

            self.on_canvas.create_button(
                                        master=self.window, canvas=canvas,
                                        btn_text="Use Appdata",
                                        row=row, cul=cul_sel + 70, width=10,
                                        tags=["text", "Button"],
                                        description_name="Reset",
                                        command=yuzu_appdata
                                        )
            backupbutton = cul_sel + 165

        # Create a Backup button
        self.on_canvas.create_button(
                                    master=self.window, canvas=canvas,
                                    btn_text="Backup",
                                    row=row, cul=backupbutton, width=7,
                                    tags=["text", "Button"],
                                    description_name="Backup",
                                    command=lambda: backup(self)
        )
        row += scale(40)

        # Create big TEXT label.
        self.preset_label = self.maincanvas.create_text(cul_tex + scale(101), row + 1, text="Display Settings", anchor="w", fill=outlinecolor, font=bigfont)
        self.preset_label2 = self.maincanvas.create_text(cul_tex + scale(100), row, text="Display Settings", anchor="w", fill=BigTextcolor, font=bigfont)
        # Create big TEXT label.
        self.preset_label = self.maincanvas.create_text(scale(400) + scale(101), row+1, text="Mod Improvements", anchor="w", fill=outlinecolor, font=bigfont)
        self.preset_label2 = self.maincanvas.create_text(scale(400) + scale(100), row, text="Mod Improvements", anchor="w", fill=BigTextcolor, font=bigfont)

        row += scale(40)

        # Create a label for resolution selection
        values = self.dfps_options.get("ResolutionNames", [])
        self.resolution_var = self.on_canvas.create_combobox(
                                                            master=self.window, canvas=canvas,
                                                            text="Select a Resolution:",
                                                            variable=value[0], values=values,
                                                            row=row, cul=cul_tex, drop_cul=cul_sel,
                                                            tags=["text"], tag=None,
                                                            description_name="Resolution",
                                                            command=lambda event: self.warning_window("Res")
                                                            )
        row += scale(40)

        # Create a label for FPS selection
        values = self.dfps_options.get("FPS", [])
        self.fps_var = self.on_canvas.create_combobox(
                                                            master=self.window, canvas=canvas,
                                                            text="Select an FPS:",
                                                            variable=value[0], values=values,
                                                            row=row, cul=cul_tex, drop_cul=cul_sel,
                                                            tags=["text"], tag=None,
                                                            description_name="FPS"
                                                      )

        row += scale(40)

        # Create a label for shadow resolution selection
        values = self.dfps_options.get("ShadowResolutionNames", [""])[1]
        self.shadow_resolution_var = self.on_canvas.create_combobox(
                                                            master=self.window, canvas=canvas,
                                                            text="Shadow Resolution:",
                                                            variable=value[0], values=values,
                                                            row=row, cul=cul_tex, drop_cul=cul_sel,
                                                            tags=["text"], tag=None,
                                                            description_name="Shadows"
                                                                    )
        row += scale(40)

        # Make exception for camera quality
        values = self.dfps_options.get("CameraQualityNames", [""])
        for index, value in enumerate(values):
            if value in ["Enable", "Enabled"]:
                values[index] = "On"
            elif value in ["Disable", "Disabled"]:
                values[index] = "Off"

        self.camera_var = self.on_canvas.create_combobox(
                                                            master=self.window, canvas=canvas,
                                                            text="Camera Quality++:",
                                                            variable=value[0], values=values,
                                                            row=row, cul=cul_tex, drop_cul=cul_sel,
                                                            tags=["text"], tag=None,
                                                            description_name="Camera"
                                                        )
        row += scale(40)

        # Create a label for UI selection
        values = ["None", "Black Screen Fix", "PS4", "Xbox"]
        self.ui_var = self.on_canvas.create_combobox(
                                                            master=self.window, canvas=canvas,
                                                            text="Select an UI:",
                                                            variable=value[0], values=values,
                                                            row=row, cul=cul_tex, drop_cul=cul_sel,
                                                            tags=["text"], tag=None,
                                                            description_name="UI"
                                                    )
        row += scale(40)

        # First Person and FOV
        values = ["Off", "70 FOV", "90 FOV", "110 FOV"]
        self.fp_var = self.on_canvas.create_combobox(
                                                        master=self.window, canvas=canvas,
                                                        text="Enable First Person::",
                                                        values=values, variable=value[0],
                                                        row=row, cul=cul_tex, drop_cul=cul_sel,
                                                        tags=["text"], tag=None,
                                                        description_name="First Person"
                                                    )
        # XYZ to generate patch.

        row = scale(120)
        cul_tex = scale(400)
        cul_sel = scale(550)

        # Create labels and enable/disable options for each entry
        self.selected_options = {}
        for version_option_name, version_option_value in self.version_options[0].items():

            # Create label
            if version_option_name not in ["Source", "nsobid", "offset", "version"]:

                # Create checkbox
                version_option_var = self.on_canvas.create_checkbutton(
                                                                        master=self.window, canvas=canvas,
                                                                        text=version_option_name,
                                                                        variable="Off",
                                                                        row=row + 40, cul=cul_tex, drop_cul=cul_sel,
                                                                        tags=["text"], tag=None,
                                                                        description_name=version_option_name
                                                                       )
                self.selected_options[version_option_name] = version_option_var
                row += scale(40)

            if row >= scale(480):
                row = scale(120)
                cul_tex += scale(180)
                cul_sel += scale(180)

        # Create a submit button
        self.on_canvas.create_button(
            master=self.window, canvas=canvas,
            btn_text="Apply Mods", tags=["Button"],
            row=520, cul=39, padding=10, width=9,
            description_name="Apply", style="success",
            command=self.submit
        )
        # Load Saved User Options.
        load_user_choices(self, self.config)
        return self.maincanvas

    def createcheatcanvas(self):
        # Create Cheat Canvas
        self.cheatcanvas = tk.Canvas(self.window, width=scale(1200), height=scale(600))
        self.cheatcanvas.pack(expand=1, fill=BOTH)
        canvas = self.cheatcanvas
        self.all_canvas.append(self.cheatcanvas)

        # Create UI elements.
        self.Cheat_UI_elements(self.cheatcanvas)
        self.create_tab_buttons(self.cheatcanvas)
        # Create Positions.
        row = scale(40)
        cul_tex = scale(40)
        cul_sel = scale(200)
        Hoverdelay = scale(500)

        # Push every version in combobox
        versionvalues = []
        for each in self.cheat_options:
            for key, value in each.items():
                if key == "Aversion":
                    versionvalues.append("Version - " + value)

        self.cheat_version = self.on_canvas.create_combobox(
                                                            master=self.window, canvas=canvas,
                                                            text="",
                                                            values=versionvalues, variable=versionvalues[1],
                                                            row=520, cul=130, drop_cul=130,
                                                            tags=["text"], tag=None,
                                                            description_name="CheatVersion",
                                                            command=lambda event: loadCheats()
                                                            )
        load_user_choices(self, self.config)


        def loadCheats():
            row = scale(40)
            cul_tex = scale(40)
            cul_sel = scale(200)

            corrent_cheats = self.cheat_options[versionvalues.index(self.cheat_version.get())].items()
            corrent_cheats_dict = dict(corrent_cheats)
            sorted_cheats = dict(sorted(corrent_cheats_dict.items(), key=lambda item: item[0]))
            try:
                for key_var, value in self.selected_cheats.items():
                    value = value.get()
                    self.old_cheats[key_var] = value
            except AttributeError as e:
                self.old_cheats = {}

            self.selected_cheats = {}

            self.cheatcanvas.delete("cheats")

            for version_option_name, version_option_value in sorted_cheats.items():
                # Exclude specific keys from being displayed
                if version_option_name in ["Source", "nsobid", "offset", "version"]:
                    continue

                # Create label
                if version_option_name not in ["Source", "Version", "Aversion", "Cheat Example"]:

                    version_option_var = self.on_canvas.create_checkbutton(
                        master=self.window, canvas=canvas,
                        text=version_option_name,
                        variable="Off",
                        row=row, cul=cul_tex, drop_cul=cul_sel,
                        tags=["text"], tag="cheats",
                        description_name=version_option_name
                    )

                    # Create enable/disable dropdown menu
                    try:
                        if self.old_cheats.get(version_option_name) == "On":
                            version_option_var.set("On")
                    except AttributeError as e:
                        self.old_cheats = {}
                    self.selected_cheats[version_option_name] = version_option_var
                else:
                    continue

                row += scale(40)

                if row > scale(480):
                    row = scale(40)
                    cul_tex += scale(200)
                    cul_sel += scale(200)


        def ResetCheats():
            try:
                for key, value in self.selected_cheats.items():
                    value.set("Off")
            except AttributeError as e:
                print(e)
                print("Error found from ResetCheats, the script will continue.")


        # Create a submit button
        self.on_canvas.create_button(
                                    master=self.window, canvas=canvas,
                                    btn_text="Apply Cheats",
                                    row=520, cul=39, width=12, padding=5,
                                    tags=["Button"],
                                    style="success",
                                    description_name="Apply Cheats",
                                    command=lambda: self.submit("Cheats")
        )

        # Create a submit button
        self.on_canvas.create_button(
                                    master=self.window, canvas=canvas,
                                    btn_text="Reset Cheats",
                                    row=520, cul=277+6, width=12, padding=5,
                                    tags=["text", "Button"],
                                    style="default",
                                    description_name="Reset Cheats",
                                    command=ResetCheats
        )
        # Read Cheats
        self.on_canvas.create_button(
                                    master=self.window, canvas=canvas,
                                    btn_text="Read Saved Cheats",
                                    row=520, cul=367+6, width=16, padding=5,
                                    tags=["Button"],
                                    style="default",
                                    description_name="Read Cheats",
                                    command=lambda: load_user_choices(self, self.config, "Cheats")
        )

        #Backup
        self.on_canvas.create_button(
                                    master=self.window, canvas=canvas,
                                    btn_text="Backup",
                                    row=520, cul=480+6, width=8, padding=5,
                                    tags=["Button"],
                                    style="default",
                                    description_name="Backup",
                                    command=lambda: backup(self)
        )
        loadCheats()
        load_user_choices(self, self.config)

    def show_maincanvas(self):
        self.cheatcanvas.pack_forget()
        self.maincanvas.pack()

    def show_cheatcanvas(self):
        self.cheatcanvas.pack()
        self.maincanvas.pack_forget()
        def canvasanimation():
            x = 0
            y = 0
            m = 1
            if FPS == 0.1:
                m = 2
            a = scale(m)
            while True:
                if not self.is_Ani_running == True:
                    print("Stopping Animation")
                    return
                if self.is_Ani_Paused == False:
                    x += m
                    self.cheatcanvas.move(self.cheatbg, -a, 0)
                    time.sleep(FPS)
                    if x == 1000:
                        self.cheatcanvas.move(self.cheatbg, scale(200), scale(200))
                        if y <= 250:
                            y += m
                            self.cheatcanvas.move(self.cheatbg, 0, -a)
                            time.sleep(FPS)
                        else:
                            x = 0
                            y = 0
                            self.cheatcanvas.move(self.cheatbg, scale(800), scale(50))
                else:
                    time.sleep(1)

        self.ani = threading.Thread(name="cheatbackground", target=canvasanimation)
        if not self.is_Ani_running == True:
            self.is_Ani_running = True
            self.ani.start()

    def open_browser(self, web, event=None):
        url = "https://ko-fi.com/maxlastbreath#"
        if web == "Kofi":
            url = "https://ko-fi.com/maxlastbreath#"
        elif web == "Github":
            url = "https://github.com/MaxLastBreath/TOTK-mods"
        elif web == "Discord":
            url = "https://discord.gg/7MMv4yGfhM"
        webbrowser.open(url)
        return

    def get_UI_path(self, file_name):
        if getattr(sys, 'frozen', False):
            # Look for the 'HUD' folder next to the executable
            executable_dir = os.path.dirname(sys.executable)
            hud_folder_path = os.path.join(executable_dir, "HUD")
            if os.path.exists(hud_folder_path):
                return os.path.abspath(os.path.join(hud_folder_path, file_name))
        # If not running as an executable or 'HUD' folder not found, assume it's in the same directory as the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        hud_folder_path = os.path.join(script_dir, "HUD")
        return os.path.abspath(os.path.join(hud_folder_path, file_name))

    def load_canvas(self):
        # Main
        self.createcanvas()
        self.createcheatcanvas()
        self.cheatcanvas.pack_forget()

    def Load_ImagePath(self):
        # Create a Gradiant for Yuzu.
        UI_path = self.get_UI_path("Yuzu_BG.png")
        image = Image.open(UI_path)
        image = image.resize((scale(1200), scale(600)))
        self.background_YuzuBG = ImageTk.PhotoImage(image)

        # Create a Gradiant for Ryujinx.
        UI_path = self.get_UI_path("Ryujinx_BG.png")
        image = Image.open(UI_path)
        image = image.resize((scale(1200), scale(600)))
        self.background_RyuBG = ImageTk.PhotoImage(image)
        # UI Elements
        UI_path = self.get_UI_path("Master_Sword.png")
        image = Image.open(UI_path)
        image = image.resize((scale(150), scale(88)))
        self.master_sword_element = ImageTk.PhotoImage(image)

        UI_path = self.get_UI_path("Master_Sword_active.png")
        image = Image.open(UI_path)
        image = image.resize((scale(155), scale(88)))
        self.master_sword_element_active = ImageTk.PhotoImage(image)

        UI_path = self.get_UI_path("Master_Sword2.png")
        image = Image.open(UI_path)
        image = ImageOps.mirror(image)
        image = image.resize((scale(155), scale(88)))
        self.master_sword_element2 = ImageTk.PhotoImage(image)

        UI_path = self.get_UI_path("Master_Sword_active2.png")
        image = Image.open(UI_path)
        image = ImageOps.mirror(image)
        image = image.resize((scale(155), scale(88)))
        self.master_sword_element2_active = ImageTk.PhotoImage(image)

        UI_path = self.get_UI_path("Hylian_Shield.png")
        image = Image.open(UI_path)
        image = image.resize((scale(72), scale(114)))
        self.hylian_element = ImageTk.PhotoImage(image)

        UI_path = self.get_UI_path("Hylian_Shield_active.png")
        image = Image.open(UI_path)
        image = image.resize((scale(72), scale(114)))
        self.hylian_element_active = ImageTk.PhotoImage(image)


        # Create a Gradiant background.
        UI_path = self.get_UI_path("BG_Left.png")
        image = Image.open(UI_path)
        image = image.resize((scale(1200), scale(600)))
        self.background_UI = ImageTk.PhotoImage(image)

        UI_path = self.get_UI_path("BG_Left_2.png")
        image = Image.open(UI_path)
        image = image.resize((scale(1200), scale(600)))
        self.background_UI_element = ImageTk.PhotoImage(image)

        # Create Gradiant for cheats.
        UI_path = self.get_UI_path("BG_Cheats.png")
        image = Image.open(UI_path)
        image = image.resize((scale(1200), scale(600)))
        self.background_Cheats = ImageTk.PhotoImage(image)

        # Create a transparent black background
        UI_path2 = self.get_UI_path("BG_Right.png")
        image = Image.open(UI_path2)
        image = image.resize((scale(1200), scale(600)))
        self.background_UI2 = ImageTk.PhotoImage(image)

        # Create a transparent black background
        UI_path2 = self.get_UI_path("BG_Right_UI.png")
        image = Image.open(UI_path2)
        image = image.resize((scale(1200), scale(600)))
        self.background_UI3 = ImageTk.PhotoImage(image)

        # Attempt to load images from custom folder.
        try:
            if os.path.exists("custom\\background.jpg"):
                image_path = "custom\\background.jpg"
            elif os.path.exists("custom\\background.png"):
                image_path = "custom\\background.png"
            else:
                # Load and set the image as the background
                image_path = self.get_UI_path("image.png")
            image = Image.open(image_path)
            image = image.resize((scale(1200), scale(600)))
            image = image.filter(ImageFilter.GaussianBlur(1))
            self.background_image = ImageTk.PhotoImage(image)
        except FileNotFoundError as e:
            self.warning(e)
        image = Image.open(image_path)
        image = image.resize((scale(2400), scale(1200)))
        image = image.filter(ImageFilter.GaussianBlur(3))
        self.blurbackground = ImageTk.PhotoImage(image)

        # Handle Text Window
        def fetch_text_from_github(file_url):
            try:
                response = requests.get(file_url)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"Error: Unable to fetch text from Github")
            except requests.exceptions.RequestException as e:
                print(f"Error occurred while fetching text: {e}")

            return ""
        # Information text
        file_url = "https://raw.githubusercontent.com/MaxLastBreath/TOTK-mods/main/scripts/Announcements/Announcement%20Window.txt"
        self.text_content = fetch_text_from_github(file_url)
        # Info Element

    def hoveranimation(self, canvas, mode, element, event):
        if mode.lower() == "enter":
            if element.lower() == "kofi":
                canvas.itemconfig(self.mastersword, state="hidden")
                canvas.itemconfig(self.mastersword_active, state="normal")
            if element.lower() == "github":
                canvas.itemconfig(self.mastersword1, state="hidden")
                canvas.itemconfig(self.mastersword1_active, state="normal")
            if element.lower() == "discord":
                canvas.itemconfig(self.hylian, state="hidden")
                canvas.itemconfig(self.hylian_active, state="normal")

        if mode.lower() == "leave":
            if element.lower() == "kofi":
                canvas.itemconfig(self.mastersword, state="normal")
                canvas.itemconfig(self.mastersword_active, state="hidden")
            if element.lower() == "github":
                canvas.itemconfig(self.mastersword1, state="normal")
                canvas.itemconfig(self.mastersword1_active, state="hidden")
            if element.lower() == "discord":
                canvas.itemconfig(self.hylian, state="normal")
                canvas.itemconfig(self.hylian_active, state="hidden")

    def load_UI_elements(self, canvas):
        # Images and Effects

        canvas.create_image(0, 0, anchor="nw", image=self.background_image, tags="background")
        canvas.create_image(0, 0, anchor="nw", image=self.background_YuzuBG, tags="overlay-1")
        canvas.create_image(0, 0, anchor="nw", image=self.background_UI, tags="overlay")
        canvas.create_image(0, 0, anchor="nw", image=self.background_UI_element, tags="overlay")
        # Info text BG
        canvas.create_image(0-scale(20), 0, anchor="nw", image=self.background_UI2, tags="overlay")
        canvas.create_image(0-scale(20), 0, anchor="nw", image=self.background_UI3, tags="overlay")

        # Trigger Animation
        self.mastersword = canvas.create_image(scale(794), scale(222) - scale(40), anchor="nw", image=self.master_sword_element, tags="overlay-sword1")
        self.mastersword_active = canvas.create_image(scale(794), scale(222) - scale(40), anchor="nw", image=self.master_sword_element_active, tags="overlay-sword1")
        self.maincanvas.itemconfig(self.mastersword_active, state="hidden")

        canvas.tag_bind(self.mastersword, "<Enter>", lambda event: self.hoveranimation(canvas, "Enter", "Kofi", event))
        canvas.tag_bind(self.mastersword_active, "<Leave>", lambda event: self.hoveranimation(canvas, "Leave", "Kofi", event))
        canvas.tag_bind(self.mastersword_active, "<Button-1>", lambda event: self.open_browser("Kofi"))

        # Trigger Animation
        self.mastersword1 = canvas.create_image(scale(1007), scale(222) - scale(40), anchor="nw", image=self.master_sword_element2, tags="overlay-sword2")
        self.mastersword1_active = canvas.create_image(scale(1007), scale(222) - scale(40), anchor="nw", image=self.master_sword_element2_active, tags="overlay-sword2")
        self.maincanvas.itemconfig(self.mastersword1_active, state="hidden")

        canvas.tag_bind(self.mastersword1, "<Enter>", lambda event: self.hoveranimation(canvas, "Enter", "Github", event))
        canvas.tag_bind(self.mastersword1_active, "<Leave>", lambda event: self.hoveranimation(canvas, "Leave", "Github", event))
        canvas.tag_bind(self.mastersword1_active, "<Button-1>", lambda event: self.open_browser("Github"))

        # Hylian Shield
        self.hylian = canvas.create_image(scale(978), scale(240), anchor="c", image=self.hylian_element, tags="overlay-hylian")
        self.hylian_active = canvas.create_image(scale(978), scale(240), anchor="c", image=self.hylian_element_active, tags="overlay")
        self.maincanvas.itemconfig(self.hylian_active, state="hidden")
        canvas.tag_bind(self.hylian, "<Enter>", lambda event: self.hoveranimation(canvas, "Enter", "discord", event))
        canvas.tag_bind(self.hylian_active, "<Leave>", lambda event: self.hoveranimation(canvas, "Leave", "discord", event))
        canvas.tag_bind(self.hylian_active, "<Button-1>", lambda event: self.open_browser("Discord"))


        # Information text.
        text_widgetoutline2 = canvas.create_text(scale(1001) - scale(20), scale(126) -scale(80), text=f"{self.mode} TOTK Optimizer", tags="information", fill="black", font=biggyfont, anchor="center", justify="center", width=scale(325))
        text_widget2 = canvas.create_text(scale(1000)-scale(20), scale(126)-scale(80), text=f"{self.mode} TOTK Optimizer", tags="information", fill="#FBF8F3", font=biggyfont, anchor="center", justify="center", width=scale(325))

        text_widgetoutline1 = canvas.create_text(scale(1001) -scale(20) -scale(10), scale(126) + scale(10), text=self.text_content, fill="black", font=biggyfont, anchor="center", justify="center", width=scale(325))
        text_widget1 = canvas.create_text(scale(1000) - scale(20) -scale(10), scale(125) +scale(10), text=self.text_content, fill="#FBF8F3", font=biggyfont, anchor="center", justify="center", width=scale(325))

    def Cheat_UI_elements(self, canvas):
        self.cheatbg = canvas.create_image(0, -scale(300), anchor="nw", image=self.blurbackground, tags="background")
        canvas.create_image(0, 0, anchor="nw", image=self.background_YuzuBG, tags="overlay-1")
        canvas.create_image(0, 0, anchor="nw", image=self.background_UI, tags="overlay")

    def create_tab_buttons(self, canvas):
        # GitHub Button

        # Ko-fi Button
        def enter(event, tag):
            self.maincanvas.itemconfigure(tag, fill="red")
        def leave(event, tag):
            self.maincanvas.itemconfigure(tag, fill=textcolor)

        if not canvas == self.maincanvas:
            kofi_button = ttk.Button(self.window, text="Donate", bootstyle="success", command=lambda: self.open_browser("Kofi"), padding=10)
            kofi_button_window = canvas.create_window(scale(1110)+scale(20), scale(520), anchor="center", window=kofi_button, width=scale(60), height=scale(30))
            self.read_description(canvas, "Kofi", kofi_button)
            github_button = ttk.Button(self.window, text="Github", bootstyle="info", command=lambda: self.open_browser("Github"), padding=10)
            github_button_window = canvas.create_window(scale(1046) + scale(20), scale(520), anchor="center", window=github_button, width=scale(60), height=scale(30))
            self.read_description(canvas, "Github", github_button)



        # Create tabs
        cul = scale(10)

        # Switch mode between Ryujinx and Yuzu
        manager_switch = ttk.Button(self.window, textvariable=self.switch_text, command=self.switchmode, bootstyle=style)
        manager_switch_window = canvas.create_window(scale(114) + scale(43) - scale(17), cul, anchor="w", window=manager_switch, width=scale(120), height=scale(30))
        self.read_description(canvas, "Switch", manager_switch)

        # Make the button active for current canvas.
        button1style = "default"
        button2style = "default"
        button3style = "default"
        active_button_style = "secondary"
        try:
            if canvas == self.maincanvas:
                button1style = active_button_style
            if canvas == self.cheatcanvas:
                button2style = active_button_style
        except AttributeError as e:
            e = "n"

        # 1
        self.tab1_button = ttk.Button(self.window, text="Main", bootstyle=f"{button1style}", command=self.show_maincanvas)
        tab1_button_window = canvas.create_window(0+ scale(43) - scale(17), cul, anchor="w", window=self.tab1_button, width=scale(50), height=scale(30))
        self.read_description(canvas, "Main", self.tab1_button)
        # 2
        self.tab2_button = ttk.Button(self.window, text="Cheats", bootstyle=f"{button2style}", command=self.show_cheatcanvas)
        tab2_button_window = canvas.create_window(scale(52) + scale(43) - scale(17), cul, anchor="w", window=self.tab2_button, width=scale(60), height=scale(30))
        self.read_description(canvas, "Cheats", self.tab2_button)
        # 3

        self.tab3_button = ttk.Button(self.window, text="Settings", bootstyle=f"{button3style}", command=lambda: self.setting.settingswindow(self.constyle, self.all_canvas))
        tab3_button_window = canvas.create_window(scale(235) + scale(43) - scale(17), cul, anchor="w", window=self.tab3_button, width=scale(70), height=scale(30))
        self.read_description(canvas, "Settings", self.tab2_button)

    def switchmode(self, command="true"):
        if command == "true":
            if self.mode == "Yuzu":
                self.mode = "Ryujinx"
                for canvas in self.all_canvas:
                    canvas.itemconfig("overlay-1", image=self.background_RyuBG)
                    canvas.itemconfig("information", text=f"{self.mode} TOTK Optimizer")
                self.switch_text.set("Switch to Yuzu")
                self.maincanvas.itemconfig("yuzu", state="hidden")
                return
            elif self.mode == "Ryujinx":
                self.mode = "Yuzu"
                for canvas in self.all_canvas:
                    canvas.itemconfig("overlay-1", image=self.background_YuzuBG)
                    canvas.itemconfig("information", text=f"{self.mode} TOTK Optimizer")
                # change text
                self.switch_text.set("Switch to Ryujinx")
                self.maincanvas.itemconfig("yuzu", state="normal")
                return
        elif command == "false":
            if self.mode == "Ryujinx":
                for canvas in self.all_canvas:
                    canvas.itemconfig("overlay-1", image=self.background_RyuBG)
                    canvas.itemconfig("information", text=f"{self.mode} TOTK Optimizer")
                self.switch_text.set("Switch to Yuzu")
                self.maincanvas.itemconfig("yuzu", state="hidden")
                return
        elif command == "Mode":
            return self.mode
    # Read Hover Description
    def read_description(self, canvas, option, position, position2=None, position3=None, position4=None):
        positionlist = []
        positionlist.append(position)
        if not position2 == None:
            positionlist.append(position2)
        elif not position3 == None:
            positionlist.append(position2)
        elif not position4 == None:
            positionlist.append(position2)
        for position in positionlist:
            try:
                if f"{option}" in self.description:
                    canvas_item = canvas.find_withtag(position)
                    if canvas_item:
                        canvas = canvas
                        hover = self.description[f"{option}"]
                        canvas.tag_bind(position, "<Enter>", lambda event: self.show_tooltip(event, position, hover, canvas))
                        canvas.tag_bind(position, "<Leave>", lambda event: self.hide_tooltip(event))
                        canvas.tag_bind(position, "<Return>", lambda event: self.hide_tooltip(event))
                        break
            except TclError as e:
                if f"{option}" in self.description:
                    hover = self.description[f"{option}"]
                    Hovertip(position, f"{hover}", hover_delay=Hoverdelay)

    def show_tooltip(self, event, item, text, canvas):
        bbox = canvas.bbox(item)
        x, y = bbox[0], bbox[1]
        x += canvas.winfo_rootx()
        y += canvas.winfo_rooty()

        self.window.after(50)
        self.tooltip = ttk.Toplevel()
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.geometry(f"+{x + scale(20)}+{y + scale(25)}")
        tooltip_label = tk.Label(self.tooltip, text=text, background="gray", relief="solid", borderwidth=1, justify="left")
        tooltip_label.pack()
        self.tooltip_active = True

    def hide_tooltip(self, _):
        self.tooltip.destroy()
        self.tooltip_active = False

    def apply_selected_preset(self, event=None):
        try:
            selected_preset = self.selected_preset.get()
        except AttributeError as e:
            selected_preset = "Saved"
            print(e)

        if selected_preset == "None":
            if os.path.exists(self.config):
                load_user_choices(self, self.config)
            else:
                # Fallback to the default preset
                default_preset = self.get_local_presets().get("Default", {})
                self.apply_preset(default_preset)

        elif selected_preset == "Saved":
            if os.path.exists(self.config):
                load_user_choices(self, self.config)
            else:
                messagebox.showinfo("Saved Preset", "No saved preset found. Please save your current settings first.")
        elif selected_preset in self.presets:
            preset_to_apply = self.presets[selected_preset]
            for key, value in preset_to_apply.items():
                if value == "Enable":
                    preset_to_apply[key] = "On"
                if value == "Enabled":
                    preset_to_apply[key] = "On"
                elif value == "Disable":
                    preset_to_apply[key] = "Off"
                elif value == "Disabled":
                    preset_to_apply[key] = "Off"
            # Apply the selected preset from the online presets
            self.apply_preset(self.presets[selected_preset])

    def apply_preset(self, preset_options):
        self.resolution_var.set(preset_options.get("Resolution", ""))
        self.fps_var.set(preset_options.get("FPS", ""))
        self.shadow_resolution_var.set(preset_options.get("ShadowResolution", ""))
        self.camera_var.set(preset_options.get("CameraQuality", ""))
        self.ui_var.set(preset_options.get("UI", ""))
        self.fp_var.set(preset_options.get("First Person", ""))

        skip_keys = ["Resolution", "FPS", "ShadowResolution", "CameraQuality", "UI"]

        for option_key, option_value in preset_options.items():
            # Check if the option exists in the self.selected_options dictionary and not in the skip_keys
            if option_key in self.selected_options and option_key not in skip_keys:
                self.selected_options[option_key].set(option_value)
            else:
                continue

    # Select Yuzu Dir
    def select_yuzu_exe(self):
        # Open a file dialog to browse and select yuzu.exe
        if self.os_platform == "Windows":
            yuzu_path = filedialog.askopenfilename(
                filetypes=[("Executable files", "*.exe"), ("All Files", "*.*")]
            )
            home_directory = os.path.dirname(self.yuzu_path)
            Default_Yuzu_Directory = os.path.join(home_directory, "user")
            Default_Ryujinx_Directory = os.path.join(home_directory, "portable")
            executablename = yuzu_path
            if executablename.endswith("Ryujinx.exe"):
                if self.mode == "Yuzu":
                    self.switchmode("true")
            if executablename.endswith("yuzu.exe"):
                if self.mode == "Ryujinx":
                    self.switchmode("true")
            if yuzu_path:
                # Save the selected yuzu.exe path to a configuration file
                save_user_choices(self, self.config, yuzu_path)
                home_directory = os.path.dirname(yuzu_path)
                if os.path.exists(Default_Yuzu_Directory) or os.path.exists(Default_Ryujinx_Directory):
                    print(f"Successfully selected {self.mode}.exe! And a portable folder was found at {home_directory}!")
                    checkpath(self, self.mode)
                else:
                    print("Portable folder not found defaulting to default appdata directory!")
                    checkpath(self, self.mode)

                # Update the yuzu.exe path in the current session
                self.yuzu_path = yuzu_path
            else:
                checkpath(self, self.mode)
            # Save the selected yuzu.exe path to a configuration file
            save_user_choices(self, self.config, yuzu_path)
        return
    # Load Yuzu Dir
    def load_yuzu_path(self, config_file):
        if self.mode == "Yuzu":
            config = configparser.ConfigParser()
            config.read(config_file)
            yuzu_path = config.get('Paths', 'yuzupath', fallback="Appdata")
            return yuzu_path
        if self.mode == "Ryujinx":
            config = configparser.ConfigParser()
            config.read(config_file)
            ryujinx_path = config.get('Paths', 'ryujinxpath', fallback="Appdata")
            return ryujinx_path
    # Download Manager
    @staticmethod
    def download_file(url, save_path):
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"Downloaded file: {save_path}")
        else:
            print(f"Failed to download file from {url}. Status code: {response.status_code}")

    def copy_files_and_subfolders(contents, Mod_directory):
         for item in contents:
             if item['type'] == 'file':
                file_url = item.get('download_url')
                file_name = os.path.join(Mod_directory, item['name'])

                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                   with open(file_name, 'wb') as file:
                       file.write(file_response.content)
                   print(f'copied file: {file_name}')
             elif item['type'] == "dir":
                 folder_name = os.path.join(Mod_directory, item['name'])
                 os.makedirs(folder_name, exist_ok=True)
                 subfolder_contents = Manager.get_folder_contents(item['url'])
                 Manager.copy_files_and_subfolders(subfolder_contents, folder_name)

    def get_folder_contents(api_url):
        response = requests.get(api_url)
        if response.status_code == 200:
           return response.json()

    def warning_window(self, setting_type):
        warning_message = None
        configfile = self.TOTKconfig
        config = configparser.ConfigParser()
        config.read(configfile)

        if setting_type == "Res":
            resolution = self.resolution_var.get()
            Resindex = self.dfps_options.get("ResolutionNames").index(resolution)
            current_res = self.dfps_options.get("ResolutionValues", [""])[Resindex].split("x")[1]
            proper_res = float(current_res)
            if not config.has_section("Core"):
                config.add_section("Core")
            try:
                mem1 = config.get("Core", "use_unsafe_extended_memory_layout\\use_global")
                mem2 = config.get("Core", "use_unsafe_extended_memory_layout\\default")
                mem3 = config.get("Core", "use_unsafe_extended_memory_layout") # true = 8gb - doesn't work anymore in new version of Yuzu
                newmem1 = config.get("Core", "memory_layout_mode\\use_global")
                newmem2 = config.get("Core", "memory_layout_mode\\default")
                newmemsetting = int(config.get("Core", "memory_layout_mode")) # 0 - 4gb, 1 - 6gb, 2 - 8gb
                res1 = config.get("Renderer", "resolution_setup\\use_global")
                res2 = config.get("Renderer", "resolution_setup\\default")
                res3 = int(config.get("Renderer", "resolution_setup"))
            except configparser.NoOptionError as e:
                mem1 = "true"
                mem2 = "true"
                mem3 = "false"
                newmem1 = "true"
                newmem2 = "true"
                newmemsetting = 0
                res1 = "true"
                res1 = "true"
                res3 = 0

            if proper_res > 1080:
                if mem3 == "false" or newmemsetting == 0 or not res3 == 2 or not newmem1 == "false" or not newmem2 == "false" or not mem1 == "false" or not mem2 == "false":
                    file_path = self.TOTKconfig
                    warning_message = f"Resolution {resolution}, requires 1x Yuzu renderer and extended memory layout 8GB to be enabled, otherwise it won't function properly and will cause artifacts, you currently have them disabled, do you want to enable them?"
                else:
                    print("Correct settings are already applied, no changes required!!")
            else:
                print("Resolution is lower than 1080p! No changes required!")

        if warning_message is not None and warning_message.strip():
            response = messagebox.askyesno(f"WARNING! Required settings NOT Enabled!", warning_message)
            # If Yes, Modify the Config File.
            if response:
                # Remove existing options in Renderer section
                if config.has_section("Renderer"):
                    if config.has_option("Renderer", "resolution_setup\\use_global"):
                        config.remove_option("Renderer", "resolution_setup\\use_global")
                    if config.has_option("Renderer", "resolution_setup\\default"):
                        config.remove_option("Renderer", "resolution_setup\\default")
                    if config.has_option("Renderer", "resolution_setup"):
                        config.remove_option("Renderer", "resolution_setup")

                # Remove existing options in Core section
                if config.has_section("Core"):
                    if config.has_option("Core", "use_unsafe_extended_memory_layout\\use_global"):
                        config.remove_option("Core", "use_unsafe_extended_memory_layout\\use_global")
                    if config.has_option("Core", "use_unsafe_extended_memory_layout\\default"):
                        config.remove_option("Core", "use_unsafe_extended_memory_layout\\default")
                    if config.has_option("Core", "use_unsafe_extended_memory_layout"):
                        config.remove_option("Core", "use_unsafe_extended_memory_layout")
                    if config.has_option("Core", "memory_layout_mode\\use_global"):
                        config.remove_option("Core", "memory_layout_mode\\use_global")
                    if config.has_option("Core", "memory_layout_mode\\default"):
                        config.remove_option("Core", "memory_layout_mode\\default")
                    if config.has_option("Core", "memory_layout_mode"):
                        config.remove_option("Core", "memory_layout_mode")
                # Add new values
                config.set("Renderer", "resolution_setup\\use_global", "false")
                config.set("Renderer", "resolution_setup\\default", "false")
                config.set("Renderer", "resolution_setup", "2")

                config.set("Core", "use_unsafe_extended_memory_layout\\use_global", "false")
                config.set("Core", "use_unsafe_extended_memory_layout\\default", "false")
                config.set("Core", "use_unsafe_extended_memory_layout", "true")
                config.set("Core", "memory_layout_mode\\use_global", "false")
                config.set("Core", "memory_layout_mode\\default", "false")
                config.set("Core", "memory_layout_mode", "1")

                with open(configfile, "w") as configfile:
                    config.write(configfile, space_around_delimiters=False)
            else:
                # If No, do nothing.
                print(f"Turning on required settings declined!!")

    def on_closing(self):
        print("Closing Window")
        self.is_Ani_running = False
        self.window.destroy()
    # Submit the results, run download manager. Open a Loading screen.
    def submit(self, mode=None):
        checkpath(self, self.mode)
        def timer(value):
            progress_bar["value"] = value
            self.window.update_idletasks()
        def run_tasks():
            if mode== "Cheats":
                timer(50)
                print(f"Backing up TOTK, save file from {self.nand_dir}.")
                backup(self)
                time.sleep(0.3)
                timer(100)
                UpdateVisualImprovements("Cheats")
                progress_window.destroy()
                return
            if mode== None:
                timer(20)
                DownloadFP()
                timer(40)
                DownloadUI()
                timer(50)
                DownloadDFPS()
                timer(80)
                UpdateVisualImprovements()
                time.sleep(0.3)
                timer(100)
                UpdateSettings()
                progress_window.destroy()
                return

        def UpdateVisualImprovements(mode=None):
            save_user_choices(self, self.config)

            if mode == "Cheats":
                save_user_choices(self, self.config, None, "Cheats")
                selected_cheats = {}
                for option_name, option_var in self.selected_cheats.items():
                    selected_cheats[option_name] = option_var.get()
                # Logic for Updating Visual Improvements/Patch Manager Mod. This new code ensures the mod works for Ryujinx and Yuzu together.
                for version_option in self.cheat_options:
                    version = version_option.get("Version", "")
                    mod_path = os.path.join(self.load_dir, "Cheat Manager Patch", "cheats")

                    # Create the directory if it doesn't exist
                    os.makedirs(mod_path, exist_ok=True)

                    filename = os.path.join(mod_path, f"{version}.txt")
                    all_values = []
                    with open(filename, "w") as file:
                        # file.write(version_option.get("Source", "") + "\n") - makes cheats not work
                        for key, value in version_option.items():
                            if key in selected_cheats:
                                if key not in ["Source", "Aversion", "Version"] and selected_cheats[key] == "On":
                                    file.write(value + "\n")
                print("Applied cheats.")
                return
            elif mode == None:
                resolution = self.resolution_var.get()
                fps = self.fps_var.get()
                shadow_resolution = self.shadow_resolution_var.get()
                camera_quality = self.camera_var.get()

                # Determine the path to the INI file in the user's home directory
                ini_file_directory = os.path.join(self.load_dir, "Mod Manager Patch", "romfs", "dfps")
                os.makedirs(ini_file_directory, exist_ok=True)
                ini_file_path = os.path.join(ini_file_directory, "default.ini")

                # Remove the previous default.ini file if it exists - DFPS settings.
                if os.path.exists(ini_file_path):
                    os.remove(ini_file_path)

                # Save the selected options to the INI file
                config = configparser.ConfigParser()
                config.optionxform = lambda option: option

                # Add the selected resolution, FPS, shadow resolution, and camera quality
                Resindex = self.dfps_options.get("ResolutionNames").index(resolution)
                ShadowIndex = self.dfps_options.get("ShadowResolutionNames").index(shadow_resolution)
                CameraIndex = self.dfps_options.get("CameraQualityNames").index(camera_quality)

                config['Graphics'] = {
                    'ResolutionWidth': self.dfps_options.get("ResolutionValues", [""])[Resindex].split("x")[0],
                    'ResolutionHeight': self.dfps_options.get("ResolutionValues", [""])[Resindex].split("x")[1],
                    'ResolutionShadows': self.dfps_options.get("ShadowResolutionValues", [""])[ShadowIndex]
                }
                config['dFPS'] = {'MaxFramerate': fps}
                config['Features'] = {'EnableCameraQualityImprovement': self.dfps_options.get("CameraQualityValues", [""])[CameraIndex]}

                selected_options = {}

                for option_name, option_var in self.selected_options.items():
                    selected_options[option_name] = option_var.get()
                # Logic for Updating Visual Improvements/Patch Manager Mod. This new code ensures the mod works for Ryujinx and Yuzu together.
                for version_option in self.version_options:
                    version = version_option.get("version", "")
                    mod_path = os.path.join(self.load_dir, "Mod Manager Patch", "exefs")

                    # Create the directory if it doesn't exist
                    os.makedirs(mod_path, exist_ok=True)

                    filename = os.path.join(mod_path, f"{version}.pchtxt")
                    all_values = []
                    with open(filename, "w") as file:
                        file.write(version_option.get("Source", "") + "\n")
                        file.write(version_option.get("nsobid", "") + "\n")
                        file.write(version_option.get("offset", "") + "\n")
                        for key, value in version_option.items():
                            if key not in ["Source", "nsobid", "offset", "version", "Version"] and self.selected_options[key].get() == "On":
                                pattern = r"@enabled\n([\da-fA-F\s]+)\n@stop"
                                matches = re.findall(pattern, value)
                                for match in matches:
                                    hex_values = match.strip().split()
                                    all_values.extend(hex_values)
                                    # Print @enabled and then @stop at the end.
                        file.write("@enabled\n")
                        for i, value in enumerate(all_values):
                            file.write(value)
                            if i % 2 == 1 and i != len(all_values) - 1:
                                file.write("\n")
                            else:
                                file.write(" ")
                        file.write("\n@stop\n")
                if self.mode == "Yuzu":
                    qtconfig = get_config_parser()
                    qtconfig.optionxform = lambda option: option
                    qtconfig.read(self.configdir)
                else:
                    qtconfig = None
                # Ensures that the patches are active
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "DFPS", action="remove")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Mod Manager Patches", action="remove")
                # To maximize compatbility with old version of Mod Folders and Mod Manager.
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Visual Improvements", action="add")
                # Update Visual Improvements MOD.
                with open(ini_file_path, 'w') as configfile:
                    config.write(configfile)

        def UpdateSettings():
            Setting_folder = None
            SettingGithubFolder = None
            Setting_selection = self.selected_settings.get()
            if Setting_selection == "No Change":
                print("No Yuzu Settings have been changed!")
                return
            elif Setting_selection == "Steamdeck":
                     Setting_folder = "Steamdeck"
                     SettingGithubFolder = "scripts/settings/Applied%20Settings/Steamdeck/0100F2C0115B6000.ini"
                     print("Installing steamdeck Yuzu preset")
            elif Setting_selection == "AMD":
                     Setting_folder = "AMD"
                     SettingGithubFolder = 'scripts/settings/Applied%20Settings/AMD/0100F2C0115B6000.ini'
                     print("Installing AMD Yuzu Preset")
            elif Setting_selection == "Nvidia":
                     Setting_folder = "Nvidia"
                     SettingGithubFolder = 'scripts/settings/Applied%20Settings/Nvidia/0100F2C0115B6000.ini'
                     print("Installing Nvidia Yuzu Preset")
            elif Setting_selection == "High End Nvidia":
                     Setting_folder = "High End Nvidia"
                     SettingGithubFolder = 'scripts/settings/Applied%20Settings/High%20End%20Nvidia/0100F2C0115B6000.ini'
                     print("Installing High End Nvidia Yuzu Preset")
            if Setting_selection is not None:
                    repo_url = 'https://github.com/MaxLastBreath/TOTK-mods'
                    Setting_directory = self.TOTKconfig
                    raw_url = f'{repo_url}/raw/main/{SettingGithubFolder}'
                    response = requests.get(raw_url)
                    if response.status_code == 200:
                        with open(Setting_directory, "wb") as file:
                            file.write(response.content)
                        print("Successfully Installed TOTK Yuzu preset settings!")
                        resolution = self.resolution_var.get()
                        Resindex = self.dfps_options.get("ResolutionNames").index(resolution)
                        current_res = self.dfps_options.get("ResolutionValues", [""])[Resindex].split("x")[1]
                        proper_res = float(current_res)
                    else:
                        print(f"Failed to download file from {raw_url}. Status code: {response.status_code}")
                        return
                    if proper_res > 1080:
                        configfile = self.TOTKconfig
                        config = configparser.ConfigParser()
                        config.read(configfile)
                        if config.has_option("Renderer", "resolution_setup\\use_global"):
                            config.remove_option("Renderer", "resolution_setup\\use_global")
                        if config.has_option("Renderer", "resolution_setup\\default"):
                            config.remove_option("Renderer", "resolution_setup\\default")
                        if config.has_option("Renderer", "resolution_setup"):
                            config.remove_option("Renderer", "resolution_setup")

                        # Remove existing options in Core section
                        if config.has_option("Core", "use_unsafe_extended_memory_layout\\use_global"):
                            config.remove_option("Core", "use_unsafe_extended_memory_layout\\use_global")
                        if config.has_option("Core", "use_unsafe_extended_memory_layout\\default"):
                            config.remove_option("Core", "use_unsafe_extended_memory_layout\\default")
                        if config.has_option("Core", "use_unsafe_extended_memory_layout"):
                            config.remove_option("Core", "use_unsafe_extended_memory_layout")
                        if config.has_option("Core", "memory_layout_mode\\use_global"):
                            config.remove_option("Core", "memory_layout_mode\\use_global")
                        if config.has_option("Core", "memory_layout_mode\\default"):
                            config.remove_option("Core", "memory_layout_mode\\default")
                        if config.has_option("Core", "memory_layout_mode"):
                            config.remove_option("Core", "memory_layout_mode")
                        # Add new values
                        config.set("Renderer", "resolution_setup\\use_global", "false")
                        config.set("Renderer", "resolution_setup\\default","false")
                        config.set("Renderer", "resolution_setup", "2")

                        config.set("Core", "use_unsafe_extended_memory_layout\\use_global", "false")
                        config.set("Core", "use_unsafe_extended_memory_layout\\default", "false")
                        config.set("Core", "use_unsafe_extended_memory_layout", "true")
                        config.set("Core", "memory_layout_mode\\use_global", "false")
                        config.set("Core", "memory_layout_mode\\default", "false")
                        config.set("Core", "memory_layout_mode", "1")
                        with open(configfile, "w") as configfile:
                            config.write(configfile)
            else:
                print("Selected option has no associated setting folder.")

        def DownloadDFPS():
            # Make sure DFPS is enabled.
            if self.mode == "Yuzu":
                qtconfig = get_config_parser()
                qtconfig.optionxform = lambda option: option
                qtconfig.read(self.configdir)
            else:
                qtconfig = None
            modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "DFPS", action="remove")

            config = configparser.ConfigParser()
            config.read(self.config)
            if not config.has_section("Updates"):
                config.add_section("Updates")
                config.set("Updates", "dfps", "1.0.0")
                with open(self.config, "w") as configfile:
                    config.write(configfile)
            try:
                latest_dfps_version = config.get("Updates", "dfps")
            except NoOptionError as e:
                # Handle the case when "dfps" option doesn't exist
                config.set("Updates", "dfps", "1.0.0")
                with open(self.config, "w") as configfile:
                    config.write(configfile)
                latest_dfps_version = "1.0.0"
            print(f"Successfully updated config!")

            current_dfps_version = self.dfps_options.get("DFPS Version")
            # Start of DFPS file check.
            if current_dfps_version != latest_dfps_version or not os.path.exists(os.path.join(self.load_dir, "DFPS", "exefs")):
                dfps_directory = os.path.join(self.load_dir, "DFPS", "exefs")
                os.makedirs(dfps_directory, exist_ok=True)
                file_urls = [
                    {
                        "url": "https://github.com/MaxLastBreath/TOTK-mods/raw/main/scripts/DFPS/main.npdm",
                        "save_path": os.path.join(dfps_directory, "main.npdm")
                    },
                    {
                        "url": "https://github.com/MaxLastBreath/TOTK-mods/raw/main/scripts/DFPS/subsdk9",
                        "save_path": os.path.join(dfps_directory, "subsdk9")
                    }
                ]
                for file_info in file_urls:
                    url = file_info["url"]
                    save_path = file_info["save_path"]

                    print("Checking for updates")
                    Manager.download_file(url, save_path)
                # Update Config File
                config.set("Updates", "dfps", current_dfps_version)
                with open(self.config, "w") as configfile:
                    config.write(configfile)
            else:
                print("You already have the latest DFPS version and the folder exists!")

        def DownloadUI():
            if self.mode == "Yuzu":
                qtconfig = get_config_parser()
                qtconfig.optionxform = lambda option: option
                qtconfig.read(self.configdir)
            else:
                qtconfig = None
            #dirs
            Blackscreen = os.path.join(self.load_dir, "BlackscreenFIX")
            Xbox = os.path.join(self.load_dir, "Xbox UI")
            Ps4 = os.path.join(self.load_dir, "Playstation UI")
            #ui
            ui_mod_folder = None
            CurrentFolder = None
            ui_selection = self.ui_var.get()
            if ui_selection == "None":
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Xbox UI", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Playstation UI", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "BlackscreenFix", action="add")
                if self.mode == "Ryujinx":
                    if os.path.exists(Ps4):
                       shutil.rmtree(Ps4)
                    if os.path.exists(Blackscreen):
                       shutil.rmtree(Blackscreen)
                    if os.path.exists(Xbox):
                       shutil.rmtree(Xbox)
                print("No UI Selected, Disabling all UI mods!")
            elif ui_selection == "PS4":
                if self.mode == "Ryujinx":
                    if os.path.exists(Xbox):
                       shutil.rmtree(Xbox)
                    if os.path.exists(Blackscreen):
                       shutil.rmtree(Blackscreen)
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Xbox UI", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "BlackscreenFix", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Playstation UI", action="remove")
                ui_mod_folder = "Playstation UI"
                CurrentFolder = "scripts/UI/Playstation%20UI/"
            elif ui_selection == "Xbox":
                if self.mode == "Ryujinx":
                    if os.path.exists(Ps4):
                       shutil.rmtree(Ps4)
                    if os.path.exists(Blackscreen):
                       shutil.rmtree(Blackscreen)
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Playstation UI", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "BlackscreenFix", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Xbox UI", action="remove")
                ui_mod_folder = "Xbox UI"
                CurrentFolder = 'scripts/UI/Xbox%20UI/'
            elif ui_selection == "Black Screen Fix":
                if self.mode == "Ryujinx":
                    if os.path.exists(Ps4):
                       shutil.rmtree(Ps4)
                    if os.path.exists(Xbox):
                       shutil.rmtree(Xbox)
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Playstation UI", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "Xbox UI", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "BlackscreenFix", action="remove")
                ui_mod_folder = "BlackscreenFix"
                CurrentFolder = 'scripts/UI/BlackscreenFix/'

            if ui_mod_folder is not None:
                    repo_url = 'https://api.github.com/repos/MaxLastBreath/TOTK-mods'
                    folder_path = f'{CurrentFolder}'
                    Mod_directory = os.path.join(self.load_dir, f'{ui_mod_folder}')
                    if os.path.exists(Mod_directory):
                        print(f"The UI mod folder '{ui_mod_folder}' already exists. Skipping download.")
                        return
                    api_url = f'{repo_url}/contents/{folder_path}'
                    response = requests.get(api_url)

                    if response.status_code == 200:
                        contents = response.json()
                        os.makedirs(Mod_directory, exist_ok=True)
                        Manager.copy_files_and_subfolders(contents, Mod_directory)
                        return
                    else:
                        print("failed to retrive folder and contents")

        def DownloadFP():
            if self.mode == "Yuzu":
                qtconfig = get_config_parser()
                qtconfig.optionxform = lambda option: option
                qtconfig.read(self.configdir)
            else:
                qtconfig = None

            FP_mod_folder = None
            FPCurrentFolder = None
            FP_selection = self.fp_var.get()
            fov70 = os.path.join(self.load_dir, "First Person 70 FOV")
            fov90 = os.path.join(self.load_dir, "First Person 90 FOV")
            fov110 = os.path.join(self.load_dir, "First Person 110 FOV")
            if FP_selection == "Off":
                if self.mode == "Ryujinx":
                    if os.path.exists(fov70):
                       shutil.rmtree(fov70)
                    if os.path.exists(fov90):
                       shutil.rmtree(fov90)
                    if os.path.exists(fov110):
                       shutil.rmtree(fov110)
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 110 FOV", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 90 FOV", action="add")
                modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 70 FOV", action="add")
                print("Selected Third Person, removing ALL First Person Mods!")

            elif FP_selection == "70 FOV":
                    FP_mod_folder = "First Person 70 FOV"
                    FPCurrentFolder = "scripts/UI/First%20Person%20FOV%2070/"
                    if self.mode == "Ryujinx":
                        if os.path.exists(fov90):
                            shutil.rmtree(fov90)
                        if os.path.exists(fov110):
                            shutil.rmtree(fov110)
                    modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 110 FOV", action="add")
                    modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 90 FOV", action="add")
                    modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 70 FOV", action="remove")

            elif FP_selection == "90 FOV":
                    FP_mod_folder = "First Person 90 FOV"
                    FPCurrentFolder = 'scripts/UI/First%20Person%20FOV%2090/'
                    if self.mode == "Ryujinx":
                        if os.path.exists(fov70):
                            shutil.rmtree(fov70)
                        if os.path.exists(fov110):
                            shutil.rmtree(fov110)
                    modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 110 FOV", action="add")
                    modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 70 FOV", action="add")
                    modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 90 FOV", action="remove")

            elif FP_selection == "110 FOV":
                    FP_mod_folder = "First Person 110 FOV"
                    FPCurrentFolder = 'scripts/UI/First%20Person%20FOV%20110/'
                    if self.mode == "Ryujinx":
                        if os.path.exists(fov70):
                            shutil.rmtree(fov70)
                        if os.path.exists(fov90):
                            shutil.rmtree(fov90)
                    modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 70 FOV", action="add")
                    modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 90 FOV", action="add")
                    modify_disabled_key(self.configdir, self.load_dir, qtconfig, self.title_id, "First Person 100 FOV", action="remove")

            if FP_mod_folder is not None:
                    repo_url = 'https://api.github.com/repos/MaxLastBreath/TOTK-mods'
                    FPfolder_path = f'{FPCurrentFolder}'
                    FPMod_directory = os.path.join(self.load_dir, f'{FP_mod_folder}')

                    if os.path.exists(FPMod_directory):
                        print(f"The FP mod folder '{FP_mod_folder}' already exists. Skipping download.")
                        return

                    api_url = f'{repo_url}/contents/{FPfolder_path}'
                    response = requests.get(api_url)

                    if response.status_code == 200:
                        contents = response.json()
                        os.makedirs(FPMod_directory, exist_ok=True)
                        Manager.copy_files_and_subfolders(contents, FPMod_directory)
                        return
                    else:
                        print("failed to retrive folder and contents")

        # Execute tasks and make a Progress Window.
        progress_window = Toplevel(self.window)
        progress_window.title("Downloading")
        window_width = 300
        window_height = 100
        screen_width = progress_window.winfo_screenwidth()
        screen_height = progress_window.winfo_screenheight()
        x_coordinate = (screen_width - window_width) // 2
        y_coordinate = (screen_height - window_height) // 2
        progress_window.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
        progress_window.resizable(False, False)
        total_iterations = 100
        progress_bar = ttk.Progressbar(progress_window, mode="determinate", maximum=total_iterations)
        progress_bar.pack(pady=20)
        task_thread = threading.Thread(target=run_tasks)
        task_thread.start()