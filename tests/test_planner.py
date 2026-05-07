import pytest
import os
import shutil
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
    assert os.path.exists(temp_config["data_dir"])


def test_load_data_with_files(temp_config):
    # Create dummy routine
    with open(temp_config["active_routine"], "w", encoding="utf-8") as f:
        f.write("* **08:00 to 09:30** Study Block 1\n")
        f.write("* **10:00 to 11:30** Rest\n")

    # Create dummy plan
    with open(temp_config["active_plan"], "w", encoding="utf-8") as f:
        f.write("**Day 1: Math**\n")
        f.write("* [ ] **Linear Algebra**\n")

    planner = PlannerLogic(temp_config)
    assert "08:00 to 09:30" in planner.routine_slots
    assert "10:00 to 11:30" not in planner.routine_slots
    assert "Day 1: Math" in planner.plan_data
    assert planner.plan_data["Day 1: Math"][0]["clean_text"] == "**Linear Algebra**"
    assert planner.plan_data["Day 1: Math"][0]["completed"] is False


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
