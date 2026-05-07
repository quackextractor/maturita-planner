import os
import sys


def get_bundled_config():
    try:
        base_path = sys._MEIPASS
    except AttributeError:
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
