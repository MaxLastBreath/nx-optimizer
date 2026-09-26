import configparser
import os
import re
import platform
from modules.logger import *
from configparser import Interpolation


# Ensure % doesn't cause issues in config, with mods like % drop rate.
class CustomInterpolation(Interpolation):
    def before_get(self, parser, section, option, value, defaults):
        return value

    def before_set(self, parser, section, option, value):
        if value.startswith("%") and not value.startswith("%%"):
            return value.replace("%", "%%", 1)
        return value


def get_config_parser():
    config = configparser.ConfigParser(interpolation=CustomInterpolation())
    return config


def list_all_folders(directory_path):
    folders = []
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            folders.append(item)
    return folders


def find_folder_index_by_name(directory_path, folder_name):
    all_folders = list_all_folders(directory_path)
    try:
        index = all_folders.index(folder_name)
        return index
    except ValueError:
        return None


def find_title_id_index(config, config_title_id):
    section = f"DisabledAddOns"
    if not config.has_section(section):
        config.add_section(section)
        log.info(
            f"Config has not been able, identify config_title_id: {config_title_id},"
            f"the manager will continue but the mods may not be turned off as expected."
        )
        return None
    else:
        for key, value in config.items(section):
            if value == str(config_title_id):
                TitleIndexnum = key.split("\\")[0]
                return TitleIndexnum
    return None


def remove_duplicates(arr):
    return list(set(arr))


def get_d_values(config, properindex):
    section = "DisabledAddOns"
    d_values = []
    for key, value in config.items(section):
        if key.startswith(f"{properindex}\\disabled\\") and key.endswith("\\d"):
            d_values.append(value)
    return d_values


def clean_disabled_addons(config, config_title_id):
    section = "DisabledAddOns"
    keys_to_remove = []
    properindex = find_title_id_index(config, config_title_id)
    if properindex == None:
        return
    for key in config[section]:
        match = re.match("^" + properindex + r"\\disabled\\\d+\\d", key)
        if match:
            keys_to_remove.append(key)

    for key in keys_to_remove:
        config.remove_option(section, key)


def find_and_remove_entry(
    configdir, directory, config, config_title_id, entry_to_remove
):
    properindex = find_title_id_index(config, config_title_id)
    if properindex == None:
        return

    section = "DisabledAddOns"
    d_values = sorted(get_d_values(config, properindex))
    if not config.has_section(section):
        config.add_section(section)

    TitleIndexnum = find_title_id_index(config, config_title_id)
    testforfolder = find_folder_index_by_name(directory, entry_to_remove)
    if testforfolder is None:
        return

    try:
        while entry_to_remove in d_values:
            d_values.remove(entry_to_remove)
    except ValueError:
        return

    clean_d_values = remove_duplicates(d_values)
    clean_d_values.sort()
    disabledindex = len(clean_d_values)
    clean_disabled_addons(config, config_title_id)
    for i, d_value in enumerate(clean_d_values):
        key = f"{properindex}\\disabled\\{i + 1}\\d"
        default_key = f"{properindex}\\disabled\\{i + 1}\\d\\default"
        config.set(section, key, d_value)
        config.set(section, default_key, "false")

    config.set(section, f"{TitleIndexnum}\\disabled\\size", str(disabledindex))
    write_config_file(configdir, config)


def add_entry(configdir, directory, config, config_title_id, entry_to_add):

    properindex = find_title_id_index(config, config_title_id)
    if properindex == None:
        return
    section = f"DisabledAddOns"
    if not config.has_section(section):
        config.add_section(section)
    TitleIndexnum = find_title_id_index(config, config_title_id)
    try:
        testforfolder = find_folder_index_by_name(directory, entry_to_add)
    except ValueError:
        return

    if testforfolder is None:
        return
    # Check if the entry already exists
    d_values = sorted(get_d_values(config, properindex))
    if entry_to_add in d_values:
        # print(f"Already exists{entry_to_add}")
        return
    log.info(f"Disabling: {entry_to_add}")
    d_values.append(f"{entry_to_add}")
    clean_d_values = remove_duplicates(d_values)
    clean_d_values.sort()
    disabledindex = len(clean_d_values)
    clean_disabled_addons(config, config_title_id)
    for i, d_value in enumerate(clean_d_values):
        key = f"{properindex}\\disabled\\{i + 1}\\d"
        default_key = f"{properindex}\\disabled\\{i + 1}\\d\\default"
        config.set(section, key, d_value)
        config.set(section, default_key, "false")

    config.set(section, f"{TitleIndexnum}\\disabled\\size", str(disabledindex))
    write_config_file(configdir, config)


def modify_disabled_key(
    configdir, directory, config, config_title_id, entry, action="add"
):
    if platform.system() == "Linux":
        return

    if config == None:
        return

    try:
        if platform.system() == "Windows":
            if action == "add":
                print("Disabling mod:", entry, config_title_id)
                add_entry(configdir, directory, config, config_title_id, entry)
            if action == "remove":
                print("Enabling mod:", entry, config_title_id)
                find_and_remove_entry(configdir, directory, config, config_title_id, entry)
    except configparser.InterpolationSyntaxError as e:
        log.error(f"Failed to Patch Config files, likely due to a %% character in one of the mods {e}")


def write_config_file(configdir, config):
    with open(configdir, "w", encoding="utf-8") as config_file:
        config.write(config_file, space_around_delimiters=False)
