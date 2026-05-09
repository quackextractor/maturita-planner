import os
import sys


def get_bundled_config():
    # Check if the application is run as a bundled executable
    if getattr(sys, 'frozen', False):
        # sys.executable points to the actual .exe / binary file location
        base_path = os.path.dirname(sys.executable)
    else:
        # Running from source (e.g., python main.py)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    data_dir = os.path.join(base_path, "data")

    return {
        "original_plan": os.path.join(data_dir, "original_plan.md"),
        "active_plan": os.path.join(data_dir, "active_plan.md"),
        "original_routine": os.path.join(data_dir, "original_routine.md"),
        "active_routine": os.path.join(data_dir, "active_routine.md"),
        "data_dir": data_dir
    }


DEFAULT_CONFIG = get_bundled_config()
