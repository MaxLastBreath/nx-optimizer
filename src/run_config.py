import sys, os

__ROOT__ = os.path.dirname(__file__)
__LOCAL__ = __ROOT__

if getattr(sys, "frozen", False):
    __ROOT__ = sys._MEIPASS
    __LOCAL__ = os.path.dirname(os.environ.get("APPIMAGE", sys.executable))
