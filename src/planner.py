import os
import re
import shutil
import copy
import datetime


class PlannerLogic:
    def __init__(self, config):
        self.config = config
        self.plan_data = {}
        self.routine_slots = []
        self.ast = []
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
                    match = re.search(r'\*\s+\*\*([\d:]+\s*(?:to|-)\s*[\d:]+)\*\*(.*)', line)
                    if match:
                        time_slot = match.group(1).strip()
                        desc = match.group(2).strip()
                        if "Study Block" in desc:
                            desc_clean = desc.lstrip(":; -").strip()
                            if desc_clean.endswith("."):
                                desc_clean = desc_clean[:-1]
                            self.routine_slots.append({"time": time_slot, "desc": desc_clean})

        self.ast = []
        global_year = datetime.date.today().year

        if os.path.exists(self.config["active_plan"]):
            with open(self.config["active_plan"], "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                year_match = re.search(r'\b(20\d{2})\b', line)
                if year_match:
                    global_year = int(year_match.group(1))
                    break

            current_day_block = None
            for i, line in enumerate(lines):
                day_match = re.search(r'\*\*(Day \d+:.*?)\*\*', line)
                if day_match:
                    if current_day_block:
                        self.ast.append(current_day_block)

                    day_key = day_match.group(1)
                    date_obj = None
                    try:
                        month_str_match = re.search(r'([a-zA-Z]+)\s+(\d+)', day_key)
                        if month_str_match:
                            m_str = month_str_match.group(1)[:3]
                            d_int = int(month_str_match.group(2))
                            date_obj = datetime.datetime.strptime(f"{m_str} {d_int} {global_year}", "%b %d %Y").date()
                    except Exception:
                        pass

                    current_day_block = {
                        'type': 'day_section',
                        'day_key': day_key,
                        'header': line,
                        'date': date_obj,
                        'items': []
                    }
                    continue

                if current_day_block:
                    if re.search(r'^\*\s*(?:\[[xX ]\]\s*)?\*\*', line.strip()):
                        text_line = line.strip()
                        completed = "[x]" in text_line.lower() or "[X]" in text_line
                        clean_text = re.sub(r'^\*\s*(?:\[[xX ]\]\s*)?', '', text_line)

                        assigned_slot = None
                        slot_match = re.search(r'\s*\(Assigned: ([\d:]+\s*(?:to|-)\s*[\d:]+)\)', clean_text)
                        if slot_match:
                            assigned_slot = slot_match.group(1)
                            clean_text = clean_text.replace(slot_match.group(0), '').strip()

                        task_id = clean_text[:40]
                        display_text = clean_text
                        subject = None
                        badges = []

                        try:
                            subj_match = re.search(r'\*\*([A-Za-zČčŘřŠšŽžÝýÁáÍíÉéÚúŮůĚě]+)', display_text)
                            if subj_match:
                                subject = subj_match.group(1).upper()

                            badge_match = re.search(r'\(([^)]+)\)', display_text)
                            if badge_match:
                                badges_str = badge_match.group(1)
                                if ',' in badges_str or any(kw in badges_str.lower() for kw in ['hard', 'medium', 'easy', 'iterac', 'h']):
                                    badges = [b.strip() for b in badges_str.split(',')]
                                    display_text = display_text.replace(badge_match.group(0), '').strip()
                                    display_text = re.sub(r'\s+-\s+', ' - ', display_text)
                                    display_text = re.sub(r'\s{2,}', ' ', display_text)
                        except Exception:
                            pass

                        task_data = {
                            "original_text": text_line,
                            "clean_text": clean_text,
                            "display_text": display_text,
                            "subject": subject,
                            "badges": badges,
                            "id": task_id,
                            "completed": completed,
                            "assigned_slot": assigned_slot,
                            "day_key": day_key
                        }
                        current_day_block['items'].append({'type': 'task', 'data': task_data})
                    else:
                        current_day_block['items'].append({'type': 'raw', 'text': line})
                else:
                    self.ast.append({'type': 'raw', 'text': line})

            if current_day_block:
                self.ast.append(current_day_block)

        self.rollover_expired_tasks()
        self._sync_state_from_ast()

        if os.path.exists(self.config["active_plan"]):
            self.last_saved_mtime = os.path.getmtime(self.config["active_plan"])

    def _sync_state_from_ast(self):
        self.state = {}
        self.plan_data = {}
        for block in self.ast:
            if block['type'] == 'day_section':
                dk = block['day_key']
                self.state[dk] = []
                self.plan_data[dk] = []
                for item in block['items']:
                    if item['type'] == 'task':
                        self.state[dk].append(item['data'])
                        self.plan_data[dk].append(item['data'])

    def rollover_expired_tasks(self):
        today = datetime.date.today()
        target_block = None

        for block in self.ast:
            if block['type'] == 'day_section' and block['date'] == today:
                target_block = block
                break

        if not target_block:
            for block in self.ast:
                if block['type'] == 'day_section' and block['date'] and block['date'] >= today:
                    target_block = block
                    break

        if not target_block:
            for block in self.ast:
                if block['type'] == 'day_section':
                    target_block = block
                    break

        if not target_block:
            return

        tasks_moved = False
        for block in self.ast:
            if block['type'] == 'day_section' and block != target_block:
                if block['date'] and target_block['date'] and block['date'] < target_block['date']:
                    items_to_keep = []
                    for item in block['items']:
                        if item['type'] == 'task' and not item['data']['completed']:
                            item['data']['assigned_slot'] = None
                            item['data']['day_key'] = target_block['day_key']
                            target_block['items'].append(item)
                            tasks_moved = True
                        else:
                            items_to_keep.append(item)
                    block['items'] = items_to_keep

        if tasks_moved:
            self.save_plan()

    def save_plan(self):
        if not self.ast:
            return

        plan_lines = []
        for block in self.ast:
            if block['type'] == 'raw':
                plan_lines.append(block['text'])
            elif block['type'] == 'day_section':
                plan_lines.append(block['header'])
                for item in block['items']:
                    if item['type'] == 'raw':
                        plan_lines.append(item['text'])
                    elif item['type'] == 'task':
                        t = item['data']
                        status = "[x]" if t["completed"] else "[ ]"
                        slot_info = f" (Assigned: {t['assigned_slot']})" if t["assigned_slot"] else ""
                        plan_lines.append(f"* {status} {t['clean_text']}{slot_info}\n")

        with open(self.config["active_plan"], "w", encoding="utf-8") as f:
            f.writelines(plan_lines)

        self.last_saved_mtime = os.path.getmtime(self.config["active_plan"])

    def reset_day(self, day_key):
        if not os.path.exists(self.config["original_plan"]):
            return

        with open(self.config["original_plan"], "r", encoding="utf-8") as f:
            original_lines = f.readlines()

        target_block = None
        for b in self.ast:
            if b['type'] == 'day_section' and b['day_key'] == day_key:
                target_block = b
                break

        if target_block:
            target_block['items'] = []
            current_day = None
            for line in original_lines:
                day_match = re.search(r'\*\*(Day \d+:.*?)\*\*', line)
                if day_match:
                    current_day = day_match.group(1)
                    continue

                if current_day == day_key:
                    if re.search(r'^\*\s*(?:\[[xX ]\]\s*)?\*\*', line.strip()):
                        text_line = line.strip()
                        clean_text = re.sub(r'^\*\s*(?:\[[xX ]\]\s*)?', '', text_line)
                        task_id = clean_text[:40]
                        task_data = {"id": task_id, "clean_text": clean_text, "completed": False, "assigned_slot": None, "day_key": day_key}
                        target_block['items'].append({'type': 'task', 'data': task_data})
                    else:
                        target_block['items'].append({'type': 'raw', 'text': line})

        self.save_plan()
        self.load_data()

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
        self.ast = []

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

    def move_tasks_to_day(self, task_ids, target_day_key):
        target_block = next((b for b in self.ast if b['type'] == 'day_section' and b['day_key'] == target_day_key), None)
        if not target_block:
            return

        tasks_moved = False
        for block in self.ast:
            if block['type'] == 'day_section' and block != target_block:
                items_to_keep = []
                for item in block['items']:
                    if item['type'] == 'task' and item['data']['id'] in task_ids:
                        item['data']['assigned_slot'] = None
                        item['data']['day_key'] = target_day_key
                        target_block['items'].append(item)
                        tasks_moved = True
                    else:
                        items_to_keep.append(item)
                block['items'] = items_to_keep

        if tasks_moved:
            self.save_plan()
            self._sync_state_from_ast()
