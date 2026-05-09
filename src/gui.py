import tkinter as tk
import customtkinter as ctk
import os
import re
import sys
import datetime
import subprocess
import hashlib
import colorsys
from tkinterdnd2 import DND_FILES
from src.config import DEFAULT_CONFIG
from src.planner import PlannerLogic


def get_deterministic_colors(text):
    """
    Generates a consistent color pair by snapping to a predefined list of
    visually distinct hues to avoid muddy or near-identical generated colors.
    """
    hash_obj = hashlib.md5(text.lower().strip().encode('utf-8'))
    hash_int = int(hash_obj.hexdigest(), 16)

    # Pre-selected hues that avoid the hardcoded Red, Orange, Green, Blue, Purple
    # and are spaced exactly 15 degrees apart to guarantee visual distinctness.
    safe_hues = [
        45, 60, 75, 90,       # Yellow to Lime
        150, 165, 180, 195,   # Teal to Cyan
        300, 315, 330, 345    # Magenta to Pink
    ]

    hue_degrees = safe_hues[hash_int % len(safe_hues)]
    hue = hue_degrees / 360.0

    # Generate a light color for Light Mode and a dark color for Dark Mode
    light_rgb = colorsys.hls_to_rgb(hue, 0.85, 0.65)
    dark_rgb = colorsys.hls_to_rgb(hue, 0.35, 0.65)

    light_hex = "#{:02x}{:02x}{:02x}".format(int(light_rgb[0] * 255), int(light_rgb[1] * 255), int(light_rgb[2] * 255))
    dark_hex = "#{:02x}{:02x}{:02x}".format(int(dark_rgb[0] * 255), int(dark_rgb[1] * 255), int(dark_rgb[2] * 255))

    return (light_hex, dark_hex)


class AutoScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent_canvas.bind("<Configure>", self._on_canvas_configure, add="+")
        self.bind("<Configure>", lambda e: self.check_scrollbar(), add="+")

    def _on_canvas_configure(self, event):
        self._parent_canvas.itemconfig(self._create_window_id, width=event.width)
        self.check_scrollbar()

    def check_scrollbar(self, event=None):
        def _check():
            try:
                if self.winfo_reqheight() <= self._parent_canvas.winfo_height():
                    self._scrollbar.grid_remove()
                else:
                    self._scrollbar.grid()
            except Exception:
                pass
        self.after(10, _check)


class DragManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.dragged_widget = None
        self.drag_data = None
        self.offset_x = 0
        self.offset_y = 0
        self.start_x = 0
        self.start_y = 0
        self.intent_drag = False
        self.potential_widget = None

    def make_draggable(self, handle, widget_to_move, task_data):
        def _on_start(e):
            if self.app.current_view.get() == "Library":
                return "break"
            self.start_x = e.x_root
            self.start_y = e.y_root
            self.intent_drag = False
            self.potential_widget = widget_to_move
            self.drag_data = task_data
            return "break"

        def _on_motion(e):
            if self.app.current_view.get() == "Library":
                return "break"
            if not self.intent_drag:
                if abs(e.x_root - self.start_x) > 5 or abs(e.y_root - self.start_y) > 5:
                    self.intent_drag = True
                    self.on_drag_start(e, self.potential_widget, self.drag_data)
            else:
                self.on_drag_motion(e)
            return "break"

        def _on_release(e):
            if self.app.current_view.get() == "Library":
                self.app.handle_task_click(e, task_data, widget_to_move)
                return "break"
            if self.intent_drag:
                self.on_drag_release(e)
            else:
                self.app.handle_task_click(e, task_data, widget_to_move)
            return "break"

        handle.bind("<ButtonPress-1>", _on_start)
        handle.bind("<B1-Motion>", _on_motion)
        handle.bind("<ButtonRelease-1>", _on_release)

        if isinstance(handle, ctk.CTkTextbox):
            handle._textbox.bind("<ButtonPress-1>", _on_start)
            handle._textbox.bind("<B1-Motion>", _on_motion)
            handle._textbox.bind("<ButtonRelease-1>", _on_release)

    def on_drag_start(self, event, widget, task_data):
        if task_data['id'] not in self.app.selected_task_ids:
            self.app.selected_task_ids = {task_data['id']}
            self.app.update_selection_visuals()

        selected_count = len(self.app.selected_task_ids)

        self.offset_x = event.x_root - widget.winfo_rootx()
        self.offset_y = event.y_root - widget.winfo_rooty()

        w, h = widget.winfo_width(), widget.winfo_height()
        self.dragged_widget = ctk.CTkFrame(
            self.app.root,
            fg_color=("gray85", "gray30"),
            border_width=2,
            corner_radius=6,
            width=w,
            height=h
        )
        self.dragged_widget.pack_propagate(False)

        if selected_count > 1:
            display_str = f"Moving {selected_count} study blocks..."
        else:
            display_str = task_data.get('display_text', task_data['clean_text'])

        proxy_label = ctk.CTkLabel(
            self.dragged_widget,
            text=display_str[:120] + "..." if len(display_str) > 120 else display_str,
            wraplength=w - 20,
            font=("Arial", 12)
        )
        proxy_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.original_widgets = []
        for tid in self.app.selected_task_ids:
            if tid in self.app.task_frames:
                tw = self.app.task_frames[tid]
                tw.pack_forget()
                self.original_widgets.append(tw)

        self.update_drag_position(event)
        self.dragged_widget.lift()
        self.app.root.configure(cursor="hand2")

    def on_drag_motion(self, event):
        if not self.dragged_widget:
            return
        self.update_drag_position(event)

    def update_drag_position(self, event):
        x = event.x_root - self.app.root.winfo_rootx() - self.offset_x
        y = event.y_root - self.app.root.winfo_rooty() - self.offset_y
        self.dragged_widget.place(x=x, y=y)

    def on_drag_release(self, event):
        if not self.dragged_widget:
            return

        self.dragged_widget.destroy()
        self.dragged_widget = None

        x, y = event.x_root, event.y_root
        target = self.app.root.winfo_containing(x, y)

        slot_id = None
        if target:
            current = target
            while current:
                if hasattr(current, "slot_id"):
                    slot_id = current.slot_id
                    break
                current = current.master

        for tid in self.app.selected_task_ids:
            day_key = self.app._get_day_for_task(tid)
            self.app.logic.update_task(day_key, tid, assigned_slot=slot_id, auto_save=False)

        if self.app.autosave_var.get():
            self.app.logic.save_plan()
            self.app.update_timestamp_label()

        self.app.root.configure(cursor="")
        self.app.refresh_ui()

        self.original_widgets = []
        self.potential_widget = None


class PlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Maturita Planner")
        self.root.geometry("1100x700")

        self.logic = PlannerLogic(DEFAULT_CONFIG)
        self.drag_manager = DragManager(self)
        self.task_widgets = {}
        self.task_frames = {}
        self.slot_frames = {}
        self.selected_task_ids = set()
        self.last_clicked_task_id = None

        self.setup_ui()
        self.check_file_changes()

    def setup_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        if not os.path.exists(self.logic.config["active_plan"]) or not os.path.exists(self.logic.config["active_routine"]):
            self.show_welcome_screen()
        else:
            self.load_main_interface()

    def show_welcome_screen(self):
        self.welcome_frame = ctk.CTkFrame(self.root)
        self.welcome_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.welcome_frame, text="Maturita Planner Setup", font=("Arial", 24, "bold")).pack(pady=40)
        ctk.CTkLabel(self.welcome_frame, text="Drag and drop your plan.md AND routine.md files into this window.").pack(pady=10)

        self.plan_status = ctk.CTkLabel(self.welcome_frame, text="Plan file: Missing", text_color="red")
        self.plan_status.pack(pady=5)

        self.routine_status = ctk.CTkLabel(self.welcome_frame, text="Routine file: Missing", text_color="red")
        self.routine_status.pack(pady=5)

        self.dropped_plan = None
        self.dropped_routine = None

        self.welcome_frame.drop_target_register(DND_FILES)
        self.welcome_frame.dnd_bind('<<Drop>>', self.handle_file_drop)

    def handle_file_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            f_path = f.strip("{}")
            filename = os.path.basename(f_path).lower()
            if "plan" in filename:
                self.dropped_plan = f_path
                self.plan_status.configure(text=f"Plan loaded: {filename}", text_color="green")
            elif "routine" in filename:
                self.dropped_routine = f_path
                self.routine_status.configure(text=f"Routine loaded: {filename}", text_color="green")

        if self.dropped_plan and self.dropped_routine:
            self.logic.process_initial_drop(self.dropped_plan, self.dropped_routine)
            self.setup_ui()

    def load_main_interface(self):
        self.days = list(self.logic.state.keys())
        today = datetime.date.today()
        matched_day = None

        for b in self.logic.ast:
            if b['type'] == 'day_section' and b['date'] == today:
                matched_day = b['day_key']
                break

        if matched_day:
            self.current_day = matched_day
        elif self.days:
            for d in self.days:
                if any(not t['completed'] for t in self.logic.state[d]):
                    self.current_day = d
                    break
            if not self.current_day:
                self.current_day = self.days[0]
        else:
            self.current_day = None

        self.top_frame = ctk.CTkFrame(self.root, height=50)
        self.top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.current_view = tk.StringVar(value="Planner")
        self.view_seg = ctk.CTkSegmentedButton(self.top_frame, values=["Planner", "Library"], variable=self.current_view, command=self.switch_view)
        self.view_seg.pack(side=tk.LEFT, padx=10)

        self.day_var = tk.StringVar(value=self.current_day)
        self.planner_controls_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.planner_controls_frame.pack(side=tk.LEFT)

        ctk.CTkButton(self.planner_controls_frame, text="<", width=30, command=self.prev_day).pack(side=tk.LEFT, padx=(10, 2))
        self.day_combo = ctk.CTkComboBox(self.planner_controls_frame, variable=self.day_var, values=self.days, command=self.change_day)
        self.day_combo.pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(self.planner_controls_frame, text=">", width=30, command=self.next_day).pack(side=tk.LEFT, padx=(2, 10))

        self.save_label = ctk.CTkLabel(self.top_frame, text="Last saved: Never", text_color="gray")
        self.save_label.pack(side=tk.LEFT, padx=20)

        self.autosave_var = tk.BooleanVar(value=True)
        self.autosave_check = ctk.CTkCheckBox(self.top_frame, text="Autosave", variable=self.autosave_var, command=self.toggle_autosave)
        self.autosave_check.pack(side=tk.LEFT, padx=(20, 5))

        self.save_btn = ctk.CTkButton(self.top_frame, text="Save", command=self.manual_save, state="disabled", width=60)
        self.default_btn_fg = self.save_btn.cget("fg_color")
        self.save_btn.configure(fg_color="gray")
        self.save_btn.pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(self.top_frame, text="Major Deletion", command=self.major_deletion, fg_color="#b71c1c", hover_color="#7f0000").pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(self.top_frame, text="Reset Plan", command=self.reset_plan, fg_color="#e65100", hover_color="#b24200").pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(self.top_frame, text="Reset Day", command=self.reset_current_day, fg_color="#f57c00", hover_color="#ef6c00").pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(self.top_frame, text="Data", command=self.open_data_folder, fg_color="gray30", hover_color="gray40").pack(side=tk.RIGHT, padx=5)

        self.main_pane = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            bd=0,
            sashwidth=8,
            sashrelief=tk.RIDGE,
            sashcursor="sb_h_double_arrow",
            opaqueresize=False,
            bg="#4a4a4a"
        )
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_container = ctk.CTkFrame(self.main_pane, fg_color="transparent")
        self.main_pane.add(self.left_container, minsize=350, stretch="always")
        self.left_frame = AutoScrollableFrame(self.left_container, label_text="Unassigned Tasks")
        self.left_frame.pack(fill=tk.BOTH, expand=True)

        self.right_container = ctk.CTkFrame(self.main_pane, fg_color="transparent")
        self.main_pane.add(self.right_container, minsize=500, stretch="always")
        self.right_frame = AutoScrollableFrame(self.right_container, label_text="Daily Routine")
        self.right_frame.pack(fill=tk.BOTH, expand=True)

        self.library_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.library_filters_frame = ctk.CTkFrame(self.library_container)
        self.library_filters_frame.pack(fill=tk.X, pady=(0, 10))

        self.lib_search_var = tk.StringVar()
        self.lib_subj_var = tk.StringVar(value="All Subjects")
        self.lib_day_var = tk.StringVar(value="All Days")

        ctk.CTkEntry(self.library_filters_frame, textvariable=self.lib_search_var, placeholder_text="Search...").pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        self.lib_subj_combo = ctk.CTkComboBox(self.library_filters_frame, variable=self.lib_subj_var, values=["All Subjects"], command=lambda _: self.refresh_library())
        self.lib_subj_combo.pack(side=tk.LEFT, padx=5, pady=5)
        self.lib_day_combo = ctk.CTkComboBox(self.library_filters_frame, variable=self.lib_day_var, values=["All Days"], command=lambda _: self.refresh_library())
        self.lib_day_combo.pack(side=tk.LEFT, padx=5, pady=5)
        self.lib_search_var.trace_add("write", lambda *args: self.refresh_library())

        self.library_scroll_frame = AutoScrollableFrame(self.library_container, label_text="All Study Blocks")
        self.library_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.action_bar = ctk.CTkFrame(self.root, fg_color="#1E88E5", height=50)
        ctk.CTkLabel(self.action_bar, text="Bulk Actions:", text_color="white", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=15)
        self.action_count_lbl = ctk.CTkLabel(self.action_bar, text="0 selected", text_color="white")
        self.action_count_lbl.pack(side=tk.LEFT, padx=10)
        ctk.CTkButton(self.action_bar, text="Move to Day...", command=self.prompt_move_to_day, fg_color="#0D47A1", hover_color="#1565C0").pack(side=tk.RIGHT, padx=15, pady=10)

        self.refresh_ui()

    def switch_view(self, choice):
        self.selected_task_ids.clear()
        self.update_selection_visuals()

        if choice == "Planner":
            self.library_container.pack_forget()
            self.planner_controls_frame.pack(side=tk.LEFT)
            self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.refresh_ui()
        else:
            self.main_pane.pack_forget()
            self.planner_controls_frame.pack_forget()
            self.library_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.refresh_library()

    def handle_task_click(self, event, task_data, widget):
        tid = task_data['id']
        state = event.state
        shift_pressed = state & 0x0001
        ctrl_pressed = state & 0x0004

        if shift_pressed and self.last_clicked_task_id:
            last_widget = self.task_frames.get(self.last_clicked_task_id)
            if last_widget and last_widget.master == widget.master:
                children = [c for c in widget.master.winfo_children() if isinstance(c, ctk.CTkFrame) and hasattr(c, 'task_id')]
                idx1 = next((i for i, c in enumerate(children) if c.task_id == self.last_clicked_task_id), -1)
                idx2 = next((i for i, c in enumerate(children) if c.task_id == tid), -1)
                if idx1 != -1 and idx2 != -1:
                    start, end = min(idx1, idx2), max(idx1, idx2)
                    for i in range(start, end + 1):
                        self.selected_task_ids.add(children[i].task_id)
            else:
                self.selected_task_ids.add(tid)
        elif ctrl_pressed:
            if tid in self.selected_task_ids:
                self.selected_task_ids.remove(tid)
            else:
                self.selected_task_ids.add(tid)
        else:
            self.selected_task_ids = {tid}

        self.last_clicked_task_id = tid
        self.update_selection_visuals()

    def update_selection_visuals(self):
        for tid, frame in self.task_frames.items():
            if tid in self.selected_task_ids:
                frame.configure(border_color="#00E5FF")
            else:
                frame.configure(border_color=getattr(frame, "original_border_color", "gray"))

        if len(self.selected_task_ids) > 0:
            self.action_count_lbl.configure(text=f"{len(self.selected_task_ids)} selected")
            self.action_bar.pack(side=tk.BOTTOM, fill=tk.X)
        else:
            self.action_bar.pack_forget()

    def prompt_move_to_day(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Move to Day")
        dialog.geometry("300x200")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Select Target Day:").pack(pady=(20, 5))
        combo_var = tk.StringVar(value=self.days[0] if self.days else "")
        ctk.CTkComboBox(dialog, variable=combo_var, values=self.days).pack(pady=10)

        def confirm():
            target_day = combo_var.get()
            if target_day:
                self.logic.move_tasks_to_day(self.selected_task_ids, target_day)
                self.selected_task_ids.clear()
                self.update_selection_visuals()
                if self.current_view.get() == "Planner":
                    self.refresh_ui()
                else:
                    self.refresh_library()
            dialog.destroy()

        ctk.CTkButton(dialog, text="Move", command=confirm).pack(pady=20)

    def toggle_autosave(self):
        if self.autosave_var.get():
            self.save_btn.configure(state="disabled", fg_color="gray")
            self.manual_save()
        else:
            self.save_btn.configure(state="normal", fg_color=self.default_btn_fg)

    def manual_save(self):
        self.logic.save_plan()
        if self.current_view.get() == "Planner":
            self.refresh_ui()
        else:
            self.update_timestamp_label()

    def _get_day_for_task(self, task_id):
        for day_key, tasks in self.logic.state.items():
            for t in tasks:
                if t["id"] == task_id:
                    return day_key
        return self.current_day

    def toggle_task(self, task_id, is_completed):
        if task_id in self.selected_task_ids:
            for tid in self.selected_task_ids:
                d_key = self._get_day_for_task(tid)
                self.logic.update_task(d_key, tid, completed=is_completed, auto_save=False)
                self._update_task_ui(tid, is_completed)
            if self.autosave_var.get():
                self.manual_save()
        else:
            d_key = self._get_day_for_task(task_id)
            self.logic.update_task(d_key, task_id, completed=is_completed, auto_save=self.autosave_var.get())
            self._update_task_ui(task_id, is_completed)
            if self.autosave_var.get():
                self.update_timestamp_label()

    def _update_task_ui(self, task_id, is_completed):
        if task_id in self.task_widgets:
            txt = self.task_widgets[task_id]
            txt.configure(state="normal")
            txt.tag_remove("completed", "1.0", tk.END)
            if is_completed:
                txt.tag_add("completed", "1.0", tk.END)
                txt.tag_config("completed", foreground="gray")
            txt.configure(state="disabled")

    def show_confirmation(self, title, message, on_confirm):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=message, font=("Arial", 14), wraplength=350).pack(pady=(30, 20), padx=20)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        def confirm():
            dialog.destroy()
            on_confirm()

        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy, fg_color="gray", width=100).pack(side=tk.LEFT, expand=True)
        ctk.CTkButton(btn_frame, text="Confirm", command=confirm, fg_color="#b71c1c", hover_color="#7f0000", width=100).pack(side=tk.RIGHT, expand=True)

    def check_file_changes(self):
        try:
            if os.path.exists(self.logic.config["active_plan"]):
                current_mtime = os.path.getmtime(self.logic.config["active_plan"])
                if current_mtime > self.logic.last_saved_mtime:
                    self.logic.load_data()
                    self.days = list(self.logic.state.keys())
                    if self.current_day not in self.days and self.days:
                        self.current_day = self.days[0]
                    self.day_var.set(self.current_day)
                    if hasattr(self, 'day_combo'):
                        self.day_combo.configure(values=self.days)
                    if self.current_view.get() == "Planner":
                        self.refresh_ui()
                    else:
                        self.refresh_library()
        except Exception:
            pass
        self.root.after(2000, self.check_file_changes)

    def change_day(self, choice):
        self.current_day = choice
        self.refresh_ui()

    def prev_day(self):
        if not self.days or not self.current_day:
            return
        idx = self.days.index(self.current_day)
        new_idx = (idx - 1) % len(self.days)
        self.current_day = self.days[new_idx]
        self.day_var.set(self.current_day)
        self.refresh_ui()

    def next_day(self):
        if not self.days or not self.current_day:
            return
        idx = self.days.index(self.current_day)
        new_idx = (idx + 1) % len(self.days)
        self.current_day = self.days[new_idx]
        self.day_var.set(self.current_day)
        self.refresh_ui()

    def open_data_folder(self):
        path = self.logic.config["data_dir"]
        if os.name == 'nt':
            os.startfile(path)
        else:
            subprocess.call(['open', path] if sys.platform == 'darwin' else ['xdg-open', path])

    def reset_current_day(self):
        if self.current_day:
            self.show_confirmation("Confirm Reset Day", f"Are you sure you want to reset {self.current_day}?\nThis will remove all assigned slots and completions.", self._do_reset_current_day)

    def _do_reset_current_day(self):
        self.logic.reset_day(self.current_day)
        self.refresh_ui()

    def reset_plan(self):
        self.show_confirmation("Confirm Reset Plan", "Are you sure you want to reset the entire plan? This will revert all progress to the original imported files.", self._do_reset_plan)

    def _do_reset_plan(self):
        self.logic.reset_plan()
        self.days = list(self.logic.state.keys())
        if self.current_view.get() == "Planner":
            self.refresh_ui()
        else:
            self.refresh_library()

    def major_deletion(self):
        self.show_confirmation("Confirm Major Deletion", "Are you sure you want to delete all internal data? This will remove the active and original files completely.", self._do_major_deletion)

    def _do_major_deletion(self):
        self.logic.major_deletion()
        self.setup_ui()

    def update_timestamp_label(self):
        if self.logic.last_saved_mtime > 0:
            dt = datetime.datetime.fromtimestamp(self.logic.last_saved_mtime)
            self.save_label.configure(text=f"Last saved: {dt.strftime('%H:%M:%S')}")

    def refresh_library(self):
        self.update_timestamp_label()
        for widget in self.library_scroll_frame.winfo_children():
            widget.destroy()

        self.task_widgets = {}
        self.task_frames = {}

        all_tasks = []
        subjects = set()
        for day_key, tasks in self.logic.state.items():
            for t in tasks:
                t['day_key'] = day_key
                all_tasks.append(t)
                if t.get('subject'):
                    subjects.add(t['subject'])

        subj_vals = ["All Subjects"] + sorted(list(subjects))
        if self.lib_subj_combo.cget("values") != subj_vals:
            self.lib_subj_combo.configure(values=subj_vals)

        day_vals = ["All Days"] + self.days
        if self.lib_day_combo.cget("values") != day_vals:
            self.lib_day_combo.configure(values=day_vals)

        search_q = self.lib_search_var.get().lower()
        filter_subj = self.lib_subj_var.get()
        filter_day = self.lib_day_var.get()

        for t in all_tasks:
            if search_q and search_q not in t['display_text'].lower() and search_q not in t.get('subject', '').lower():
                continue
            if filter_subj != "All Subjects" and t.get('subject') != filter_subj:
                continue
            if filter_day != "All Days" and t['day_key'] != filter_day:
                continue
            self._create_task_widget(self.library_scroll_frame, t, show_day_badge=True)

        self.update_selection_visuals()

    def refresh_ui(self):
        if not hasattr(self, 'left_frame'):
            return
        if not self.current_day:
            return

        self.update_timestamp_label()

        for widget in self.left_frame.winfo_children():
            widget.destroy()
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        self.task_widgets = {}
        self.task_frames = {}
        self.slot_frames = {}

        tasks = self.logic.state.get(self.current_day, [])
        unassigned_tasks = [t for t in tasks if not t.get("assigned_slot")]

        for t in unassigned_tasks:
            self._create_task_widget(self.left_frame, t)

        for slot in self.logic.routine_slots:
            slot_frame = ctk.CTkFrame(self.right_frame, fg_color=("gray85", "gray20"))
            slot_frame.pack(fill=tk.X, pady=5, padx=5)
            slot_id = slot["time"]
            slot_frame.slot_id = slot_id
            self.slot_frames[slot_id] = slot_frame

            header_text = f"{slot['time']} - {slot['desc']}" if slot.get("desc") else f"Time: {slot['time']}"
            ctk.CTkLabel(slot_frame, text=header_text, font=("Arial", 14, "bold"), wraplength=450, justify="left").pack(anchor=tk.W, padx=10, pady=5)

            assigned_tasks = [t for t in tasks if t.get("assigned_slot") == slot_id]
            if not assigned_tasks:
                ctk.CTkLabel(slot_frame, text="Drop study block here", text_color="gray").pack(pady=10)
            else:
                for t in assigned_tasks:
                    self._create_task_widget(slot_frame, t)

        self.update_selection_visuals()

    def _create_task_widget(self, parent, task, show_day_badge=False):
        border_col = ("gray70", "gray40")
        if task.get('subject'):
            subj = task['subject'].upper()
            if 'PV' in subj:
                border_col = ("#42A5F5", "#1976D2")
            elif 'DS' in subj:
                border_col = ("#66BB6A", "#388E3C")
            elif 'LIT' in subj:
                border_col = ("#AB47BC", "#8E24AA")
            elif 'ČJ' in subj or 'CJ' in subj:
                border_col = ("#FFA726", "#F57C00")
            else:
                border_col = get_deterministic_colors(task['subject'])

        frame = ctk.CTkFrame(parent, fg_color=("gray95", "gray22"), border_width=2, border_color=border_col)
        frame.pack(fill=tk.X, pady=5, padx=5)
        frame.original_border_color = border_col
        frame.task_id = task['id']

        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.pack(fill=tk.X, expand=True, padx=0, pady=0)

        var = tk.BooleanVar(value=task['completed'])
        chk = ctk.CTkCheckBox(top_row, text="", variable=var, width=24, command=lambda t=task['id'], v=var: self.toggle_task(t, v.get()))
        chk.pack(side=tk.LEFT, padx=(10, 5), pady=10)

        text_content = task.get('display_text', task['clean_text'])
        chars_per_line = 60
        estimated_lines = (len(text_content) // chars_per_line) + 1
        dynamic_height = max(35, estimated_lines * 22 + 10)

        txt = ctk.CTkTextbox(top_row, height=dynamic_height, wrap="word", fg_color="transparent", border_width=0, font=("Arial", 13))
        txt.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        parts = re.split(r'(\*\*.*?\*\*)', text_content)
        txt._textbox.tag_config("bold", font=("Arial", 13, "bold"))
        if task['completed']:
            txt.tag_config("completed", foreground="gray")

        for part in parts:
            if not part:
                continue
            if part.startswith("**") and part.endswith("**"):
                clean_part = part[2:-2]
                txt.insert(tk.END, clean_part, ("bold", "completed") if task['completed'] else "bold")
            else:
                txt.insert(tk.END, part, "completed" if task['completed'] else None)

        txt.configure(state="disabled")
        self.task_widgets[task['id']] = txt
        self.task_frames[task['id']] = frame

        badge_row = ctk.CTkFrame(frame, fg_color="transparent")
        badge_row_packed = False
        badge_labels = []

        if show_day_badge and task.get('day_key'):
            lbl = ctk.CTkLabel(badge_row, text=task['day_key'], fg_color=("gray80", "gray40"), text_color=("black", "white"), corner_radius=6, height=22, padx=8, font=("Arial", 11))
            lbl.pack(side=tk.RIGHT, padx=(6, 5))
            badge_labels.append(lbl)
            badge_row_packed = True

        if task.get('badges'):
            for badge in task['badges']:
                b_lower = badge.lower()
                if "hard" in b_lower:
                    b_color = ("#FFCDD2", "#C62828")
                elif "medium" in b_lower:
                    b_color = ("#FFE0B2", "#E65100")
                elif "easy" in b_lower:
                    b_color = ("#C8E6C9", "#1B5E20")
                elif "h" in b_lower or "hod" in b_lower:
                    b_color = ("#B3E5FC", "#01579B")
                elif "iterac" in b_lower:
                    b_color = ("#D1C4E9", "#311B92")
                else:
                    b_color = get_deterministic_colors(badge)

                lbl = ctk.CTkLabel(badge_row, text=badge, fg_color=b_color, text_color=("black", "white"), corner_radius=6, height=22, padx=8, font=("Arial", 11, "bold"))
                lbl.pack(side=tk.LEFT, padx=(0, 6))
                badge_labels.append(lbl)
                badge_row_packed = True

        if badge_row_packed:
            badge_row.pack(fill=tk.X, padx=(38, 5), pady=(0, 10))

        self.drag_manager.make_draggable(frame, frame, task)
        self.drag_manager.make_draggable(txt, frame, task)
        self.drag_manager.make_draggable(top_row, frame, task)
        if badge_row_packed:
            self.drag_manager.make_draggable(badge_row, frame, task)
            for b_lbl in badge_labels:
                self.drag_manager.make_draggable(b_lbl, frame, task)
