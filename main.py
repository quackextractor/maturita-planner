#!/usr/bin/env python3
import os
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
from src.gui import PlannerApp


class TkinterDnDApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


if __name__ == '__main__':
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    root = TkinterDnDApp()
    app = PlannerApp(root)
    root.mainloop()
