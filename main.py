#!/usr/bin/env python3
import os
import customtkinter as ctk
from src.gui import PlannerApp

if __name__ == '__main__':
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    app = PlannerApp(root)
    root.mainloop()
