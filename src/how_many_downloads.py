import requests
import time
import math

GITHUB = "TOTK-mods"
OWNER = "MaxLastBreath"

url = f"https://api.github.com/repos/MaxLastBreath/TOTK-mods/releases"
search_tag = "manager"


def write_print(args):
    file.write(args)
    print(args)

# fmt: off
if __name__ == "__main__":
    response = requests.get(url)
    with open("Downloads.txt", "w") as file:
        if response.status_code == 200:
            response.raise_for_status()
            release_info = response.json()
            release_info.reverse()
        count_linux = 0
        count_windows = 0
        count_mac = 0
        total_count = 0
        current_mac_count = 0
        current_windows_amount = 0
        current_linux_amount = 0

        for item in release_info:
            if not item.get("tag_name").startswith(search_tag):
                continue
            assets = item.get("assets")
            for item in assets:
                amount = int(item.get("download_count"))
                total_count += amount

        write_print(f"__TOTAL DOWNLOADS__ {total_count}\n")
        for item in release_info:
            if not item.get("tag_name").startswith(search_tag):
                continue
            write_print(item.get("tag_name")+ "")
            assets = item.get("assets")
            for item in assets:
                name = item.get("name")
                date = item.get("created_at")
                if name.endswith(".AppImage") or name.startswith("Linux") or name.endswith("Linux.zip"):
                    amount = int(item.get("download_count"))
                    current_linux_amount = amount
                    count_linux += amount

                if name.endswith(".exe") or name.startswith("Windows") or name.endswith("Windows.zip"):
                    amount = int(item.get("download_count"))
                    current_windows_amount = amount
                    count_windows += amount

                if name.endswith("MacOS_Intel.zip") or name.endswith("MacOS_Silicon.zip"):
                    amount = int(item.get("download_count"))
                    current_mac_count = amount
                    count_mac += amount
            write_print(f" - Date: {date}\n"
            f"Total Count: {count_windows + count_linux + count_mac}\n")
            write_print(f"Linux Downloads: {current_linux_amount}\n")
            write_print(f"Windows Downloads: {current_windows_amount}\n")
            write_print(f"Mac Downloads: {current_mac_count}\n\n")

        write_print(f"\n\n--TOTAL VERSION COUNT--\n"
                  f"Of which Linux has: {count_linux} and {round((count_linux / total_count) * 100)}% Downloads\n"
                  f"Of which Windows has {count_windows} and {round((count_windows / total_count) * 100)}% Downloads\n"
                  f"Of which MacOS has {count_mac} and {round((count_mac / total_count) * 100)}% Downloads\n"
                  f"As of {time.ctime()} Total download count is: {total_count}\n")
