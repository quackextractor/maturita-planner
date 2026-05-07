import os
import re
import shutil


class PlannerLogic:
    def __init__(self, config):
        self.config = config
        self.plan_data = {}
        self.routine_slots = []
        self.state = {}
        self.last_saved_mtime = 0

        os.makedirs(self.config["data_dir"], exist_ok=True)
        self.load_data()

    def process_initial_drop(self, plan_file, routine_file):
        shutil.copy(plan_file, self.config["original_plan"])
        shutil.copy(plan_file, self.config["active_plan"])
        shutil.copy(routine_file, self.config["original_routine"])
        shutil.copy(routine_file, self.config["active_routine"])
        self.load_data()

    def load_data(self):
        self.routine_slots = []
        if os.path.exists(self.config["active_routine"]):
            with open(self.config["active_routine"], "r", encoding="utf-8") as f:
                for line in f:
                    match = re.search(r'\*\s+\*\*([\d:]+ to [\d:]+)\*\*(.*)', line)
                    if match:
                        time_slot = match.group(1).strip()
                        desc = match.group(2).strip()
                        if "Study Block" in desc:
                            self.routine_slots.append(time_slot)

        self.plan_data = {}
        current_day = None
        if os.path.exists(self.config["active_plan"]):
            with open(self.config["active_plan"], "r", encoding="utf-8") as f:
                for line in f:
                    day_match = re.search(r'\*\*(Day \d+:.*?)\*\*', line)
                    if day_match:
                        current_day = day_match.group(1)
                        self.plan_data[current_day] = []
                        continue

                    if current_day and re.search(r'^\*\s*(?:\[[xX ]\]\s*)?\*\*', line.strip()):
                        text_line = line.strip()
                        completed = "[x]" in text_line.lower()

                        clean_text = re.sub(r'^\*\s*(?:\[[xX ]\]\s*)?', '', text_line)

                        assigned_slot = None
                        slot_match = re.search(r'\(Assigned: ([\d:]+ to [\d:]+)\)', clean_text)
                        if slot_match:
                            assigned_slot = slot_match.group(1)
                            clean_text = clean_text.replace(slot_match.group(0), '').strip()

                        task_id = clean_text[:40]

                        self.plan_data[current_day].append({
                            "original_text": text_line,
                            "clean_text": clean_text,
                            "id": task_id,
                            "completed": completed,
                            "assigned_slot": assigned_slot
                        })

        self.state = self.plan_data.copy()
        if os.path.exists(self.config["active_plan"]):
            self.last_saved_mtime = os.path.getmtime(self.config["active_plan"])

    def save_plan(self):
        if not self.state:
            return
        with open(self.config["active_plan"], "w", encoding="utf-8") as f:
            f.write("### Maturita Study Plan\n\n")
            for day, tasks in self.state.items():
                f.write(f"**{day}**\n")
                for t in tasks:
                    status = "[x]" if t["completed"] else "[ ]"
                    slot_info = f" (Assigned: {t['assigned_slot']})" if t["assigned_slot"] else ""
                    f.write(f"* {status} {t['clean_text']}{slot_info}\n")
                f.write("\n")

        self.last_saved_mtime = os.path.getmtime(self.config["active_plan"])

    def reset_day(self, day_key):
        original_tasks = []
        current_day = None
        if os.path.exists(self.config["original_plan"]):
            with open(self.config["original_plan"], "r", encoding="utf-8") as f:
                for line in f:
                    day_match = re.search(r'\*\*(Day \d+:.*?)\*\*', line)
                    if day_match:
                        current_day = day_match.group(1)
                        continue
                    if current_day == day_key and re.search(r'^\*\s*(?:\[[xX ]\]\s*)?\*\*', line.strip()):
                        text_line = line.strip()
                        clean_text = re.sub(r'^\*\s*(?:\[[xX ]\]\s*)?', '', text_line)
                        task_id = clean_text[:40]
                        original_tasks.append({
                            "original_text": text_line,
                            "clean_text": clean_text,
                            "id": task_id,
                            "completed": False,
                            "assigned_slot": None
                        })
        self.state[day_key] = original_tasks
        self.save_plan()

    def reset_plan(self):
        if os.path.exists(self.config["original_plan"]):
            shutil.copy(self.config["original_plan"], self.config["active_plan"])
        self.load_data()

    def major_deletion(self):
        files_to_delete = [
            self.config["original_plan"], self.config["active_plan"],
            self.config["original_routine"], self.config["active_routine"]
        ]
        for f in files_to_delete:
            if os.path.exists(f):
                os.remove(f)
        self.state = {}
        self.plan_data = {}
        self.routine_slots = []

    def update_task(self, day_key, task_id, completed=None, assigned_slot="NO_CHANGE", auto_save=True):
        for task in self.state.get(day_key, []):
            if task["id"] == task_id:
                if completed is not None:
                    task["completed"] = completed
                if assigned_slot != "NO_CHANGE":
                    task["assigned_slot"] = assigned_slot
                break

        if auto_save:
            self.save_plan()
