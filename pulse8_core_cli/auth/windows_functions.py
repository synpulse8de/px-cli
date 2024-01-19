import winreg

from rich import print
from pulse8_core_cli.shared.platform_discovery import is_windows


def adjust_windows_registry():
    if is_windows():
        reg_file_system_key_read = winreg.OpenKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\\CurrentControlSet\\Control\\FileSystem",
            0,
            winreg.KEY_READ,
        )
        long_paths_value = winreg.QueryValueEx(
            reg_file_system_key_read, "LongPathsEnabled"
        )[0]
        if long_paths_value == 0:
            try:
                reg_file_system_key = winreg.OpenKeyEx(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\\CurrentControlSet\\Control\\FileSystem",
                    0,
                    winreg.KEY_SET_VALUE,
                )
                winreg.SetValueEx(
                    reg_file_system_key, "LongPathsEnabled", 0, winreg.REG_DWORD, 1
                )
            except PermissionError:
                print(
                    "[red]Pulse8 CLI needs to update LongPathsEnabled registry key in order "
                    "to ensure templates are correctly created. Please run your terminal as "
                    "Administrator first time to set this value. Next time you don't have to "
                    "run it as Administrator.[/red]"
                )
                exit(1)
