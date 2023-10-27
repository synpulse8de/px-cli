import platform


def is_cpu_arm() -> bool:
    platform.machine()
    return "arm" in platform.machine()
