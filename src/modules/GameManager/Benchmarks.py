from modules.GameManager.FileManager import *
from modules.logger import *
from modules.GameManager.PatchInfo import PatchInfo
import pyperclip
import os
import re

class Benchmark:
    _manager = None
    _canvas: ttk.Canvas = None
    _filemgr = None
    _patchInfo: PatchInfo = None

    _selected_benchmark = None
    _benchmarks: dict = {}

    __version = None
    __support = None
    __path = None

    __label_none: str = "No Benchmark Detected"
    __label_nosupport: str = "Benchmarks Not Supported"

    _info_tag: str = "benchmark-info"
    _label_tag: str = "benchmark-label"

    _info_text :str = (f"Turn on Direct Keyboard.\n"
                        f"Press G after loading in game.\n"
                        f"Select your Benchmark in Advanced Settings.\n"
                        f"Clicking this text copies your results.\n")
    
    _info_text_none :str = (f"This game doesn't support\n"
                            f"UltraCam Benchmark Features\n")
    
    @classmethod
    def __str__(cls):
        return cls._selected_benchmark

    @classmethod
    def Initialize(cls, manager, filemanager):
        from modules.FrontEnd.FrontEnd import Manager, FileManager
        cls._manager: Manager = manager
        cls._canvas = cls._manager.maincanvas
        cls._filemgr: FileManager = filemanager
        cls._patchInfo: PatchInfo = manager._patchInfo
        cls.ReloadBenchmarkInfo()
        cls.__showButtons()

    @classmethod
    def __showButtons(cls):
        if (cls.__support is False):
            cls._canvas.itemconfig("benchmark-button", state="hidden")
            return
        
        if (len(cls._benchmarks) == 0):
            cls._canvas.itemconfig("benchmark-button", state="hidden")
            cls._canvas.itemconfig("benchmark-reload", state="normal")
            return
        else:
            cls._canvas.itemconfig("benchmark-button", state="normal")


    @classmethod
    def __benchmarkInfo(cls, BenchmarkName = None):
        
        if cls.__support is False:
            BenchmarkName = cls.__label_nosupport
            cls._canvas.itemconfig(cls._label_tag, text=cls.__label_nosupport)
            return cls._info_text_none

        # set to None
        if BenchmarkName is None:
            BenchmarkName = cls.__label_none
            cls._canvas.itemconfig(cls._label_tag, text=cls.__label_none)
            return cls._info_text
        
        benchmark_list = list(cls._benchmarks)

        cls._canvas.itemconfig(cls._label_tag, text=f"{BenchmarkName} Benchmark {benchmark_list.index(BenchmarkName) + 1}/{len(cls._benchmarks)}")

        text = (f"Frames - {cls._benchmarks[BenchmarkName]['Frames']} Frames\n"
                f"Average - {cls._benchmarks[BenchmarkName]['Average']} FPS\n"
                f"1% Lowest FPS - {cls._benchmarks[BenchmarkName]['Low']} FPS\n"
                f"0.1% Lowest FPS - {cls._benchmarks[BenchmarkName]['Lowest']} FPS\n")

        return text
    
    @classmethod
    def cycle(cls):
        benchmark_list = list(cls._benchmarks)

        if (len(benchmark_list) == 0 or cls._selected_benchmark is None):
            return

        indexOfname = benchmark_list.index(cls._selected_benchmark)
        indexOfname+=1

        if (indexOfname > len(benchmark_list) - 1):
            indexOfname = 0
        
        if (indexOfname < 0):
            indexOfname = len(benchmark_list) - 1
        
        cls._selected_benchmark = benchmark_list[indexOfname]
        cls.load_benchmark(cls._selected_benchmark)
        cls.__showButtons()
        
    @classmethod
    def ReloadBenchmarkInfo(cls):
        cls._benchmarks = {}
        cls._selected_benchmark = None
        cls._patchInfo = cls._manager._patchInfo
        cls.__version = cls._patchInfo.Benchmark_Version
        cls.__support = cls._patchInfo.Support_Benchmark
        cls.__path = os.path.join(FileManager.sdmc, cls._patchInfo.Benchmarks_File)
        cls.__load_benchmark()
        cls.__showButtons()

    @classmethod
    def load_benchmark(cls, BenchmarkName):
        cls._selected_benchmark = BenchmarkName

        cls._canvas.itemconfig(
            cls._info_tag,
            text=cls.__benchmarkInfo(BenchmarkName)
        )

    @classmethod
    def __read_benchmark_file_v1(cls):
        "Benchmark UltraCam Version 0 read and load structures."
        "Expects a passed .txt file."

        Last_Found = None
        with open(cls.__path, "r") as benchmarks:
            for line in benchmarks:
                match = re.search(r"BENCHMARK FOR ([\w']+(?:\s+[\w']+)*) COMPLETED", line)

                if not match:
                    continue

                BenchmarkName = match.group(1)
                    
                next_line = next(benchmarks).strip()
                pattern = r"(\d+(\.\d+)?)"
                frames = re.findall(pattern, next_line)
                numbers = [
                    float(num[0]) if "." in num[0] else int(num[0])
                    for num in frames
                ]
                if numbers[2] == 1:
                    numbers.pop(2)
                if numbers[3] == 0.1:
                    numbers.pop(3)
                cls._benchmarks[BenchmarkName] = {
                    "Frames": numbers[0],
                    "Average": numbers[1],
                    "Low": numbers[2],
                    "Lowest": numbers[3],
                }
                Last_Found = BenchmarkName
        
        cls._selected_benchmark = Last_Found

    @classmethod 
    def __LoadJsonFile(cls, location):
        log.info(f"Reading File : {location}")
        with open(location, "r", encoding="utf-8") as file:
            return  json.load(file)

    @classmethod
    def Json(cls, JsonFile, Entry, fallback=None):
        try:
            ReturnValue = JsonFile[Entry]
        except KeyError:
            log.error(f"Couldn't fetch Json Entry : {Entry}")
            return fallback
        return ReturnValue

    @classmethod
    def __read_benchmark_file_v2(cls):
        Name = None

        for file in os.listdir(cls.__path):
            Path = os.path.join(cls.__path, file)

            JsonFile = cls.__LoadJsonFile(Path)
            Name = file.replace(".json", "")

            if not Name:
                continue

            cls._benchmarks[Name] = {}

            cls._benchmarks[Name]["Frames"] = cls.Json(JsonFile, "Total", 0.0)
            cls._benchmarks[Name]["Lowest"] = cls.Json(JsonFile, "Lowest", 0.0)
            cls._benchmarks[Name]["Low"] = cls.Json(JsonFile, "Low", 0.0)
            cls._benchmarks[Name]["Average"] = cls.Json(JsonFile, "Average", 0.0)
            cls._benchmarks[Name]["Max"] = cls.Json(JsonFile, "Max", 0.0)
            cls._benchmarks[Name]["Time"] = cls.Json(JsonFile, "Time", 0.0)
            cls._benchmarks[Name]["Type"] = cls.Json(JsonFile, "Type", 0.0)

        cls._selected_benchmark = Name
    
    @classmethod
    def __load_benchmark(cls):
        log.info("Loading Benchmark Reader")

        # return early
        if (not os.path.exists(cls.__path)):
            cls.load_benchmark(None)
            log.warning(f"Benchmark File Not Found. {cls.__path}")
            return
        
        if (cls.__version == 0):
            cls.__read_benchmark_file_v1()
        else :
            cls.__read_benchmark_file_v2()
        
        cls.load_benchmark(cls._selected_benchmark)

    @classmethod
    def copy(cls):
        if cls._selected_benchmark is None:
            return
        
        UserChoices = cls._manager.UserChoices

        system_os = "MacOS" if platform.system() == "Darwin" else platform.system()

        # Initial Text.    
        Systeminfo = ""
        Settings = "## Settings Info:\n"   
        Result = f"## Results:\n"
        benchmark_result = (
            f"## *{cls._selected_benchmark} Benchmark*\n" 
            f"- **Game :** {cls._manager._patchInfo.Name} [{cls._manager._patchInfo.ID}] {cls._manager._patchInfo.ModName.replace('!', '')} {cls._manager._patchInfo.ModVersion}\n"
            f"- **OS :** {system_os}\n"
        )

        if platform.system() != "Darwin":
            Systeminfo = f"- GPU: **{gpu_name}**\n"
        
        Systeminfo += (
            f"- CPU : **{CPU}**\n"
            f"- RAM : **{total_memory}** GB RAM at **{FREQUENCY}** MHz\n"
        )

        if ("resolution" in UserChoices):
            resolution = UserChoices["resolution"].get()
            Settings += f"- Resolution : **{resolution}**\n"

        if ("shadow resolution" in UserChoices):
            shadows = int(UserChoices["shadow resolution"].get().split("x")[0])
            Settings += f"- Shadow Resolution: **{shadows}**\n"

        if ("fps" in UserChoices):
            fps = cls._manager.UserChoices['fps'].get()
            Settings+= f"- FPS CAP: **{fps}**\n"

        Result += (
            f"- Frames **{cls._benchmarks[cls._selected_benchmark]['Frames']}**\n"
            f"- Average **{cls._benchmarks[cls._selected_benchmark]['Average']}**\n"
            f"- 1% Lows **{cls._benchmarks[cls._selected_benchmark]['Low']}** FPS\n"
            f"- 0.1% Lows **{cls._benchmarks[cls._selected_benchmark]['Lowest']}** FPS\n"
        )

        if (cls.__version > 1):
            Result += f"- 1% Max **{cls._benchmarks[cls._selected_benchmark]['Max']}** FPS\n"
            TimeSpan = cls._benchmarks[cls._selected_benchmark]['Time']
            Result += f"- Duration : **{(int)(TimeSpan / 3600)}h:{(int)(TimeSpan / 60)}m:{(int)(TimeSpan % 60)}s:{(int)(TimeSpan * 100 - (int)(TimeSpan) * 100)}ms**\n"
            Result += f"- Benchmark Type: **{cls._benchmarks[cls._selected_benchmark]['Type']}**\n"

        # Combine Texts
        benchmark_result += Systeminfo
        benchmark_result += Settings
        benchmark_result += Result

        if (cls.__version > 1):
            benchmark_result += "\n\n**UltraCam Version 3.0+ Benchmark, Result Might Be Lower**"

        log.info("Copied Benchmark Result")
            
        pyperclip.copy(benchmark_result)
        