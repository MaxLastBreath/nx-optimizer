from idlelib.tooltip import Hovertip
from ttkbootstrap import *
from tkinter import *
from configuration.settings import *
import time
import ttkbootstrap as ttk


class Canvas:
    def __init__(self):
        self.tooltip = None
        self.window = None
        self.tooltip_active = None
        self.is_Ani_running = True
        self.is_Ani_Paused = False

    def create_combobox(self, master, canvas,
                        text, description_name=None, variable=any, values=[],
                        row=40, cul=40, drop_cul=180,
                        tags=[], tag=None, command=None):
        # create text
        if tag is not None:
            tags.append(tag)
        # add outline and user-tag to the outlined text.
        outline_tag = ["outline", tag]
        # create an outline to the text.
        canvas.create_text(
                           scale(cul) + scale(1),
                           scale(row) + scale(1),
                           text=text,
                           anchor="w",
                           fill=outlinecolor,
                           font=textfont,
                           tags=outline_tag
                           )
        # create the text and the variable for the dropdown.
        new_variable = tk.StringVar(value=variable)
        text_line = canvas.create_text(
                                       scale(cul),
                                       scale(row),
                                       text=text,
                                       anchor="w",
                                       fill=textcolor,
                                       font=textfont,
                                       tags=tags
                                       )

        # create comobbox
        dropdown = ttk.Combobox(
                                master=master,
                                textvariable=new_variable,
                                values=values,
                                state="readonly",
                                )

        dropdown_window = canvas.create_window(
                                               scale(drop_cul),
                                               scale(row),
                                               anchor="w",
                                               window=dropdown,
                                               width=scale(150),
                                               height=CBHEIGHT,
                                               tags=tag
                                               )
        # bind canvas
        dropdown.bind("<<ComboboxSelected>>", command)
        # attempt to make a Hovertip
        self.read_description(
                              canvas=canvas,
                              option=description_name,
                              position_list=[dropdown, text_line],
                              master=master
                              )
        row += 40
        return new_variable

    def create_checkbutton(
            self, master, canvas,
            text, description_name=None, variable=any,
            row=40, cul=40, drop_cul=180,
            tags=[], tag=None, command=any):
        # create text
        if tag is not None:
            tags.append(tag)
        # add outline and user-tag to the outlined text.
        outline_tag = ["outline", tag]
        # create an outline to the text.
        canvas.create_text(
                           scale(cul) + scale(1),
                           scale(row) + scale(1),
                           text=text,
                           anchor="w",
                           fill=outlinecolor,
                           font=textfont,
                           tags=outline_tag
                           )
        # create the text and the variable for the dropdown.
        new_variable = tk.StringVar(value=variable)
        text_line = canvas.create_text(
                                       scale(cul),
                                       scale(row),
                                       text=text,
                                       anchor="w",
                                       fill=textcolor,
                                       font=textfont,
                                       tags=tags,
                                       activefil="red",
                                       )

        # create checkbutton
        checkbutton = ttk.Checkbutton(
                                master=master,
                                variable=new_variable,
                                onvalue="On",
                                offvalue="Off",
                                state="readonly",
                                command=command,
                                bootstyle="danger"
                                )

        checkbutton_window = canvas.create_window(
                                               scale(drop_cul),
                                               scale(row),
                                               anchor="w",
                                               window=checkbutton,
                                               tags=tag
                                               )
        # attempt to make a Hovertip
        canvas.tag_bind(text_line, "<Button-1>", lambda event: self.toggle(event, new_variable))
        self.read_description(
                              canvas=canvas,
                              option=description_name,
                              position_list=[checkbutton, text_line],
                              master=master
                              )
        row += 40
        return new_variable

    def create_button(
            self, master, canvas,
            btn_text, description_name=None, textvariable=None,
            row=40, cul=40, width=None, padding=None, pos="w",
            tags=[], tag=None,
            style="default", command=any,
                      ):
        # create text
        if tag is not None:
            tags.append(tag)
        # create checkbutton

        button = ttk.Button(
            master=master,
            text=btn_text,
            command=command,
            textvariable=textvariable,
            bootstyle=style,
            padding=padding
        )

        canvas.create_window(
            scale(cul),
            scale(row),
            width=scale(width*10),
            anchor=pos,
            window=button,
            tags=tag
        )

        self.read_description(
            canvas=canvas,
            option=description_name,
            position_list=[button],
            master=master
        )
        return

    def create_label(self, master, canvas,
                        text, description_name=None, font=textfont, color=textcolor, activefil=None,
                        row=40, cul=40,
                        tags=[], tag=None, outline_tag=None, command=None
                     ):
        # create text
        if tag is not None:
            tags.append(tag)
        if command is not None:
            activefil = "red"
        # add outline and user-tag to the outlined text.
        if outline_tag is not None:
            outline_tag = [outline_tag, tag]
        # create an outline to the text.
        canvas.create_text(
                           scale(cul) + scale(1),
                           scale(row) + scale(1),
                           text=text,
                           anchor="w",
                           fill=outlinecolor,
                           font=font,
                           tags=outline_tag,
                           )
        # create the text and the variable for the dropdown.
        text_line = canvas.create_text(
                                       scale(cul),
                                       scale(row),
                                       text=text,
                                       anchor="w",
                                       fill=color,
                                       font=font,
                                       tags=tags,
                                       activefil=activefil,
                                       )
        canvas.tag_bind(text_line, "<Button-1>", command)
        self.read_description(
                              canvas=canvas,
                              option=description_name,
                              position_list=[text_line],
                              master=master
                              )

    def read_description(self, canvas, option, position_list=list, master=any):
        for position in position_list:
            try:
                if f"{option}" in description:
                    canvas_item = canvas.find_withtag(position)
                    if canvas_item:
                        canvas = canvas
                        hover = description[f"{option}"]
                        tooltip = None
                        self.create_tooltip(canvas, position, hover, master)
                        break

            except TclError as e:
                if f"{option}" in description:
                    hover = description[f"{option}"]
                    Hovertip(position, f"{hover}", hover_delay=Hoverdelay)

    def create_tooltip(self, canvas, position, hover, master):

        canvas.tag_bind(position, "<Enter>", lambda event: self.show_tooltip(
                                                                             event=event,
                                                                             item=position,
                                                                             tool_text=hover,
                                                                             the_canvas=canvas,
                                                                             master=master
                                                                             )
                        )

        canvas.tag_bind(position, "<Leave>", lambda event: self.hide_tooltip(event=event))
        canvas.tag_bind(position, "<Return>", lambda event: self.hide_tooltip(event))

    def show_tooltip(self, event, item, tool_text, the_canvas, master):
        bbox = the_canvas.bbox(item)
        x, y = bbox[0], bbox[1]
        x += the_canvas.winfo_rootx()
        y += the_canvas.winfo_rooty()

        master.after(50)
        self.tooltip = tk.Toplevel()
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.geometry(f"+{x + scale(20)}+{y + scale(25)}")
        tooltip_label = tk.Label(
                                 master=self.tooltip,
                                 text=tool_text,
                                 background="gray",
                                 relief="solid",
                                 borderwidth=1,
                                 justify="left"
                                 )
        tooltip_label.pack()
        self.tooltip_active = True

    def hide_tooltip(self, event):
        self.tooltip.destroy()
        self.tooltip_active = False

    def toggle(self, event, var):
        if var.get() == "On":
            var.set("Off")
        else:
            var.set("On")

    # Handle animations and events during those animations.
    def focus(self, event):
        self.is_Ani_Paused = False
        
    def unfocus(self, event):
        print("FFF")
        self.is_Ani_Paused = True

    def on_closing(self, master):
        print("Closing Window")
        self.is_Ani_running = False
        master.destroy()

    def canvas_animation(self, master, canvas):
        canvas.bind("<Enter>", self.focus)
        canvas.bind("<Leave>", self.unfocus)
        x = 0
        y = 0
        m = 1
        if FPS == 0.1:
            m = 2
        a = scale(m)
        while True:
            if self.is_Ani_running is False:
                return
            if self.is_Ani_Paused is False:
                print(self.is_Ani_Paused)
                if x <= 1000:
                    x += m
                    canvas.move("background", -a, 0)
                    time.sleep(FPS)
                if x >= 1000:
                    if y == 0:
                        canvas.move("background", scale(200), scale(300))
                    if y <= 300:
                        y += m
                        canvas.move("background", 0, -a)
                        time.sleep(FPS)
                    if y >= 300:
                        x = 0
                        y = 0
                        canvas.move("background", scale(800), 0)
            else:
                time.sleep(1)