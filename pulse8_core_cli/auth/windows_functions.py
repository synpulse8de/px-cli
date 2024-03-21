import winreg
import os
import pyuac

from rich import print


def setup_win_registry():
    long_paths_value = get_win_registry_value_long_paths_enabled()
    if long_paths_value == 0:
        try:
            print("Updating Windows registry...")
            reg_file_system_key = winreg.OpenKeyEx(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\\CurrentControlSet\\Control\\FileSystem",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(
                reg_file_system_key, "LongPathsEnabled", 0, winreg.REG_DWORD, 1
            )
            if reg_file_system_key:
                winreg.FlushKey(reg_file_system_key)
                winreg.CloseKey(reg_file_system_key)
            print("[green]Successfully updated Windows registry.[/green]")
        except PermissionError:
            print(
                "[red]Failed to update Windows registry. Please try running 'pulse8 utils setup-winreg' "
                "manually with administrator privileges or update registry key manually by setting "
                "'Computer\\HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\FileSystem' to '1'[/red]"
            )
            exit(1)


def setup_win_registry_admin(caller_command: str = None):
    if get_win_registry_value_long_paths_enabled() == 0:
        return_code = pyuac.runAsAdmin(cmdLine=["pulse8", "utils", "setup-winreg"])
        if return_code == 0:
            print("[green]Successfully updated Windows registry.[/green]")
            if caller_command is not None:
                os.system(caller_command)
                exit(0)
        else:
            print(
                "[red]Failed to update Windows registry. Please try running 'pulse8 utils setup-winreg' "
                "manually with administrator privileges or update registry key manually by setting "
                "'Computer\\HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\FileSystem' to '1'[/red]"
            )
            exit(return_code)


def get_win_registry_value_long_paths_enabled():
    reg_file_system_key_read = winreg.OpenKeyEx(
        winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\\CurrentControlSet\\Control\\FileSystem",
        0,
        winreg.KEY_READ,
    )
    return winreg.QueryValueEx(
        reg_file_system_key_read, "LongPathsEnabled"
    )[0]
