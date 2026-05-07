import tkinter as tk
import customtkinter as ctk
import os
import re
import sys
import datetime
import subprocess
from tkinterdnd2 import DND_FILES
from src.config import DEFAULT_CONFIG
from src.planner import PlannerLogic


class AutoScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use add="+" to avoid overwriting CTk internal bindings which breaks scrollregions
        self._parent_canvas.bind("<Configure>", self._on_canvas_configure, add="+")
        self._parent_frame.bind("<Configure>", lambda e: self.check_scrollbar(), add="+")

    def _on_canvas_configure(self, event):
        # Force the internal frame to always match the canvas width to prevent squishing
        self._parent_canvas.itemconfig(self._parent_canvas_window, width=event.width)
        self.check_scrollbar()

    def check_scrollbar(self, event=None):
        def _check():
            try:
                if self._parent_frame.winfo_reqheight() <= self._parent_canvas.winfo_height():
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

        # Explicitly bind the internal tkinter Text widget if it's a CTkTextbox
        # This absolutely prevents the native text selection highlighting
        if isinstance(handle, ctk.CTkTextbox):
            handle._textbox.bind("<ButtonPress-1>", _on_start)
            handle._textbox.bind("<B1-Motion>", _on_motion)
            handle._textbox.bind("<ButtonRelease-1>", _on_release)

    def on_drag_start(self, event, widget, task_data):
        self.drag_data = task_data

        # Calculate cursor offset relative to the widget's screen position
        self.offset_x = event.x_root - widget.winfo_rootx()
        self.offset_y = event.y_root - widget.winfo_rooty()

        # Create a floating proxy widget on root to avoid clipping by parent frames
        # We copy the original size to keep the layout feeling consistent
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

        # Add a simplified label to the proxy for visual feedback
        # This is a robust way to "float" content over any other UI element
        proxy_label = ctk.CTkLabel(
            self.dragged_widget,
            text=task_data['clean_text'][:120] + "..." if len(task_data['clean_text']) > 120 else task_data['clean_text'],
            wraplength=w - 20,
            font=("Arial", 12)
        )
        proxy_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Hide the original widget during drag
        widget.pack_forget()
        self.original_widget = widget

        # Initial Global Positioning
        self.update_drag_position(event)

        self.dragged_widget.lift()
        self.app.root.configure(cursor="hand2")

    def on_drag_motion(self, event):
        if not self.dragged_widget:
            return
        self.update_drag_position(event)

    def update_drag_position(self, event):
        # Coordinates relative to root window
        x = event.x_root - self.app.root.winfo_rootx() - self.offset_x
        y = event.y_root - self.app.root.winfo_rooty() - self.offset_y
        self.dragged_widget.place(x=x, y=y)

    def on_drag_release(self, event):
        if not self.dragged_widget:
            return

        # Determine the old parent before destroying the dragged widget
        old_parent = self.original_widget.master if hasattr(self, 'original_widget') and self.original_widget else None

        # Destroy the proxy widget FIRST so it doesn't block the hit test under cursor
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

        # Save to backend
        if slot_id:
            self.app.logic.update_task(self.app.current_day, self.drag_data["id"], assigned_slot=slot_id)
        else:
            self.app.logic.update_task(self.app.current_day, self.drag_data["id"], assigned_slot=None)

        self.app.root.configure(cursor="")

        # Determine the new parent
        new_parent = self.app.left_frame
        if slot_id:
            new_parent = self.app.slot_frames.get(slot_id)

        # Destroy original widget
        if hasattr(self, 'original_widget') and self.original_widget and self.original_widget.winfo_exists():
            self.original_widget.destroy()
            self.original_widget = None

        if new_parent:
            # Remove "Drop study block here" placeholder if moving into a slot
            if slot_id:
                for child in new_parent.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and child.cget("text") == "Drop study block here":
                        child.destroy()

            # Update the task data state and recreate the widget cleanly
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
            self.logic.reset_day(self.current_day)
            self.refresh_ui()

    def reset_plan(self):
        self.logic.reset_plan()
        self.days = list(self.logic.plan_data.keys())
        self.refresh_ui()

    def major_deletion(self):
        self.logic.major_deletion()
        self.setup_ui()

    def toggle_task(self, task_id, is_completed):
        self.logic.update_task(self.current_day, task_id, completed=is_completed)

        if task_id in self.task_widgets:
            txt = self.task_widgets[task_id]
            txt.configure(state="normal")

            # Clear existing tags
            txt.tag_remove("completed", "1.0", tk.END)

            if is_completed:
                txt.tag_add("completed", "1.0", tk.END)
                txt.tag_config("completed", foreground="gray")

            txt.configure(state="disabled")

    def refresh_ui(self):
        if not hasattr(self, 'left_frame'):
            return
        if not self.current_day:
            return

        if self.logic.last_saved_mtime > 0:
            dt = datetime.datetime.fromtimestamp(self.logic.last_saved_mtime)
            self.save_label.configure(text=f"Last saved: {dt.strftime('%H:%M:%S')}")

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
            slot_frame.slot_id = slot
            self.slot_frames[slot] = slot_frame

            ctk.CTkLabel(slot_frame, text=f"Time: {slot}", font=("Arial", 14, "bold")).pack(anchor=tk.W, padx=10, pady=5)

            assigned_tasks = [t for t in tasks if t.get("assigned_slot") == slot]
            if not assigned_tasks:
                ctk.CTkLabel(slot_frame, text="Drop study block here", text_color="gray").pack(pady=10)
            else:
                for t in assigned_tasks:
                    self._create_task_widget(slot_frame, t)

    def _create_task_widget(self, parent, task):
        frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray25"), border_width=1)
        frame.pack(fill=tk.X, pady=5, padx=5)

        var = tk.BooleanVar(value=task['completed'])
        chk = ctk.CTkCheckBox(frame, text="", variable=var, width=24, command=lambda t=task['id'], v=var: self.toggle_task(t, v.get()))
        chk.pack(side=tk.LEFT, padx=(10, 5), pady=10)

        text_content = task['clean_text']
        chars_per_line = 50
        estimated_lines = (len(text_content) // chars_per_line) + 1
        dynamic_height = max(35, estimated_lines * 20 + 10)

        txt = ctk.CTkTextbox(
            frame,
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

        self.drag_manager.make_draggable(frame, frame, task)
        self.drag_manager.make_draggable(txt, frame, task)
