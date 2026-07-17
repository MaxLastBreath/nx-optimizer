from modules.FrontEnd.ImageButton import *
from PIL import Image, ImageTk, ImageFilter, ImageOps
from idlelib.tooltip import Hovertip
from tkinter import *
from configuration.settings import *
from run_config import __ROOT__
import ttkbootstrap as ttk
import string
import random


def next_index(event, var: ttk.Variable, list: list, increase: int = 1, command=None):
    value = str(var.get())
    string_list = [str(item) for item in list]
    index = string_list.index(value)
    index += increase
    if index == len(list):
        index = 0
    if index < 0:
        index = len(list) - 1
    var.set(list[index])
    if command is not None:
        command(event)


def change_scale(event:None, var: ttk.Variable, lo:float, hi:float, increments: float, command=None):  # fmt: skip
    new_value = float(var.get()) + increments
    if new_value > float(hi):
        new_value = float(hi)

    if new_value < float(lo):
        new_value = float(lo)

    var.set(str(new_value))

    if command is not None:
        command(event)


def update_text(event:None, canvas: ttk.Canvas, name: str, var: ttk.Variable, type: str = "s32"):  # fmt: skip
    if type == "s32":
        var.set(round(float(var.get())))
        canvas.itemconfig(name, text=int(var.get()))
    if type == "f32":
        var.set(round(float(var.get()) * 10) / 10)
        canvas.itemconfig(name, text=float(var.get()))


def toggle(event, var: ttk.Variable):
    if var.get() == "On":
        var.set("Off")
    else:
        var.set("On")


class ImageContext:
    path: str = ""
    object: ttk.PhotoImage = None

    def __init__(cls, _path, _object):
        cls.path = _path
        cls.object = _object


class Canvas_Create:
    """TOTK Optimizer framework for handling images, toolboxes etc..."""

    LoadedImages: list[ImageContext] = []
    tooltip = None
    tooltip_active = None
    is_Ani_running = True
    is_Ani_Paused = False

    @classmethod
    def create_combobox(
        cls,
        canvas: ttk.Canvas,
        text: str,
        master: ttk.Window,
        description_name: str = None,
        text_description: str = None,
        variable: ttk.StringVar = any,
        values=[],
        row: int = 40,
        cul: int = 40,
        drop_cul: int = 180,
        width: int = 150,
        style: str = "warning",
        tags: list[str] = [],
        tag: str = None,
        command: any = None,
        is_active: bool = True,
    ) -> ttk.Combobox:

        tags = list(tags) if tags else []

        # create text
        active_color_new = active_color
        if tag is not None:
            tags.append(tag)
        if is_active is False:
            active_color_new = None
        elif is_active is True:
            tags.append("active_text")

        # add outline and user-tag to the outlined text.
        outline_tag = ["outline", tag]

        for item in tags:
            outline_tag.append(item)

        # create an outline to the text.
        canvas.create_text(
            scale(cul) + scale(1),
            scale(row) + scale(1),
            text=text,
            anchor="w",
            fill=outline_color,
            font=textfont,
            tags=outline_tag,
        )

        # create the text and the variable for the dropdown.
        new_variable = ttk.StringVar(master=master, value=variable)
        text_line = canvas.create_text(
            scale(cul),
            scale(row),
            text=text,
            anchor="w",
            fill=textcolor,
            font=textfont,
            tags=tags,
            activefil=active_color_new,
        )

        # create combobox
        dropdown_variable = ttk.Combobox(
            master=master,
            textvariable=new_variable,
            values=values,
            state="readonly",
            bootstyle=style,
        )

        dropdown_window = canvas.create_window(
            scale(drop_cul),
            scale(row),
            anchor="w",
            window=dropdown_variable,
            width=scale(width),
            height=CBHEIGHT,
            tags=tags,
        )

        # bind canvas
        dropdown_variable.bind("<<ComboboxSelected>>", command)

        # attempt to make a Hovertip
        cls.read_description(
            canvas=canvas,
            option=description_name,
            text=text_description,
            position_list=[dropdown_variable, text_line],
            master=master,
        )

        canvas.tag_bind(
            text_line,
            "<Button-1>",
            lambda event: next_index(event, new_variable, values, 1, command),
        )
        canvas.tag_bind(
            text_line,
            "<Button-3>",
            lambda event: next_index(event, new_variable, values, -1, command),
        )

        row += 40
        return dropdown_variable

    @classmethod
    def create_scale(
        cls,
        canvas: ttk.Canvas,
        text: str,
        master: ttk.Window,
        description_name: str = None,
        text_description: str = None,
        variable: ttk.Variable = any,
        scale_from=1,
        scale_to=100,
        increments=5,
        row: int = 40,
        cul: int = 40,
        drop_cul: int = 180,
        width: int = 150,
        style: str = "warning",
        type: str = "s32",
        tags: list[str] = [],
        tag: str = None,
        command: None = None,
        is_active: bool = True,
    ) -> ttk.Variable:

        tags = list(tags) if tags else []

        # create text
        active_color_new = active_color
        if tag is not None:
            tags.append(tag)
        if is_active is False:
            active_color_new = None
        elif is_active is True:
            tags.append("active_text")

        # add outline and user-tag to the outlined text.
        outline_tag = ["outline", tag]

        for item in tags:
            outline_tag.append(item)

        # create an outline to the text.
        canvas.create_text(
            scale(cul) + scale(1),
            scale(row) + scale(1),
            text=text,
            anchor="w",
            fill=outline_color,
            font=textfont,
            tags=outline_tag,
        )

        # create the text and the variable for the dropdown.
        new_variable = ttk.StringVar(master=master, value=variable)
        text_line = canvas.create_text(
            scale(cul),
            scale(row),
            text=text,
            anchor="w",
            fill=textcolor,
            font=textfont,
            tags=tags,
            activefil=active_color_new,
        )

        def custom_command():
            update_text(None, canvas, text, new_variable, type=type)
            if command:
                command(None)

        new_variable.trace_add("write", lambda *args: custom_command())


        # create scale box
        scale_box = ttk.Scale(
            master=master,
            from_=scale_from,
            to=scale_to,
            command=lambda e: custom_command(),
            length=width,
            style=style,
            variable=new_variable,
        )

        win = canvas.create_window(
            scale(drop_cul),
            scale(row),
            anchor="w",
            window=scale_box,
            width=scale(width),
            height=scale(12),
            tags=tags,
        )

        # attempt to make a Hovertip
        cls.read_description(
            canvas=canvas,
            option=description_name,
            position_list=[scale_box, text_line],
            master=master,
        )

        tags.append(text)
        outline_tag.append(text)

        # Shows the value from the scale.
        canvas.create_text(
            scale(cul + width + 25) + scale(1),
            scale(row) + scale(1),
            text="NOT SET",
            anchor="w",
            fill=outline_color,
            font=textfont,
            tags=outline_tag,
        )

        text_line_value = canvas.create_text(
            scale(cul + width + 25),
            scale(row),
            text="NOT SET",
            anchor="w",
            fill=textcolor,
            font=textfont,
            tags=tags,
            activefil=active_color_new,
        )

        cls.read_description(
            canvas=canvas,
            option=description_name,
            text=text_description,
            position_list=[scale_box, text_line],
            master=master,
        )

        canvas.tag_bind(
            text_line,
            "<Button-1>",
            lambda event: change_scale(
                event,
                new_variable,
                lo=scale_from,
                hi=scale_to,
                increments=increments,
            ),
        )

        canvas.tag_bind(
            text_line,
            "<Button-3>",
            lambda event: change_scale(
                event,
                new_variable,
                lo=scale_from,
                hi=scale_to,
                increments=-increments,
            ),
        )

        canvas.tag_bind(
            text_line_value,
            "<Button-1>",
            lambda event: change_scale(
                event,
                new_variable,
                lo=scale_from,
                hi=scale_to,
                increments=increments,
            ),
        )

        canvas.tag_bind(
            text_line_value,
            "<Button-3>",
            lambda event: change_scale(
                event,
                new_variable,
                lo=scale_from,
                hi=scale_to,
                increments=-increments,
            ),
        )

        return new_variable

    @classmethod
    def create_checkbutton(
        cls,
        master: ttk.Window,
        canvas: ttk.Canvas,
        text: str,
        description_name: str = None,
        text_description: str = None,
        variable: ttk.Variable = any,
        row: int = 40,
        cul: int = 40,
        drop_cul: int = 180,
        tags: list[str] = [],
        tag: str = None,
        command: any = None,
        is_active: bool = True,
        style: str = "success",
    ) -> ttk.StringVar:

        tags = list(tags) if tags else []

        # create text
        active_color_new = active_color
        if tag is not None:
            tags.append(tag)
        if is_active is False:
            active_color_new = None
        elif is_active is True:
            tags.append("active_text")

        # add outline and user-tag to the outlined text.
        outline_tag = ["outline", tag]

        for item in tags:
            outline_tag.append(item)

        # create an outline to the text.
        canvas.create_text(
            scale(cul) + scale(1),
            scale(row) + scale(1),
            text=text,
            anchor="w",
            fill=outline_color,
            font=textfont,
            tags=outline_tag,
        )

        # create the text and the variable for the dropdown.
        Variable = ttk.StringVar(master=master, value=variable)

        text_line = canvas.create_text(
            scale(cul),
            scale(row),
            text=text,
            anchor="w",
            fill=textcolor,
            font=textfont,
            tags=tags,
            activefil=active_color_new,
        )

        # create checkbutton
        try:
            checkbutton = ttk.Checkbutton(
                master=master,
                variable=Variable,
                onvalue="On",
                offvalue="Off",
                state="readonly",
                command=command,
                bootstyle=style,
            )
        except Exception as e:
            log.error(e)

        checkbutton_window = canvas.create_window(
            scale(drop_cul),
            scale(row),
            anchor="w",
            window=checkbutton,
            width=scale(11),
            height=scale(11),
            tags=tags,
        )

        # attempt to make a Hover tip
        canvas.tag_bind(text_line, "<Button-1>", lambda event: toggle(event, Variable))

        cls.read_description(
            canvas=canvas,
            option=description_name,
            position_list=[checkbutton, text_line],
            text=text_description,
            master=master,
        )

        row += 40
        return Variable

    @classmethod
    def create_button(
        cls,
        master: ttk.Window,
        canvas: ttk.Canvas,
        text: str,
        description_name: str = None,
        text_description: str = None,
        textvariable: ttk.StringVar = None,
        row: int = 40,
        cul: int = 40,
        width: int | None = None,
        padding: int | None = None,
        pos: str = "w",
        tags: list[str] = [],
        tag: str = None,
        style: str = "default",
        command: any = None,
    ):

        tags = list(tags) if tags else []

        # create text
        if tag is not None:
            tags.append(tag)
        # create button

        button = ttk.Button(
            master=master,
            text=text,
            command=command,
            textvariable=textvariable,
            bootstyle=style,
            padding=padding,
        )

        canvas.create_window(
            scale(cul),
            scale(row),
            width=scale(width * 10),
            anchor=pos,
            window=button,
            tags=tags,
        )

        cls.read_description(
            canvas=canvas,
            option=description_name,
            position_list=[button],
            text=text_description,
            master=master,
        )
        return

    @classmethod
    def create_label(
        cls,
        master: ttk.Window,
        canvas: ttk.Canvas,
        text: str,
        description_name: str = None,
        text_description: str = None,
        font: str = textfont,
        color: str = textcolor,
        active_fill: bool = None,
        row: int = 40,
        cul: int = 40,
        anchor: str = "w",
        justify: str = "left",
        tags: list[str] = [],
        tag: str = None,
        outline_tag: str = None,
        command: any = None,
    ):

        tags = list(tags) if tags else []

        # create text
        if tag is not None:
            tags.append(tag)
        if command is not None and active_fill is None:
            active_fill = active_color

        outline_tag = [outline_tag]
        for _tag in tags:
            outline_tag.append(_tag)

        # create an outline to the text.
        text_outline = canvas.create_text(
            scale(cul) + scale(1),
            scale(row) + scale(1),
            text=text,
            anchor=anchor,
            justify=justify,
            fill=outline_color,
            font=font,
            tags=outline_tag,
        )

        # create the text and the variable.
        text_line = canvas.create_text(
            scale(cul),
            scale(row),
            text=text,
            anchor=anchor,
            justify=justify,
            fill=color,
            font=font,
            tags=tags,
            activefil=active_fill,
        )

        canvas.tag_bind(text_line, "<Button-1>", command)
        cls.read_description(
            canvas=canvas,
            option=description_name,
            position_list=[text_line],
            text=text_description,
            master=master,
        )
        return text_line, text_outline  # return textID

    @classmethod
    def image_Button(
        cls,
        canvas: ttk.Canvas,
        row: int,
        cul: int,
        name: str | None = None,
        anchor: str = "nw",
        img_1: ttk.PhotoImage = any,
        img_2: ttk.PhotoImage = any,
        tags: list =[],
        isOn: bool = False,
        command: Callable = None,
        Type: ButtonToggle = ButtonToggle.Static,
    ) -> ImageButton:

        ImageBtn: ImageButton = ImageButton(
            canvas.master,
            canvas,
            name,
            CreateRandomTag(name),
            [img_1, img_2],
            Type=Type,
            isOn=isOn,
            tags=tags,
        )

        ImageBtn.BindImages(scale(cul), scale(row), anchor)
        ImageBtn.BindCommand(command)
        ImageBtn.MakeDynamic(Type)
        ImageBtn.AddAnimationToQueue()

        return ImageBtn

    @classmethod
    def set_image(
        cls,
        canvas: ttk.Canvas,
        row: int,
        cul: int,
        anchor: str = "nw",
        img: ttk.PhotoImage = any,
        tag: str | None = None,
        state: str = "normal",
    ):

        if tag is None:
            tag = random.choices(string.ascii_uppercase + string.digits, k=8)
            tag = "".join(tag)

        canvas.create_image(
            scale(cul), scale(row), anchor=anchor, image=img, state=state, tags=[tag]
        )

    @classmethod
    def read_description(
        cls,
        canvas: ttk.Canvas,
        option: str,
        text: str | None = None,
        position_list=[],
        master: ttk.Window = any,
    ):
        if f"{option}" not in description and text is None:
            return

        for position in position_list:
            try:
                canvas_item = canvas.find_withtag(position)
                if canvas_item:
                    if text is not None:
                        hover = text
                        cls.create_tooltip(canvas, master, position, hover)
                    else:
                        hover = description[f"{option}"]
                        cls.create_tooltip(canvas, master, position, hover)
                    break
            except TclError as e:
                if text is not None:
                    hover = text
                    Hovertip(position, f"{hover}", hover_delay=Hoverdelay)
                else:
                    hover = text
                    Hovertip(position, f"{hover}", hover_delay=Hoverdelay)

    @classmethod
    def create_tooltip(cls, canvas: ttk.Canvas, master: ttk.Window, position, hover):

        canvas.tag_bind(
            position,
            "<Enter>",
            lambda e: cls.show_tooltip(
                canvas=canvas,
                master=master,
                item=position,
                tool_text=hover,
            ),
        )

        canvas.tag_bind(position, "<Leave>", lambda e: cls.hide_tooltip())
        canvas.tag_bind(position, "<Return>", lambda e: cls.hide_tooltip())

    @classmethod
    def show_tooltip(
        cls,
        canvas: ttk.Canvas,
        master: ttk.Window,
        item,
        tool_text,
    ):
        import tkinter as Tk

        bbox = canvas.bbox(item)
        x, y = bbox[0], bbox[1]
        x += canvas.winfo_rootx()
        y += canvas.winfo_rooty()

        master.after(50)
        cls.tooltip = Tk.Toplevel(master=master)
        cls.tooltip.wm_overrideredirect(True)
        cls.tooltip.geometry(f"+{x + scale(20)}+{y + scale(25)}")

        tooltip_label = ttk.Label(
            master=cls.tooltip,
            text=tool_text,
            background="white",
            relief="solid",
            borderwidth=1,
            justify="left",
        )

        tooltip_label.pack()

        cls.tooltip_active = True

    @classmethod
    def hide_tooltip(cls):
        if cls.tooltip is not None:
            try:
                cls.tooltip.destroy()
            except Exception:
                pass
            cls.tooltip = None
        cls.tooltip_active = False

    @classmethod
    def focus(cls):
        # Handle animations and events during those animations.
        cls.is_Ani_Paused = False

    @classmethod
    def un_focus(cls):
        cls.is_Ani_Paused = True

    @classmethod
    def on_closing(cls, master):
        superlog.critical("User Exit Application.")
        cls.is_Ani_running = False
        master.destroy()

    @classmethod
    def get_UI_path(cls, file_name: str, folder_name: str = "GUI"):
        path = os.path.join(__ROOT__, folder_name, file_name)
        
        if not os.path.exists(path):
            path2 = os.path.join(__ROOT__, file_name)
            if os.path.exists(path2):
                return path2

            path2 = os.path.join(folder_name, file_name)
            if os.path.exists(path2):
                return path2
            
            path2 = os.path.join(file_name)
            if os.path.exists(path2):
                return path2

            raise FileNotFoundError(f"Couldn't find image: {file_name}")
        return path

    @classmethod
    def Photo_Image(
        cls,
        image_path=str,
        width: int | None = None,
        height: int | None = None,
        blur: int | None = None,
        mirror: bool = False,
        flip: bool = False,
        auto_contrast: bool = False,
        img_scale: int = None,
    ) -> PhotoImage:

        UI_path = cls.get_UI_path(image_path)
        image = ttk.Image.open(UI_path)
        if isinstance(img_scale, int) or isinstance(img_scale, float):
            width = int(width * img_scale)
            height = int(height * img_scale)
        if isinstance(width, int) and isinstance(height, int):
            image = image.resize((scale(width), scale(height)))
        if isinstance(blur, int):
            image = image.filter(ImageFilter.GaussianBlur(blur))
        if mirror is True:
            image = ImageOps.mirror(image)
        if flip is True:
            image = ImageOps.flip(image)
        if auto_contrast is True:
            image = ImageOps.autocontrast(image)
        new_photo_image = ImageTk.PhotoImage(image)

        return new_photo_image

    @classmethod
    def Change_Background_Image(cls, canvas: ttk.Canvas, _path: str):
        for item in cls.LoadedImages:
            if item.path == _path:
                canvas.itemconfig("background", image=item.object)
                return

        newImage = cls.Photo_Image(image_path=_path, width=1200, height=600, blur=2)

        cls.LoadedImages.append(ImageContext(_path, newImage))
        canvas.itemconfig("background", image=newImage)
