import pytest
import os
import time
from src.planner import PlannerLogic


@pytest.fixture
def temp_config(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return {
        "data_dir": str(data_dir),
        "original_plan": str(data_dir / "plan_orig.md"),
        "active_plan": str(data_dir / "plan.md"),
        "original_routine": str(data_dir / "routine_orig.md"),
        "active_routine": str(data_dir / "routine.md"),
    }


def test_planner_logic_init(temp_config):
    planner = PlannerLogic(temp_config)
    assert planner.plan_data == {}
    assert planner.routine_slots == []
    assert planner.ast == []
    assert os.path.exists(temp_config["data_dir"])


def test_load_data_with_files(temp_config):
    # Create dummy routine
    with open(temp_config["active_routine"], "w", encoding="utf-8") as f:
        f.write("* **08:00 to 09:30**: Study Block 1\n")
        f.write("* **10:00 to 11:30**: Rest\n")

    # Create dummy plan with extra formatting to ensure preservation
    with open(temp_config["active_plan"], "w", encoding="utf-8") as f:
        f.write("### Plan Title 2026\n")
        f.write("**Day 1: May 07**\n")
        f.write("* [ ] **Linear Algebra**\n")
        f.write("* *Total: 10 hours*\n")

    planner = PlannerLogic(temp_config)
    assert len(planner.routine_slots) == 1
    assert planner.routine_slots[0]["time"] == "08:00 to 09:30"
    assert planner.routine_slots[0]["desc"] == "Study Block 1"
    assert "Day 1: May 07" in planner.plan_data
    assert planner.plan_data["Day 1: May 07"][0]["clean_text"] == "**Linear Algebra**"
    assert planner.plan_data["Day 1: May 07"][0]["completed"] is False

    # Verify AST structure instead of raw lines
    assert len(planner.ast) == 2
    assert planner.ast[0]["type"] == "raw"
    assert planner.ast[1]["type"] == "day_section"
    assert len(planner.ast[1]["items"]) == 2


def test_load_data_with_badges(temp_config):
    with open(temp_config["active_plan"], "w", encoding="utf-8") as f:
        f.write("**Day 1: Math**\n")
        f.write("* [ ] **PV 1:** Adresování (Hard, 12 iterací, 2.0h) - Focus: Theory\n")

    planner = PlannerLogic(temp_config)
    task = planner.plan_data["Day 1: Math"][0]

    assert task["subject"] == "PV"
    assert task["badges"] == ["Hard", "12 iterací", "2.0h"]
    assert "(Hard" not in task["display_text"]
    assert "Adresování" in task["display_text"]


def test_update_task(temp_config):
    # Create dummy plan
    with open(temp_config["active_plan"], "w", encoding="utf-8") as f:
        f.write("**Day 1: Math**\n")
        f.write("* [ ] **Linear Algebra**\n")

    planner = PlannerLogic(temp_config)
    task_id = planner.plan_data["Day 1: Math"][0]["id"]

    planner.update_task("Day 1: Math", task_id, completed=True)
    assert planner.state["Day 1: Math"][0]["completed"] is True

    # Verify file saved
    planner.load_data()
    assert planner.plan_data["Day 1: Math"][0]["completed"] is True


def test_last_saved_mtime_update(temp_config):
    with open(temp_config["active_plan"], "w", encoding="utf-8") as f:
        f.write("**Day 1: Math**\n")
        f.write("* [ ] **Linear Algebra**\n")

    planner = PlannerLogic(temp_config)
    initial_mtime = planner.last_saved_mtime
    assert initial_mtime > 0

    task_id = planner.plan_data["Day 1: Math"][0]["id"]

    # Force a wait to ensure mtime changes (filesystem precision)
    time.sleep(0.1)

    planner.update_task("Day 1: Math", task_id, completed=True, auto_save=True)

    assert planner.last_saved_mtime > initial_mtime
    assert planner.last_saved_mtime == os.path.getmtime(temp_config["active_plan"])
