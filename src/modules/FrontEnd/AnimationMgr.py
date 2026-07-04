from modules.logger import log
from collections import deque

_INTERVAL_MS = 400


class AnimationQueue:
    isInit: bool = False
    queue = deque()
    _master = None

    @classmethod
    def Initialize(cls, master):
        log.warning("Initialize AnimationQueue")
        if cls.isInit:
            raise ("Already Initialized.")
        cls._master = master
        cls._schedule()
        cls.isInit = True

    @classmethod
    def AddToQueue(cls, func):
        cls.queue.append(func)

    @classmethod
    def _schedule(cls):
        cls._master.after(_INTERVAL_MS, cls._tick)

    @classmethod
    def _tick(cls):
        if not cls.queue:
            cls._schedule()
            return

        for func in cls.queue:
            func()
        
        cls._schedule()
