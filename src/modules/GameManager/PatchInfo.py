from modules.logger import log, superlog
import json, math, os


class PatchInfo:
    Folder: str = "PatchInfo/Tears Of The Kingdom"
    Name: str = "Tears of The Kingdom"
    ID: str = "0100F2C0115B6000"
    ModName: str = "!!!TOTK Optimizer"
    ModVersion: str = "1.0"
    ConfigPath: str = "UltraCam/maxlastbreath.ini"
    ModFolder: str = ""
    Versions: list[str] = []
    Cheats: bool = False
    ResolutionScale: bool = True
    isSDconfig: bool = False

    Support_Benchmark: bool = False
    Benchmark_Version: int = 0
    Benchmarks_File: str = "TOTKBenchmark.txt" # This is a file Path... Always load from SDcard. so sd:/FilePath

    def __init__(self, folder: str, JsonFile: json):  # fmt: skip
        self.Folder = folder
        self.ID = self.Json(JsonFile, "ID") # mandatory
        self.SelectionID = JsonFile.get("SelectionID", self.ID)
        self.SelectionAliases = JsonFile.get("SelectionAliases", [])
        self.Name = self.Json(JsonFile, "Name") # mandatory
        self.Versions = self.Json(JsonFile, "Versions", [])
        self.ModName = self.Json(JsonFile, "ModName", "!!!NX-Optimizer")
        self.ConfigPath = self.Json(JsonFile, "ModConfig")
        self.ModFolder = self.Json(JsonFile, "ModFolder")
        self.Cheats = self.Json(JsonFile, "Cheats", False)
        self.isSDconfig = self.Json(JsonFile, "SD", False)
        self.ResolutionScale = self.Json(JsonFile, "EmulationScale", True)
        self.ModVersion = self.Json(JsonFile, "Mod_Version", "1.0")
        self.OptionsFile = JsonFile.get("Config", "Options.json")
        self.PresetsFile = JsonFile.get("Presets", "Presets.json")
        self.ExefsPatch = JsonFile.get("ExefsPatch")
        self.NativePayload = JsonFile.get("NativePayload")
        self.ConflictingMods = JsonFile.get("ConflictingMods", [])

        self.Support_Benchmark = self.Json(JsonFile, "benchmarks", False)
        self.Benchmark_Version = self.Json(JsonFile, "benchmarks_version", 0)
        self.Benchmarks_File = self.Json(JsonFile, "benchmarks_file", self.Benchmarks_File)

    def Json(self, JsonFile, Entry, fallback=None):
        try:
            ReturnValue = JsonFile[Entry]
        except KeyError:
            log.error(f"Couldn't fetch {Entry} for {self.Json(JsonFile, 'Name', fallback='ERROR')}")
            return fallback
        return ReturnValue
        
    def GetModPath(self) -> str:
        location = os.path.join(self.Folder, self.ModFolder)
        return location

    def IDtoNum(self):
        return int(self.ID, 16)

    def LoadJson(self):
        Location = os.path.join(self.Folder, self.OptionsFile)
        with open(Location, "r", encoding="utf-8") as file:
            return json.load(file)

    def LoadPresetsJson(self):
        Location = os.path.join(self.Folder, self.PresetsFile)

        if not os.path.exists(Location):
            return {"Saved": {}}

        with open(Location, "r", encoding="utf-8") as file:
            return {"Saved": {}} | json.load(file)

    def MigrateUserConfig(self, config, options):
        """Map retired numeric settings to the closest preset, in memory only."""
        section = self.SelectionID
        if not config.has_section(section):
            return
        for group in options.values():
            for name, option in group.items():
                legacy = option.get("LegacyNumericOption")
                if not legacy or config.has_option(section, name) or not config.has_option(section, legacy):
                    continue
                try:
                    value = config.getfloat(section, legacy)
                    if not math.isfinite(value):
                        raise ValueError("Non-finite legacy setting")
                    values = option["Values"]
                    index = min(range(len(values)), key=lambda i: abs(values[i] - value))
                except ValueError:
                    index = option["Default"]
                config.set(section, name, str(index))
                log.info(f"Migrated {legacy} to {name}: {option['Name_Values'][index]}")

    def LoadCheatsJson(self):
        if self.Cheats is False:
            log.warning("No Cheats detected")
            return
        if self.Cheats is True:
            Location = os.path.join(self.Folder, "Cheats.json")
            with open(Location, "r", encoding="utf-8") as file:
                return json.load(file)
