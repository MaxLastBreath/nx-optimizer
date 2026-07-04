from modules.FrontEnd.WidgetStates import *
import ttkbootstrap as ttk
from typing import Callable
from modules.logger import *
from PIL import Image, ImageTk


class ImageButton:

    __IsHovering: bool = False
    __AniIndex: int = 1

    _Window: ttk.Window
    _Canvas: ttk.Canvas
    _Images: list[ImageTk.PhotoImage]
    Name: str
    IsOn: ttk.BooleanVar
    tagOn: str
    tagOff: str
    Type: ButtonToggle
    FullTags = []

    def __init__(
        self,
        window: ttk.Window,
        canvas: ttk.Canvas,
        name: str,
        Tag: str,
        imagelist: list[ttk.PhotoImage],
        Type: ButtonToggle = ButtonToggle.Static,
        isOn: bool = False,
        tags=[],
    ):
        self._Window = window
        self._Canvas = canvas
        self.Name = name
        self.Tag = Tag
        self.Type = Type
        self.IsOn = ttk.BooleanVar(window, False)
        self.FullTags = tags
        self.IsOn.set(isOn)
        self._Images = imagelist
        # log.info(f"{self.Name}, {self.IsOn.get()} and default : {isOn}")

    def get(self):
        return self.IsOn.get()

    def set(self, isActive: bool):
        self.IsOn.set(isActive)

        if self.Type == ButtonToggle.Dynamic:
            if self.IsOn.get() is True:
                self._Canvas.itemconfig(self.Tag, image=self._Images[1])
            else:
                self._Canvas.itemconfig(self.Tag, image=self._Images[0])

    def toggle(self):
        if self.IsOn.get() is True:
            self.IsOn.set(False)
        else:
            self.IsOn.set(True)

        if self.Type == ButtonToggle.Dynamic:
            if self.IsOn.get() is True:
                self._Canvas.itemconfig(self.Tag, image=self._Images[1])
            else:
                self._Canvas.itemconfig(self.Tag, image=self._Images[0])

    def MakeDynamic(self, bool: ButtonToggle):
        self.Type = bool

    def ToggleCommand(self, OnClick: Callable, event: None):
        if self.Type == ButtonToggle.StaticDynamic:
            self.toggle()

        if self.Type == ButtonToggle.Dynamic:
            self.toggle()

        if callable(OnClick):
            OnClick(event)

    def BindCommand(self, OnClick: Callable):
        self._Canvas.tag_bind(
            self.Tag, "<Button-1>", lambda args: self.ToggleCommand(OnClick, args)
        )

        self._Canvas.tag_bind(
            self.Tag, "<Enter>", lambda e: self.ActivateImage(WidgetState.Enter)  # fmt:skip
        )

        self._Canvas.tag_bind(
            self.Tag, "<Leave>", lambda e: self.ActivateImage(WidgetState.Leave)  # fmt:skip
        )

    def SetImageState(self, isOn: bool = False):
        if isOn:
            self._Canvas.itemconfig(self.Tag, state=self._Images[1])

    def BindImages(
        self,
        cul: int,
        row: int,
        anchor: str = "nw",
    ):
        tags = self.FullTags.copy()
        tags.append(self.Tag)

        self._Canvas.create_image(
            cul,
            row,
            anchor=anchor,
            image=self._Images[0],
            state="normal",
            tags=tags,
        )

    def ToggleImg(
        self,
        State: WidgetState,
    ):

        if self.Type == ButtonToggle.Dynamic:
            return

        if State == WidgetState.Enter:
            self.__IsHovering = True
            self._Canvas.itemconfig(self.Tag, image=self._Images[1])

        if State == WidgetState.Leave:
            self.__IsHovering = False
            self._Canvas.itemconfig(self.Tag, image=self._Images[0])

    def ActivateImage(self, State: WidgetState):
        # log.info(f"{self.IsOn.get()}")
        if self.Type == ButtonToggle.StaticDynamic:
            if self.get() is False:
                self.ToggleImg(State)
        else:
            self.ToggleImg(State)

    def AddAnimationToQueue(self):
        from modules.FrontEnd.AnimationMgr import AnimationQueue

        AnimationQueue.AddToQueue(self.Animation)

    def Animation(self):
        try:
            if not self.__IsHovering:
                return
        
            if not self._Images:
                return

            if hasattr(self, "_last_drawn_index"):
                if self.__AniIndex == self._last_drawn_index:
                    return

            next_index = self.__AniIndex +1
            if next_index > len(self._Images):
                next_index = 0

            self._Canvas.itemconfig(
                self.Tag,
                image=self._Images(self.__AniIndex)
            )
                
            self._last_drawn_index = self.__AniIndex
            self.__AniIndex = next_index
        
        except Exception:
            pass
