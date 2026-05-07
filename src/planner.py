import os
import json
import re


class PlannerLogic:
    def __init__(self, config):
        self.config = config
        self.plan_data = {}
        self.routine_slots = []
        self.state = {}

        os.makedirs(self.config["data_dir"], exist_ok=True)
        self.load_original_markdown()
        self.load_state()

    def load_original_markdown(self):
        self.routine_slots = []
        if os.path.exists(self.config["routine_file"]):
            with open(self.config["routine_file"], "r", encoding="utf-8") as f:
                for line in f:
                    match = re.search(r'\*\s+\*\*([\d:]+ to [\d:]+)\*\*(.*)', line)
                    if match:
                        time_slot = match.group(1).strip()
                        desc = match.group(2).strip()
                        if "Study Block" in desc:
                            self.routine_slots.append(time_slot)

        current_day = None
        self.plan_data = {}
        if os.path.exists(self.config["plan_file"]):
            with open(self.config["plan_file"], "r", encoding="utf-8") as f:
                for line in f:
                    day_match = re.search(r'\*\*(Day \d+:.*?)\*\*', line)
                    if day_match:
                        current_day = day_match.group(1)
                        self.plan_data[current_day] = []
                        continue

                    if current_day and line.strip().startswith('* **'):
                        self.plan_data[current_day].append({
                            "original_text": line.strip(),
                            "id": line.strip()[:20],
                            "completed": False,
                            "assigned_slot": None
                        })

    def load_state(self):
        if os.path.exists(self.config["state_file"]):
            try:
                with open(self.config["state_file"], "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception:
                self.state = self.plan_data.copy()
        else:
            self.state = self.plan_data.copy()

    def save_state(self):
        with open(self.config["state_file"], "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=4)

    def reset_day(self, day_key):
        if day_key in self.plan_data:
            self.state[day_key] = [dict(task) for task in self.plan_data[day_key]]
            self.save_state()

    def update_task(self, day_key, task_id, completed=None, assigned_slot=None):
        for task in self.state.get(day_key, []):
            if task["id"] == task_id:
                if completed is not None:
                    task["completed"] = completed
                if assigned_slot is not False:
                    task["assigned_slot"] = assigned_slot
                break
        self.save_state()

    def export_day_to_markdown(self, day_key, filepath):
        tasks = self.state.get(day_key, [])
        if not tasks:
            return

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"### Exported Plan for {day_key}\n\n")

            f.write("**Daily Routine**\n")
            for slot in self.routine_slots:
                assigned = [t for t in tasks if t.get("assigned_slot") == slot]
                if assigned:
                    for t in assigned:
                        status = "[x]" if t.get("completed") else "[ ]"
                        clean_text = t['original_text'].replace('*', '').strip()
                        f.write(f"* **{slot}** {status} {clean_text}\n")
                else:
                    f.write(f"* **{slot}** Empty\n")

            f.write("\n**Unassigned Tasks**\n")
            unassigned = [t for t in tasks if not t.get("assigned_slot")]
            for t in unassigned:
                status = "[x]" if t.get("completed") else "[ ]"
                clean_text = t['original_text'].replace('*', '').strip()
                f.write(f"* {status} {clean_text}\n")
