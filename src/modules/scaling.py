from modules.macos import macos_path
from screeninfo import *
import platform
import configparser
import os

CONFIG_FILE_LOCAL_OPTIMIZER = "TOTKOptimizer.ini"

if platform.system() == "Darwin":
    localconfig = os.path.join(macos_path, CONFIG_FILE_LOCAL_OPTIMIZER)

config = configparser.ConfigParser()
config.read(CONFIG_FILE_LOCAL_OPTIMIZER, encoding="utf-8")
w_scale = config.get("Settings", "scale", fallback="On")


def Auto_SF():
    if w_scale == "Off":
        return 1.0
    sf = 1.0
    if w_scale == "1.0x":
        sf = 1.0
    if w_scale == "1.5x":
        sf = 1.5
    if w_scale == "2.0x":
        sf = 2.0
    if w_scale == "2.5x":
        sf = 2.5
    if w_scale == "3.0x":
        sf = 3.0
    if w_scale == "On":
        h = 1080
        try:
            monitors = get_monitors()
            for monitor in monitors:
                if monitor.is_primary:
                    h = monitor.height
        except Exception as e:
            print(e)
            return 1.0
        if h <= 1080 and h < 1440:
            sf = 1.0
        if h >= 1440:
            sf = 1.5
        if h >= 2160:
            sf = 2.0
        if h >= 3456:
            sf = 3.0
    return sf


# Use First Monitor to determine SF, this bypasses scaling from windows.
sf = Auto_SF()

def scale(scale):
    from run import OptimizerWindowSize

    WindowSize: float  = (OptimizerWindowSize[0] + OptimizerWindowSize[1]) / (1200 + 600) - 1
    return int(float(scale * sf) * (1.0 + (WindowSize)))

def scaleWindow(scale):
    return int(float(scale * sf))
