from enum import Enum
from modules.logger import *
from configuration.settings import config
import platform
import ttkbootstrap as ttk


class NxType(Enum):
    LEGACY = "Legacy"
    RYUJINX = "Ryujinx"

class NxMode:
    __mode: NxType = NxType.LEGACY
    _modes_list = list(NxType)

    @classmethod
    def __str__(cls):
        return cls.get()
    
    @classmethod
    def set(cls, value):
        Tag = NxType(value)
        if not isinstance(Tag, NxType):
            raise ValueError("Mode must be an instance of NxType")  
        cls.__AUTOCHANGE(cls.__mode.value, Tag.value)

    @classmethod
    def get(cls):
        return cls.__mode.value

    @classmethod
    def switch(cls): 
        current_index = cls._modes_list.index(cls.__mode)
        next_index = (current_index + 1) % len(cls._modes_list)
        cls.set(cls._modes_list[next_index])

    @classmethod
    def isRyujinx(cls) -> bool:
        return cls.__mode == NxType.RYUJINX

    @classmethod
    def isLegacy(cls) -> bool:
        return cls.__mode == NxType.LEGACY

    @classmethod
    def __AUTOCHANGE(cls, old_value, new_value):
        """Logic to execute when Mode changes"""

        cls.__mode = NxType(new_value)

        for canvas in cls.__Canvases:
            for tag in cls._modes_list:
                canvas.itemconfigure(tag.value, state="hidden")
            canvas.itemconfigure(cls.get(), state="normal")

        log.info(f"NX-Mode Changed to {new_value} from {old_value}")
        cls._filemgr.checkpath()

    @classmethod
    def Initialize(cls, Canvases: list, filemgr):
        from modules.GameManager.FileManager import FileManager
        cls.__Canvases = Canvases
        cls._filemgr: FileManager = filemgr

        if platform.system() == "Darwin":
            cls.set(NxType.RYUJINX)
            return
        
        cls.set(NxType(config.get("Mode", "managermode", fallback="Legacy")))