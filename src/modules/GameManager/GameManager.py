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

                # check if a game already exists inside of our loop
                for item in cls.GamePatches:
                    if item.Name == jsonfile['Name']:
                        return item

                log.info(
                    f"{jsonfile['Name']} [{jsonfile['ID']}] : {jsonfile['Versions']}"
                )

                _PatchInfo: PatchInfo = PatchInfo(patchfolder, jsonfile)

                cls.GamePatches.append(
                    _PatchInfo
                )
                return _PatchInfo

    @classmethod
    def CreatePatches(cls, patch_directory) -> None:
        "Loads patch info for each game detected in Patch Folder"

        for folder in os.listdir(patch_directory):
            patchfolder = os.path.join(patch_directory, folder)
            if not os.path.isdir(patchfolder):
                continue
            cls.CreatePatchInfo(patchfolder)

    @classmethod
    def GetJsonByID(cls, ID: str) -> PatchInfo:
        """Finds the current json file for a TITLEID."""

        for item in cls.GamePatches:
            if ID.lower() == item.ID.lower():
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
