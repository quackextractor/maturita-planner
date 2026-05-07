import tkinter as tk
import customtkinter as ctk
from src.config import DEFAULT_CONFIG
from src.planner import PlannerLogic


class DragManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.dragged_widget = None
        self.drag_data = None
        self.start_x = 0
        self.start_y = 0

    def make_draggable(self, widget, task_data):
        widget.bind("<ButtonPress-1>", lambda e: self.on_drag_start(e, widget, task_data))
        widget.bind("<B1-Motion>", self.on_drag_motion)
        widget.bind("<ButtonRelease-1>", self.on_drag_release)
        for child in widget.winfo_children():
            child.bind("<ButtonPress-1>", lambda e: self.on_drag_start(e, widget, task_data))
            child.bind("<B1-Motion>", self.on_drag_motion)
            child.bind("<ButtonRelease-1>", self.on_drag_release)

    def on_drag_start(self, event, widget, task_data):
        self.dragged_widget = widget
        self.drag_data = task_data
        self.start_x = event.x_root
        self.start_y = event.y_root
        widget.lift()

    def on_drag_motion(self, event):
        if not self.dragged_widget:
            return
        dx = event.x_root - self.start_x
        dy = event.y_root - self.start_y
        x = self.dragged_widget.winfo_x() + dx
        y = self.dragged_widget.winfo_y() + dy
        self.dragged_widget.place(x=x, y=y)
        self.start_x = event.x_root
        self.start_y = event.y_root

    def on_drag_release(self, event):
        if not self.dragged_widget:
            return

        x, y = event.x_root, event.y_root
        target = self.app.root.winfo_containing(x, y)

        slot_id = None
        if target:
            # Check if dropped in a routine slot frame
            current = target
            while current:
                if hasattr(current, "slot_id"):
                    slot_id = current.slot_id
                    break
                current = current.master

        if slot_id:
            self.app.logic.update_task(self.app.current_day, self.drag_data["id"], assigned_slot=slot_id)
        else:
            # Dropped outside, unassign
            self.app.logic.update_task(self.app.current_day, self.drag_data["id"], assigned_slot=None)

        self.dragged_widget.place_forget()
        self.dragged_widget = None
        self.app.refresh_ui()


class PlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Maturita Planner")
        self.root.geometry("1100x700")

        self.logic = PlannerLogic(DEFAULT_CONFIG)
        self.drag_manager = DragManager(self)

        self.days = list(self.logic.plan_data.keys())
        self.current_day = self.days[0] if self.days else None

        self.setup_ui()

    def setup_ui(self):
        # Top Bar
        self.top_frame = ctk.CTkFrame(self.root, height=50)
        self.top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.day_var = tk.StringVar(value=self.current_day)
        self.day_combo = ctk.CTkComboBox(self.top_frame, variable=self.day_var, values=self.days, command=self.change_day)
        self.day_combo.pack(side=tk.LEFT, padx=10, pady=10)

        ctk.CTkButton(self.top_frame, text="Reset Day", command=self.reset_current_day, fg_color="#b71c1c", hover_color="#7f0000").pack(side=tk.RIGHT, padx=10)

        # Main Layout
        self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bd=0, sashwidth=4)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: Unassigned Tasks Wrapper
        self.left_container = ctk.CTkFrame(self.main_pane, fg_color="transparent")
        self.main_pane.add(self.left_container)

        self.left_frame = ctk.CTkScrollableFrame(self.left_container, width=400, label_text="Unassigned Tasks")
        self.left_frame.pack(fill=tk.BOTH, expand=True)

        # Right: Daily Routine Wrapper
        self.right_container = ctk.CTkFrame(self.main_pane, fg_color="transparent")
        self.main_pane.add(self.right_container)

        self.right_frame = ctk.CTkScrollableFrame(self.right_container, width=600, label_text="Daily Routine")
        self.right_frame.pack(fill=tk.BOTH, expand=True)

        self.refresh_ui()

    def change_day(self, choice):
        self.current_day = choice
        self.refresh_ui()

    def reset_current_day(self):
        if self.current_day:
            self.logic.reset_day(self.current_day)
            self.refresh_ui()

    def toggle_task(self, task_id, is_completed):
        self.logic.update_task(self.current_day, task_id, completed=is_completed)
        self.refresh_ui()

    def refresh_ui(self):
        if not self.current_day:
            return

        # Clear existing widgets
        for widget in self.left_frame.winfo_children():
            widget.destroy()
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        tasks = self.logic.state.get(self.current_day, [])
        unassigned_tasks = [t for t in tasks if not t.get("assigned_slot")]

        # Render Unassigned
        for t in unassigned_tasks:
            self._create_task_widget(self.left_frame, t)

        # Render Routine Slots
        for slot in self.logic.routine_slots:
            slot_frame = ctk.CTkFrame(self.right_frame, fg_color=("gray85", "gray20"))
            slot_frame.pack(fill=tk.X, pady=5, padx=5)
            slot_frame.slot_id = slot  # Mark for drop target

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

        # Strip markdown syntax for display
        clean_text = task['original_text'].replace('*', '').strip()

        var = tk.BooleanVar(value=task['completed'])
        chk = ctk.CTkCheckBox(frame, text=clean_text, variable=var,
                              command=lambda t=task['id'], v=var: self.toggle_task(t, v.get()))
        chk.pack(anchor=tk.W, padx=10, pady=10)

        if task['completed']:
            chk.configure(text_color="gray")

        self.drag_manager.make_draggable(frame, task)
