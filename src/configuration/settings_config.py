from ttkbootstrap import *
import ttkbootstrap as ttk
from _tkinter import TclError
from configuration.settings import *
from modules.GameManager.LaunchManager import LaunchManager
from modules.scaling import scale, sf
from modules.colors import Color
from modules.FrontEnd.CanvasMgr import Canvas_Create

class Setting:
    _window = None
    _manager = None
    w_scale_var = None
    backup_var = None
    backup_cheat_var = None
    ani_var = None

    # Initialize after the window in manager is set.
    def __init__(self, manager):
        self.window = manager._window
        self._manager = manager
        self.Colors = Color()
        self.config = configparser.ConfigParser()
        self.config.read(localconfig, encoding="utf-8")

    def settingswindow(self, style, canvases):
        self.style = style
        self.createwindow()
        canvas_obj = self.canvas(canvases)
        self.loadconfig(canvas_obj)

    def clear(self, canvas, window, canvases=list):
        canvases.remove(canvas)
        canvas.destroy()
        window.destroy()

    def canvas(self, canvases=list):
        window = self.window
        canvas_obj = ttk.Canvas(name="settings", master=window, width=scale(400), height=scale(500))
        self.window.protocol("WM_DELETE_WINDOW_1", lambda: self.clear(canvas_obj, window, canvases))
        canvas_obj.pack()
        canvases.append(canvas_obj)

        row = 40
        cul_tex = 40
        cul_sel = 180

        # font dropdown menu
        font_list = ["Arial", "Georgia", "Calibri", "Triforce", "Segoe", "The Wild Breath of Zelda", "Times New Roman", "Tahoma", "Impact", "Lucida", "Bahnschrift"]
        font_list.sort()
        self.font_var = Canvas_Create().create_combobox(
            master=window, canvas=canvas_obj,
            text="Select font:",
            variable="Arial", values=font_list,
            row=row, cul=cul_tex,
            tags=["text"], tag=None,
            description_name="fonts",
            width=100
        )
        row += 40

        # color dropdown menu

        item_list = self.Colors.getlist()
        item_list.sort()
        canvas_obj.create_rectangle(scale(cul_sel+110), scale(row-10), scale(cul_sel+110+20), scale(row+10), fill="red", tags="swatch1")
        self.color_var = Canvas_Create().create_combobox(
            master=window, canvas=canvas_obj,
            text="Text Color:",
            variable="cyan", values=item_list,
            row=row, cul=cul_tex,
            tags=["text"], tag=None,
            description_name="Text Colors",
            width=100,
            command=lambda event: self.swatch_color(event, canvas_obj, self.color_var, "swatch1")
        )
        row += 40

        canvas_obj.create_rectangle(scale(cul_sel + 110), scale(row - 10), scale(cul_sel + 110 + 20), scale(row + 10), fill="red", tags="swatch2")
        self.outline_var = Canvas_Create().create_combobox(
            master=window, canvas=canvas_obj,
            text="Shadow Color:",
            variable="purple", values=item_list,
            row=row, cul=cul_tex,
            tags=["text"], tag=None,
            description_name="Text Colors",
            width=100,
            command=lambda event: self.swatch_color(event, canvas_obj, self.outline_var, "swatch2")
        )
        row += 40

        canvas_obj.create_rectangle(scale(cul_sel + 110), scale(row - 10), scale(cul_sel + 110 + 20), scale(row + 10), fill="red", tags="swatch3")
        self.active_var = Canvas_Create().create_combobox(
            master=window, canvas=canvas_obj,
            text="Active Text Color:",
            variable="red", values=item_list,
            row=row, cul=cul_tex,
            tags=["text"], tag=None,
            description_name="Text Colors",
            width=100,
            command=lambda event: self.swatch_color(event, canvas_obj, self.active_var, "swatch3")
        )
        row += 40
        # style dropdown menu
        style_list = self.style.theme_names()
        self.style_var = Canvas_Create().create_combobox(
            master=window, canvas=canvas_obj,
            text="Choose GUI Style:",
            variable="flatly", values=style_list,
            row=row, cul=cul_tex,
            tags=["text"], tag=None,
            description_name="GUI-Theme",
            width=100
        )
        row += 40

        # on/off scale with windows.
        values = ["On", "Off", "1.0x", "1.5x", "2.0x", "2.5x", "3.0x"]
        self.w_scale_var = Canvas_Create().create_combobox(
            master=window, canvas=canvas_obj,
            text="Scale with Windows:",
            variable="On", values=values,
            row=row, cul=cul_tex,
            tags=["text"], tag=None,
            description_name="Windows Scaling",
            width=100
        )
        row += 40

        # on/off Auto Backup
        self.backup_var = Canvas_Create().create_checkbutton(
            master=window, canvas=canvas_obj,
            text="Auto Backup",
            variable="Off",
            row=row, cul=cul_tex,
            tags=["text"], tag=None,
            description_name="Auto Backup",
        )
        row += 40

        # on/off Auto Backup for Cheats
        self.backup_cheat_var = Canvas_Create().create_checkbutton(
            master=window, canvas=canvas_obj,
            text="Auto Backup(Cheats):",
            variable="On",
            row=row, cul=cul_tex,
            tags=["text"], tag=None,
            description_name="Auto Backup Cheats",
        )
        row += 40

        # on/off Animations
        self.ani_var = Canvas_Create().create_checkbutton(
            master=window, canvas=canvas_obj,
            text="GUI Animations:",
            variable="On",
            row=row, cul=cul_tex,
            tags=["text"], tag=None,
            description_name="Gui Animations",
        )
        row += 40

        Canvas_Create().create_label(
            master=window, canvas=canvas_obj,
            text="Select Game File",
            row=row, cul=cul_tex,
            tags=["Button"], tag=None,
            description_name="Apply",
            command=lambda event : LaunchManager.select_game_file(self._manager)
        )
        row += 40

        Canvas_Create().create_button(
            master=window, canvas=canvas_obj,
            btn_text="Apply",
            row=row, cul=cul_tex, width=6, padding=5,
            tags=["Button"], tag=None,
            description_name="Apply",
            style="success",
            command=lambda: self.saveconfig(self._manager.all_canvas)
        )
        return canvas_obj

    def saveconfig(self, canvases=list):
        #print("font_var:", self.font_var.get())
        #print("color_var:", self.color_var.get())
        #print("style_var:", self.style_var.get())
        #print("w_scale_var:", self.w_scale_var.get())
        #print("backup_var:", self.backup_var.get())
        #print("backup_cheat_var:", self.backup_cheat_var.get())
        #print("ani_var:", self.ani_var.get())

        # Update Settings too.
        get_setting()

        config = configparser.ConfigParser()
        config.read(localconfig, encoding="utf-8")
        if not config.has_section("Settings"):
            config["Settings"] = {}
        config["Settings"]["font"] = self.font_var.get()
        config["Settings"]["color"] = self.color_var.get()
        config["Settings"]["shadow_color"] = self.outline_var.get()
        config["Settings"]["active_color"] = self.active_var.get()
        config["Settings"]["style"] = self.style_var.get()
        config["Settings"]["scale"] = self.w_scale_var.get()
        config["Settings"]["backup"] = self.backup_var.get()
        config["Settings"]["cheat-backup"] = self.backup_cheat_var.get()
        config["Settings"]["animation"] = self.ani_var.get()

        with open(localconfig, 'w', encoding="utf-8") as file:
            config.write(file)

        color = Color()
        new_font = (self.font_var.get(), 13)
        new_text_color = color.get(self.color_var.get())
        new_active_color = color.get(self.active_var.get())
        new_outline_color = color.get(self.outline_var.get())
        theme = self.style_var.get()
        self.style.theme_use(theme)
        try:
            for canvas in canvases:
                canvas.itemconfig("active_text", activefill=new_active_color)
                canvas.itemconfig("text", fill=new_text_color, font=new_font)
                canvas.itemconfig("outline", fill=new_outline_color, font=new_font)
        except TclError as e:
            print(e)

    def loadconfig(self, canvas):
        config = configparser.ConfigParser()
        config.read(localconfig, encoding="utf-8")

        self.font_var.set(config.get("Settings", "font", fallback=font))
        self.color_var.set(config.get("Settings", "color", fallback=tcolor))
        self.outline_var.set(config.get("Settings", "shadow_color", fallback=toutline))
        self.active_var.set(config.get("Settings", "active_color", fallback=tactive))
        self.style_var.set(config.get("Settings", "style", fallback=theme))
        self.w_scale_var.set(config.get("Settings", "scale", fallback=w_scale))
        self.backup_var.set(config.get("Settings", "backup", fallback=is_auto_backup))
        self.backup_cheat_var.set(config.get("Settings", "cheat-backup", fallback=is_cheat_backup))
        self.ani_var.set(config.get("Settings", "animation", fallback=is_animation))

        self.swatch_color(event=None, canvas=canvas, var=self.color_var, swatch="swatch1")
        self.swatch_color(event=None, canvas=canvas, var=self.outline_var, swatch="swatch2")
        self.swatch_color(event=None, canvas=canvas, var=self.active_var, swatch="swatch3")

        fonty = get_setting("f")
        newfont = (fonty, 13)
        canvas.itemconfig("active_text", activefill=self.Colors[self.active_var.get()])
        canvas.itemconfig("text", fill=self.Colors[self.color_var.get()], font=newfont)
        canvas.itemconfig("outline", fill=self.Colors[self.outline_var.get()], font=newfont)

    def createwindow(self):
        self.window = ttk.Window(scaling=sf)
        self.window.title(f"Optimizer Settings")
        window_width = scale(400)
        window_height = scale(500)
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.window.resizable(False, False)

    def swatch_color(self, event, canvas, var, swatch):
        color = self.Colors[var.get()]
        canvas.itemconfig(swatch, fill=color)
