import ttkbootstrap as ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from modules.logger import *
from modules.FrontEnd.FrontEnd import Manager
from modules.update import textver, check_for_updates, delete_old_exe
from modules.scaling import sf, scale
from ctypes import *

OptimizerWindowSize = (1200, 600) # everything is scaled with 1200x600 in mind. 2:1 aspect ratio

if __name__ == "__main__":
    try:
        if platform.system() == "Windows":
            windll.shcore.SetProcessDpiAwareness(2)
            windll.user32.SetProcessDPIAware()

        window = TkinterDnD.Tk()
        window.tk.call("tk", "scaling", sf)
        window.title(f"NX Optimizer {textver}")
        window_width = scaleWindow(OptimizerWindowSize[0])
        window_height = scaleWindow(OptimizerWindowSize[1])
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        window.minsize(window_width, window_height)
        window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        window.resizable(False, False)

        main = Manager(window)

        ttk.Style().configure(
            "TButton", foreground="white", font=("Comic Sans MS", 10, "bold")
        )

        # Delete any old executables
        # Disabled for MacOS (For now)
        if platform.system() != "Darwin":
            delete_old_exe()
            check_for_updates()

        window.mainloop()
    except Exception as e:
        log.critical(f"ERROR AT MAIN: {e}", exc_info=True)
