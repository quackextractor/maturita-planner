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
    Generates a consistent, aesthetically pleasing background and border color
    pair based on the string provided.
    """
    # Create a stable hash of the text
    hash_obj = hashlib.md5(text.lower().strip().encode('utf-8'))
    hash_int = int(hash_obj.hexdigest(), 16)

    # Use the hash to pick a hue (0.0 to 1.0)
    hue = (hash_int % 360) / 360.0

    # Generate a light color for Light Mode and a dark color for Dark Mode
    # HLS: Hue, Lightness, Saturation
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

    def make_draggable(self, handle, widget_to_move, task_data):
        def _on_start(e):
            self.on_drag_start(e, widget_to_move, task_data)
            return "break"

        def _on_motion(e):
            self.on_drag_motion(e)
            return "break"

        def _on_release(e):
            self.on_drag_release(e)
            return "break"

        handle.bind("<ButtonPress-1>", _on_start)
        handle.bind("<B1-Motion>", _on_motion)
        handle.bind("<ButtonRelease-1>", _on_release)

        if isinstance(handle, ctk.CTkTextbox):
            handle._textbox.bind("<ButtonPress-1>", _on_start)
            handle._textbox.bind("<B1-Motion>", _on_motion)
            handle._textbox.bind("<ButtonRelease-1>", _on_release)

    def on_drag_start(self, event, widget, task_data):
        self.drag_data = task_data
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

        display_str = task_data.get('display_text', task_data['clean_text'])
        proxy_label = ctk.CTkLabel(
            self.dragged_widget,
            text=display_str[:120] + "..." if len(display_str) > 120 else display_str,
            wraplength=w - 20,
            font=("Arial", 12)
        )
        proxy_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        widget.pack_forget()
        self.original_widget = widget

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

        old_parent = self.original_widget.master if hasattr(self, 'original_widget') and self.original_widget else None

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

        if slot_id:
            self.app.logic.update_task(self.app.current_day, self.drag_data["id"], assigned_slot=slot_id, auto_save=self.app.autosave_var.get())
        else:
            self.app.logic.update_task(self.app.current_day, self.drag_data["id"], assigned_slot=None, auto_save=self.app.autosave_var.get())

        if self.app.autosave_var.get():
            self.app.update_timestamp_label()

        self.app.root.configure(cursor="")

        new_parent = self.app.left_frame
        if slot_id:
            new_parent = self.app.slot_frames.get(slot_id)

        if hasattr(self, 'original_widget') and self.original_widget and self.original_widget.winfo_exists():
            self.original_widget.destroy()
            self.original_widget = None

        if new_parent:
            if slot_id:
                for child in new_parent.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and child.cget("text") == "Drop study block here":
                        child.destroy()

            self.drag_data["assigned_slot"] = slot_id
            self.app._create_task_widget(new_parent, self.drag_data)

            if old_parent and hasattr(old_parent, "slot_id") and old_parent != new_parent:
                remaining_tasks = [c for c in old_parent.winfo_children() if isinstance(c, ctk.CTkFrame)]
                if not remaining_tasks:
                    ctk.CTkLabel(old_parent, text="Drop study block here", text_color="gray").pack(pady=10)

        self.dragged_widget = None
        self.original_widget = None


class PlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Maturita Planner")
        self.root.geometry("1100x700")

        self.logic = PlannerLogic(DEFAULT_CONFIG)
        self.drag_manager = DragManager(self)
        self.task_widgets = {}
        self.slot_frames = {}

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
        self.days = list(self.logic.plan_data.keys())
        self.current_day = self.days[0] if self.days else None

        self.top_frame = ctk.CTkFrame(self.root, height=50)
        self.top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.day_var = tk.StringVar(value=self.current_day)

        ctk.CTkButton(self.top_frame, text="<", width=30, command=self.prev_day).pack(side=tk.LEFT, padx=(10, 2))
        self.day_combo = ctk.CTkComboBox(self.top_frame, variable=self.day_var, values=self.days, command=self.change_day)
        self.day_combo.pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(self.top_frame, text=">", width=30, command=self.next_day).pack(side=tk.LEFT, padx=(2, 10))

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
        ctk.CTkButton(self.top_frame, text="Open Data Folder", command=self.open_data_folder, fg_color="gray30", hover_color="gray40").pack(side=tk.RIGHT, padx=5)

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

        self.refresh_ui()

    def toggle_autosave(self):
        if self.autosave_var.get():
            self.save_btn.configure(state="disabled", fg_color="gray")
            self.manual_save()
        else:
            self.save_btn.configure(state="normal", fg_color=self.default_btn_fg)

    def manual_save(self):
        self.logic.save_plan()
        self.refresh_ui()

    def show_confirmation(self, title, message, on_confirm):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text=message, font=("Arial", 14), wraplength=350).pack(pady=(30, 20), padx=20)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        def confirm():
            dialog.destroy()
            on_confirm()

        def cancel():
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="Cancel", command=cancel, fg_color="gray", width=100).pack(side=tk.LEFT, expand=True)
        ctk.CTkButton(btn_frame, text="Confirm", command=confirm, fg_color="#b71c1c", hover_color="#7f0000", width=100).pack(side=tk.RIGHT, expand=True)

    def check_file_changes(self):
        try:
            if os.path.exists(self.logic.config["active_plan"]):
                current_mtime = os.path.getmtime(self.logic.config["active_plan"])
                if current_mtime > self.logic.last_saved_mtime:
                    self.logic.load_data()
                    self.days = list(self.logic.plan_data.keys())
                    if self.current_day not in self.days and self.days:
                        self.current_day = self.days[0]
                    self.day_var.set(self.current_day)
                    if hasattr(self, 'day_combo'):
                        self.day_combo.configure(values=self.days)
                    self.refresh_ui()
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
            self.show_confirmation(
                "Confirm Reset Day",
                f"Are you sure you want to reset {self.current_day}?\nThis will remove all assigned slots and completions.",
                self._do_reset_current_day
            )

    def _do_reset_current_day(self):
        self.logic.reset_day(self.current_day)
        self.refresh_ui()

    def reset_plan(self):
        self.show_confirmation(
            "Confirm Reset Plan",
            "Are you sure you want to reset the entire plan? This will revert all progress to the original imported files.",
            self._do_reset_plan
        )

    def _do_reset_plan(self):
        self.logic.reset_plan()
        self.days = list(self.logic.plan_data.keys())
        self.refresh_ui()

    def major_deletion(self):
        self.show_confirmation(
            "Confirm Major Deletion",
            "Are you sure you want to delete all internal data? This will remove the active and original files completely.",
            self._do_major_deletion
        )

    def _do_major_deletion(self):
        self.logic.major_deletion()
        self.setup_ui()

    def toggle_task(self, task_id, is_completed):
        self.logic.update_task(self.current_day, task_id, completed=is_completed, auto_save=self.autosave_var.get())
        if self.autosave_var.get():
            self.update_timestamp_label()

        if task_id in self.task_widgets:
            txt = self.task_widgets[task_id]
            txt.configure(state="normal")
            txt.tag_remove("completed", "1.0", tk.END)

            if is_completed:
                txt.tag_add("completed", "1.0", tk.END)
                txt.tag_config("completed", foreground="gray")

            txt.configure(state="disabled")

    def update_timestamp_label(self):
        if self.logic.last_saved_mtime > 0:
            dt = datetime.datetime.fromtimestamp(self.logic.last_saved_mtime)
            self.save_label.configure(text=f"Last saved: {dt.strftime('%H:%M:%S')}")

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

    def _create_task_widget(self, parent, task):
        border_col = ("gray70", "gray40")
        if task.get('subject'):
            # Use deterministic generator for dynamic subjects
            border_col = get_deterministic_colors(task['subject'])

        frame = ctk.CTkFrame(parent, fg_color=("gray95", "gray22"), border_width=2, border_color=border_col)
        frame.pack(fill=tk.X, pady=5, padx=5)

        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.pack(fill=tk.X, expand=True, padx=0, pady=0)

        var = tk.BooleanVar(value=task['completed'])
        chk = ctk.CTkCheckBox(top_row, text="", variable=var, width=24, command=lambda t=task['id'], v=var: self.toggle_task(t, v.get()))
        chk.pack(side=tk.LEFT, padx=(10, 5), pady=10)

        text_content = task.get('display_text', task['clean_text'])
        chars_per_line = 60
        estimated_lines = (len(text_content) // chars_per_line) + 1
        dynamic_height = max(35, estimated_lines * 22 + 10)

        txt = ctk.CTkTextbox(
            top_row,
            height=dynamic_height,
            wrap="word",
            fg_color="transparent",
            border_width=0,
            font=("Arial", 13)
        )
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

        badge_labels = []
        badge_row = None
        if task.get('badges'):
            badge_row = ctk.CTkFrame(frame, fg_color="transparent")
            badge_row.pack(fill=tk.X, padx=(38, 5), pady=(0, 10))
            for badge in task['badges']:
                # Generate a completely generic color based on the badge text itself
                b_color = get_deterministic_colors(badge)
                text_col = ("black", "white")

                lbl = ctk.CTkLabel(badge_row, text=badge, fg_color=b_color, text_color=text_col, corner_radius=6, height=22, padx=8, font=("Arial", 11, "bold"))
                lbl.pack(side=tk.LEFT, padx=(0, 6))
                badge_labels.append(lbl)

        self.drag_manager.make_draggable(frame, frame, task)
        self.drag_manager.make_draggable(txt, frame, task)
        self.drag_manager.make_draggable(top_row, frame, task)

        if badge_row:
            self.drag_manager.make_draggable(badge_row, frame, task)
            for b_lbl in badge_labels:
                self.drag_manager.make_draggable(b_lbl, frame, task)
