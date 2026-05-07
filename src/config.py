import os
import json
import sys


def get_bundled_config():
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return {
        "plan_file": os.path.join(base_path, "plan.md"),
        "routine_file": os.path.join(base_path, "routine.md"),
        "data_dir": os.path.join(base_path, "data"),
        "state_file": os.path.join(base_path, "data", "app_state.json")
    }


DEFAULT_CONFIG = get_bundled_config()
