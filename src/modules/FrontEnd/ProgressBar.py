from modules.FrontEnd.CustomDialogue import CustomDialog
from modules.logger import *
from modules.FrontEnd.CanvasMgr import Canvas_Create
import ttkbootstrap as ttk
import threading


class ProgressBar:

    string: str = None
    progress_bar: ttk.Progressbar = None
    progress_window: ttk.Window = None

    @classmethod
    # fmt: off
    def Run(cls, window, tasks):
        cls.progress_window = ttk.Toplevel(window)
        cls.progress_window.title("Downloading")
        window_width = 300
        window_height = 100
        screen_width = cls.progress_window.winfo_screenwidth()
        screen_height = cls.progress_window.winfo_screenheight()
        x_coordinate = (screen_width - window_width) // 2
        y_coordinate = (screen_height - window_height) // 2
        cls.progress_window.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
        cls.progress_window.resizable(False, False)
        total_iterations = 100
        cls.string = ttk.StringVar()
        cls.string.set("Applying the changes.")
        log.info("ProgressBar Start.")
        label = ttk.Label(cls.progress_window, textvariable=cls.string)
        label.pack(pady=10)
        cls.progress_bar = ttk.Progressbar(cls.progress_window, mode="determinate", maximum=total_iterations)
        cls.progress_bar.pack(pady=20)
        def _safe_tasks():
            try:
                tasks()
            except Exception as e:
                log.error(f"Task thread crashed: {e!r}")
                cls.progress_window.after(0, cls.Destroy)

        task_thread = threading.Thread(target=_safe_tasks)
        task_thread.start()

    @classmethod
    def Destroy(cls):
        cls.progress_window.destroy()

    @classmethod
    def End(cls, manager):
        log.warning("ProgressBar Ended.")

        cls.Destroy()

        m = 1.3
        # Kofi button.
        element_1 = Canvas_Create.Photo_Image(
            image_path="support.png",
            width=int(70 * m),
            height=int(48 * m),
        )

        element_2 = Canvas_Create.Photo_Image(
            image_path="support_active.png",
            width=int(70 * m),
            height=int(48 * m),
        )

        element_3 = Canvas_Create.Photo_Image(
            image_path="no_thanks.png",
            width=int(70 * m),
            height=int(48 * m),
        )

        element_4 = Canvas_Create.Photo_Image(
            image_path="no_thanks_active.png",
            width=int(70 * m),
            height=int(48 * m),
        )

        if not manager.os_platform == "Linux":
            dialog = CustomDialog(
                manager,
                "TOTK Optimizer Tasks Completed",
                "",
                yes_img_1=element_1,
                yes_img_2=element_2,
                no_img_1=element_3,
                no_img_2=element_4,
                custom_no="No Thanks",
                width=384,
                height=216,
            )

            dialog.wait_window()
            if dialog.result:
                manager.open_browser("kofi")
