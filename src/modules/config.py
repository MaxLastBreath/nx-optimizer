import shutil
from configuration.settings import *
import os, json, re

from modules.FrontEnd.FrontEndMode import NxMode

# fmt: off
def dropdown_name(patch_dict, index):
    return patch_dict["Name_Values"][int(index)]

def apply_choice(Manager, patch_dict, option_key, value):
    "Resolve a dropdown/scale/bool value and set it on UserChoices."

    patch_class = patch_dict["Class"]
    key = option_key if option_key in Manager.UserChoices else option_key.lower()

    if patch_class == "dropdown":
        Manager.UserChoices[key].set(dropdown_name(patch_dict, value))
    elif patch_class == "scale":
        Manager.maincanvas.itemconfig(patch_dict["Name"], text=value)
        Manager.UserChoices[key].set(value)
    else:
        if patch_class == "bool":
            if value is True: value = "On"
            if value is False: value = "Off"
        Manager.UserChoices[key].set(value)

def apply_preset(Manager, preset_options: dict):

    "Apply Presets for different games"

    from modules.FrontEnd.FrontEnd import Manager as mgr

    Manager: mgr = Manager

    # Manager.fetch_var(Manager.ui_var, preset_options, "UI")
    # Manager.fetch_var(Manager.fp_var, preset_options, "First Person")
    # Manager.fetch_var(Manager.selected_settings, preset_options, "Settings") # set Legacy settings.

    for i, (key, value) in enumerate(Manager.UltracamPatchJson.items()):        
        patch_info = value

        if "emuscale" in preset_options:
            Manager._EmulatorScale.set(preset_options["emuscale"])

        for option_key, option_value in preset_options.items():
            if option_key in Manager.selected_options:
                Manager.selected_options[option_key].set(option_value)
            else:
                continue

        selected_preset = Manager.selected_preset.get()

        if selected_preset.lower() == "default":
            for option_key in Manager.UserChoices:
                try:
                    patch_dict = patch_info[option_key.lower()]
                except KeyError:
                    continue
                apply_choice(Manager, patch_dict, option_key, patch_dict["Default"])

        for option_key, option_value in preset_options.items():
            if option_key.lower() in Manager.UserChoices:
                patch_dict = patch_info[option_key.lower()]
                apply_choice(Manager, patch_dict, option_key, option_value)
            else:
                continue

GAME_KEYS = ["emuscale", "configpath"]

def clear_game_values(Manager, config):
    "Option values live in the mod's own config now, drop any stale copies kept by older versions."

    GameID = Manager._patchInfo.ID

    if not config.has_section(GameID):
        config.add_section(GameID)
        return

    if not config.get(GameID, "configpath", fallback=None):
        return

    for option in config.options(GameID):
        if option in GAME_KEYS:
            continue
        config.remove_option(GameID, option)

def save_config_path(Manager, config_file, config_path):
    "Records where the mod config was last written so it can be read back on the next launch."

    config = configparser.ConfigParser()
    config.read(config_file, encoding="utf-8")

    GameID = Manager._patchInfo.ID
    if not config.has_section(GameID):
        config.add_section(GameID)

    config.set(GameID, "configpath", config_path)

    with open(config_file, "w", encoding="utf-8") as file:
        config.write(file)

def mod_config_file(config_path, config_name):
    "Path of a single mod config, mirroring how the patcher lays them out."

    if config_name == "Keys":
        return config_path ## compatibility for old patches
    return os.path.join(config_path, config_name + ".ini")

def read_mod_config(config_path, config_name):
    "Reads one of the mod's own .ini files, None when it was never written."

    config_file = mod_config_file(config_path, config_name)
    if not os.path.exists(config_file):
        return None

    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    config.read(config_file, encoding="utf-8")
    return config

def vector_index(patch_dict, pair):
    "Matches a Width/Height pair read back from a mod config to its dropdown entry."

    target = [str(int(float(number))) for number in pair]

    for index, entry in enumerate(patch_dict["Values"]):
        if isinstance(entry, str):
            numbers = re.findall(r"\d+(?:\.\d+)?", entry)
        else:
            numbers = entry
        if [str(int(float(number))) for number in numbers[:2]] == target:
            return index
    return None

def load_mod_choice(Manager, config, patch_dict, option_key):
    "Restores a single UserChoice from the value the patcher wrote into the mod config."

    Config_Class = patch_dict["Config_Class"]
    section = Config_Class[0]

    if not config.has_section(section):
        return

    if len(Config_Class) == 3:
        pair = [config.get(section, key, fallback=None) for key in Config_Class[1:]]
        if None in pair:
            return
        index = vector_index(patch_dict, pair)
        if index is None:
            return
        apply_choice(Manager, patch_dict, option_key, index)
        return

    value = config.get(section, Config_Class[1], fallback=None)
    if value is None:
        return

    if patch_dict["Class"].lower() == "dropdown":
        values = [str(entry) for entry in patch_dict["Values"]]
        if value not in values:
            return
        apply_choice(Manager, patch_dict, option_key, values.index(value))
        return

    apply_choice(Manager, patch_dict, option_key, value)

def loadGameConfig(Manager, config):
    # Load UltraCam Beyond new patches from the mod configs the patcher last wrote.
    for key, value in Manager.UltracamPatchJson.items():
        for itemName in value:
            Manager.UserConfigs[itemName] = key

    GameID = Manager._patchInfo.ID
    Manager._EmulatorScale.set(config.get(GameID, "emuscale", fallback=1))

    config_path = config.get(GameID, "configpath", fallback=None)
    if not config_path:
        return

    for key, patch_info in Manager.UltracamPatchJson.items():
        modconfig = read_mod_config(config_path, key)
        if modconfig is None:
            continue

        for patch in Manager.UserChoices:
            patch_dict = patch_info.get(patch)
            if patch_dict is None:
                continue
            load_mod_choice(Manager, modconfig, patch_dict, patch)

def save_user_choices(Manager, config_file, Legacy_path=None):
    log.info(f"Saving user choices in {localconfig}")
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)

    # This is only required for the UI and FP mods.
    if not config.has_section("Options"):
        config["Options"] = {}
    # config['Options']['UI'] = Manager.ui_var.get()
    # config['Options']['First Person'] = Manager.fp_var.get()

    clear_game_values(Manager, config)

    # Save the enable/disable choices
    for option_name, option_var in Manager.selected_options.items():
        config['Options'][option_name] = option_var.get()

    # Save the Legacy.exe path if provided
    if not config.has_section("Paths"):
        config["Paths"] = {}
    if NxMode.isLegacy():
        if Legacy_path:
            config['Paths']['LegacyPath'] = Legacy_path
    if NxMode.isRyujinx():
        if Legacy_path:
            config['Paths']['RyujinxPath'] = Legacy_path

    # Save the manager selected mode I.E Ryujinx/Legacy
    config["Mode"] = {"ManagerMode": NxMode.get()}

    log.info("User choices saved in Memory,"
             "Attempting to write into file.")
    
    if (Manager._patchInfo.ResolutionScale):
        config.set(Manager._patchInfo.ID, "emuscale", Manager._EmulatorScale.get())
    
    # Write the updated configuration back to the file
    with open(config_file, 'w', encoding="utf-8") as file:
        config.write(file)
    log.info("Successfully written into log file")

def load_user_choices(Manager, config_file, mode=None):
    config = configparser.ConfigParser()
    config.read(config_file, encoding="utf-8")

    loadGameConfig(Manager, config)

    # Load the enable/disable choices
    for option_name, option_var in Manager.selected_options.items():
        option_value = config.get('Options', option_name, fallback="Off")
        option_var.set(option_value)
        log.info("Options")
    

def apply_selected_preset(manager, event=None):
    from modules.FrontEnd.FrontEnd import Manager
    manager: Manager = manager

    try:
        selected_preset = manager.selected_preset.get()
    except AttributeError as e:
        selected_preset = "Saved"
        log.error(f"Failed to apply selected preset: {e}")

    presets = manager._patchInfo.LoadPresetsJson()

    if selected_preset.lower() == "saved":
        load_user_choices(manager, manager.config)
    elif selected_preset in presets:
        preset_to_apply = presets[selected_preset]
        for key, value in preset_to_apply.items():
            if value is True:
                preset_to_apply[key] = "On"
            elif value is False:
                preset_to_apply[key] = "Off"
            elif not isinstance(value, int) and not isinstance(value, float) and value.lower() in ["enable", "enabled", "on"]:
                preset_to_apply[key] = "On"
            elif not isinstance(value, int) and not isinstance(value, float) and value.lower() in ["disable", "disabled", "off"]:
                preset_to_apply[key] = "Off"
        # Apply the selected preset from the online presets
        apply_preset(manager, presets[selected_preset])

def write_Legacy_config(Manager, config_file: str, title_id: str, section: str, setting: str, selection):
    write_Legacy_configs(Manager, config_file, title_id, {(section, setting): selection})

def write_Legacy_configs(Manager, config_file: str, title_id: str, settings: dict):
    os.makedirs(config_file, exist_ok=True)
    Custom_Config = os.path.join(config_file, f"{title_id}.ini")
    Legacyconfig = configparser.ConfigParser()
    Legacyconfig.read(Custom_Config, encoding="utf-8")
    for (section, setting), selection in settings.items():
        if not Legacyconfig.has_section(section):
            Legacyconfig[f"{section}"] = {}
        Legacyconfig[f"{section}"][f"{setting}\\use_global"] = "false"
        Legacyconfig[f"{section}"][f"{setting}\\default"] = "false"
        Legacyconfig[f"{section}"][f"{setting}"] = selection
    with open(Custom_Config, "w", encoding="utf-8") as file:
        Legacyconfig.write(file, space_around_delimiters=False)

def read_ryujinx_version(config_file: str)-> int:
    with open(config_file, "r", encoding="utf-8") as file:
        configData = json.load(file)
    version = int(configData["version"])
    log.info(f"Ryujinx Config {version}")
    return version

def write_ryubing_config(config_file: str, game_config: str, setting, selection):
    if not os.path.exists(game_config):
        game_config_dir = os.path.dirname(game_config)
        os.makedirs(game_config_dir, exist_ok=True)
        shutil.copy(config_file, game_config)
        log.warning(f"Creating a new Game Config {game_config}")
    
    with open(game_config, "r", encoding="utf-8") as file:
        data = json.load(file)
        data[setting] = selection

    os.remove(game_config)
    with open(game_config, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def write_ryujinx_config(filemgr, config_file, setting, selection):
    from modules.GameManager.FileManager import FileManager

    if not os.path.exists(config_file):
        log.error(f"RYUJINX GLOBAL CONFIG FILE DOESN'T EXIST! {config_file}")
        return
    
    if (read_ryujinx_version(config_file) >= 68):
        write_ryubing_config(config_file, FileManager._gameconfig, setting, selection)
        return
    
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        data[setting] = selection

    os.remove(config_file)
    with open(config_file, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def enable_ryujinx_mods(blacklist: list, whitelist: list):
    from modules.GameManager.FileManager import FileManager

    mod_config = os.path.join(os.path.dirname(FileManager._gameconfig), "mods.json")

    if (not os.path.exists(mod_config)):
        log.warning("No mod config for game.")
        return

    with open(mod_config, "r", encoding="utf-8") as file:
        data = json.load(file)

    for item in blacklist:
        for mod in data["mods"]:
            if mod["name"] == item:
                mod["enabled"] = False
                log.warning(f"Disabling Mod {item}")

    for item in whitelist:
        for mod in data["mods"]:
            if mod["name"] == item:
                mod["enabled"] = True
                log.warning(f"Enabling Mod {item}")

    os.remove(mod_config)
    with open(mod_config, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def load_config_game(Manager, config_file):
    ''' Loads the current selected Configuration game. '''
    config = configparser.ConfigParser()
    config.read(config_file, encoding="utf-8")
    if not config.has_section("Options"):
        config["Options"] = {}
        return "0"
    
    return config.get("Options", "Game", fallback=Manager._patchInfo.ID)

def save_config_game(Manager, config_file):
    ''' Saves the current selected Configuration game. '''
    config = configparser.ConfigParser()
    config.read(config_file, encoding="utf-8")
    if not config.has_section("Options"):
        config["Options"] = {}
    config.set("Options", "Game", Manager._patchInfo.ID)

    with open(config_file, 'w', encoding="utf-8") as file:
        config.write(file)
