from modules.GameManager.PatchInfo import PatchInfo
from modules.logger import log, superlog
from run_config import __ROOT__
import json, os


class Game_Manager:
    GamePatches: list[PatchInfo] = []
    _DefaultID: str = "0100F2C0115B6000"
    _Directory: str = "PatchInfo"
    _PatchFile: str = "PatchInfo.json"

    def __init__(self):
        self.LoadPatches()

    @classmethod
    def LoadPatches(cls) -> None:
        current_directory = os.path.curdir
        patch_directory_root = os.path.join(__ROOT__, cls._Directory)
        patch_directory = os.path.join(current_directory, cls._Directory)

        if os.path.exists(patch_directory):
            cls.CreatePatches(patch_directory)

        superlog.info("Looking for supported games...")
        cls.CreatePatches(patch_directory_root)

    @classmethod
    def CreatePatchInfo(cls, patchfolder) -> PatchInfo:
        
        "Load Patch Info for game."
        
        _PatchInfo = None

        for filename in os.listdir(patchfolder):
            filepath = os.path.join(patchfolder, filename)

            if filename == cls._PatchFile:
                with open(filepath, "r", encoding="utf-8") as file:
                    jsonfile = json.load(file)

                # Variants share a title ID and artwork, but have distinct options
                # and saved selections (e.g. UltraCam 1.6 vs native FPS 1.9).
                definitions = [jsonfile] + [jsonfile | variant for variant in jsonfile.get("Variants", [])]
                for definition in definitions:
                    item = next((p for p in cls.GamePatches if p.Name == definition['Name']), None)
                    if item is None:
                        log.info(f"{definition['Name']} [{definition['ID']}] : {definition['Versions']}")
                        item = PatchInfo(patchfolder, definition)
                        cls.GamePatches.append(item)
                    if _PatchInfo is None:
                        _PatchInfo = item
                return _PatchInfo

    @classmethod
    def CreatePatches(cls, patch_directory) -> None:
        "Loads patch info for each game detected in Patch Folder"

        for folder in os.listdir(patch_directory):
            patchfolder = os.path.join(patch_directory, folder)
            cls.CreatePatchInfo(patchfolder)

    @classmethod
    def GetJsonByID(cls, ID: str) -> PatchInfo:
        """Find a saved selection, accepting legacy title IDs for base profiles."""

        for item in cls.GamePatches:
            if ID.lower() == item.SelectionID.lower():
                return item

        # Retired selections resolve to the current profile, without importing
        # their old option encoding (e.g. FPS dropdown index 0 is not 0 FPS).
        for item in cls.GamePatches:
            if any(ID.lower() == alias.lower() for alias in item.SelectionAliases):
                return item

        # if we don't find anything return TOTK patch.
        for item in cls.GamePatches:
            if item.ID.lower() == cls._DefaultID.lower():
                return item

    @classmethod
    def GetPatches(cls) -> list[PatchInfo]:
        if not cls.GamePatches:
            cls.LoadPatches()
        return cls.GamePatches
