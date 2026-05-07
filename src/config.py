import os
import sys


def get_bundled_config():
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    data_dir = os.path.join(base_path, "data")
    return {
        "plan_file": os.path.join(data_dir, "active_plan.md"),
        "routine_file": os.path.join(data_dir, "active_routine.md"),
        "data_dir": data_dir,
        "state_file": os.path.join(data_dir, "app_state.json")
    }


DEFAULT_CONFIG = get_bundled_config()
