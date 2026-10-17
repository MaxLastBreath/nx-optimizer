from modules.FrontEnd.CanvasMgr import Canvas_Create, ButtonToggle
from modules.FrontEnd.TextureMgr import TextureMgr
from configuration.settings import *
from modules.GameManager.Benchmarks import Benchmark
import ttkbootstrap as ttk

def load_UI_elements(manager, canvas: ttk.Canvas):
    from modules.FrontEnd.FrontEnd import Manager

    manager: Manager = manager

    # Images and Effects
    canvas.create_image(
        0, 0, anchor="nw", image=TextureMgr.Request("image.jpg"), tags="background"
    )

    canvas.create_image(
        0,
        0,
        anchor="nw",
        image=TextureMgr.Request("Legacy_BG.png"),
        tags="SWITCHOVERLAY",
    )

    canvas.create_image(
        0, 0, anchor="nw", image=TextureMgr.Request("ui_static_overlay"), tags="overlay"
    )

    Offset = 255

    Canvas_Create.create_label(
        master=canvas.master,
        canvas=canvas,
        text="Benchmark",
        font=("Triforce", 25),
        row=285 - Offset,
        cul=980,
        anchor="c",
        justify="c",
        tags=[Benchmark._label_tag],
    )

    # Canvas_Create.set_image(
    #     canvas=canvas,
    #     row=500,
    #     cul=980,
    #     anchor="c",
    #     img=TextureMgr.Request("benchmark_border.png"),
    #     tag="benchmark_border",
    # )

    ButonWidth = TextureMgr.Request("benchmark_cycle.png").width() - 30

    Canvas_Create.image_Button(
        canvas=canvas,
        row=500 - Offset,
        cul=980 - (ButonWidth * 1.4) / sf,
        anchor="c",
        img_1=TextureMgr.Request("benchmark_copy.png"),
        img_2=TextureMgr.Request("benchmark_copy_active.png"),
        command=lambda e: Benchmark.copy(),
        tags=["benchmark-button"]
    )

    Canvas_Create.image_Button(
        canvas=canvas,
        row=500 - Offset,
        cul=980,
        anchor="c",
        img_1=TextureMgr.Request("benchmark_loading.png"),
        img_2=TextureMgr.Request("benchmark_loading_active.png"),
        command=lambda e: Benchmark.ReloadBenchmarkInfo(),
        tags=["benchmark-button", "benchmark-reload"]
    )

    Canvas_Create.image_Button(
        canvas=canvas,
        row=500 - Offset ,
        cul=980 + (ButonWidth * 1.4) / sf,
        anchor="c",
        img_1=TextureMgr.Request("benchmark_cycle.png"),
        img_2=TextureMgr.Request("benchmark_cycle_active.png"),
        command=lambda e: Benchmark.cycle(),
        tags=["benchmark-button"]
    )

    Canvas_Create.create_label(
        master=manager._window,
        canvas=canvas,
        text=f"{gpu_name}\n" f"{CPU}\n" f"Memory: {total_memory}GB {FREQUENCY} MHz",
        description_name="Benchmarks",
        anchor="nw",
        command=lambda e: Benchmark.copy(),
        row=310 - Offset,
        cul=820,
        font=biggyfont,
        active_fill="cyan",
        tags=["PC_info"],
        tag=["PC_info"],
        outline_tag="PC_info",
    )

    Canvas_Create.create_label(
        master=manager._window,
        canvas=canvas,
        text=Benchmark._info_text,
        description_name="Benchmarks",
        anchor="nw",
        command=lambda e: Benchmark.copy(),
        row=400 - Offset,
        cul=820,
        font=biggyfont,
        active_fill="cyan",
        tags=[Benchmark._info_tag]
    )

    LogoOffset = 100

    # Create Active Buttons.
    Canvas_Create.image_Button(
        canvas=canvas,
        row=162 + LogoOffset,
        cul=794,
        img_1=TextureMgr.Request("Master_Sword.png"),
        img_2=TextureMgr.Request("Master_Sword_active.png"),
        command=lambda event: manager.open_browser("Kofi"),
    )

    Canvas_Create.image_Button(
        canvas=canvas,
        row=162 + LogoOffset,
        cul=1007,
        img_1=TextureMgr.Request("Master_Sword2.png"),
        img_2=TextureMgr.Request("Master_Sword_active2.png"),
        command=lambda event: manager.open_browser("Github"),
    )

    Canvas_Create.image_Button(
        canvas=canvas,
        row=220 + LogoOffset,
        cul=978,
        anchor="c",
        img_1=TextureMgr.Request("Hylian_Shield.png"),
        img_2=TextureMgr.Request("Hylian_Shield_Active.png"),
        command=lambda event: manager.open_browser("Discord"),
    )

    # # Information text.
    # Canvas_Create.create_label(
    #     master=manager._window,
    #     canvas=canvas,
    #     text=manager.text_content,
    #     description_name="Info_Label",
    #     justify="center",
    #     anchor="n",
    #     row=35,
    #     cul=975,
    #     font=biggyfont,
    #     tags=["Info_Label"],
    #     tag=["Info_Label"],
    #     outline_tag="Info_Label",
    # )


def create_tab_buttons(manager, canvas):
    if not canvas == manager.maincanvas:
        # Kofi Button
        Canvas_Create.create_button(
            master=manager._window,
            canvas=canvas,
            text="Donate",
            style="success",
            row=1130,
            cul=520,
            width=60,
            padding=10,
            pos="center",
            tags=["Button"],
            description_name="Kofi",
            command=lambda: manager.open_browser("Kofi"),
        )

        # Github Button
        Canvas_Create.create_button(
            master=manager._window,
            canvas=canvas,
            text="Github",
            style="success",
            row=1066,
            cul=520,
            width=60,
            padding=10,
            pos="center",
            tags=["Button"],
            description_name="Github",
            command=lambda: manager.open_browser("Github"),
        )

    # Make the button active for current canvas.
    button1style = "default"
    button2style = "default"
    button3style = "default"
    active_button_style = "secondary"
    try:
        if canvas == manager.maincanvas:
            button1style = active_button_style
        if canvas == manager.cheatcanvas:
            button2style = active_button_style
    except AttributeError as e:
        e = "n"

    # 1 - Main
    Canvas_Create.image_Button(
        canvas=canvas,
        row=15,
        cul=65,
        name="Main",
        anchor="c",
        img_1=TextureMgr.Request("main.png"),
        img_2=TextureMgr.Request("main_a.png"),
        command=lambda e: manager.show_main_canvas(),
        Type=ButtonToggle.Static,
    )

    # 1 - Cheats
    Canvas_Create.image_Button(
        canvas=canvas,
        row=15,
        cul=65 + 80,
        name="CheatButton",
        anchor="c",
        tags=["CheatButton"],
        img_1=TextureMgr.Request("cheats.png"),
        img_2=TextureMgr.Request("cheats_a.png"),
        command=lambda e: manager.show_cheat_canvas(),
        Type=ButtonToggle.Static,
    )

    # 3 - Settings
    # Canvas_Create.create_button(
    #     master=manager._window,
    #     canvas=canvas,
    #     text="Settings",
    #     style=button3style,
    #     row=11,
    #     cul=257,
    #     width=8,
    #     tags=["Button"],
    #     description_name="Settings",
    #     command=lambda: manager.setting.settingswindow(
    #         manager.constyle, manager.all_canvas
    #     ),
    # )
