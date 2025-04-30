import platform


def is_cpu_arm() -> bool:
    platform.machine()
    return "arm" in platform.machine()


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_macos() -> bool:
    return platform.system() == "Darwin"


def is_linux() -> bool:
    return platform.system() == "Linux"
