import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import sqlite3
import matplotlib
import os

matplotlib.use("TkAgg")  # required for charts

# Import all tab classes
from ui.profile_tab import ProfileTab
from ui.calc_tab import CalcTab
from ui.food_tab import FoodTab
from ui.exercise_tab import ExerciseTab
from ui.meal_tab import MealTab
from ui.progress_tab import ProgressTab
from ui.export_tab import ExportTab

# Import from core
from core.db import db_connect
from core.helpers import today_str

APP_TITLE = "Calorie Calculator Pro — Advanced"

class CalorieProApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x720")
        self.minsize(980, 720)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.current_user_id = None
        self.current_user = None
        self.current_target = 2000

        # Tabs
        self.profile_tab = None
        self.calc_tab = None
        self.food_tab = None
        self.ex_tab = None
        self.meal_tab = None
        self.prog_tab = None
        self.export_tab = None

        self._build_topbar()
        self._build_tabs()
        self.load_first_user_or_prompt()

    def _build_topbar(self):
        bar = ctk.CTkFrame(self)
        bar.pack(fill="x", padx=12, pady=(12, 0))

        self.user_select = ctk.CTkComboBox(bar, values=[], command=self.on_user_select)
        self.user_select.set("Select or create profile…")
        self.user_select.pack(side="left", padx=8, pady=10)

        add_btn = ctk.CTkButton(bar, text="＋ New Profile", command=self.create_profile_dialog)
        add_btn.pack(side="left", padx=8)

        self.mode_switch = ctk.CTkSwitch(bar, text="Light Mode", command=self.toggle_mode)
        self.mode_switch.pack(side="right", padx=8)

    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(self, width=940, height=620)
        self.tabs.pack(padx=20, pady=10, fill="both", expand=True)

        self.tab_profile = self.tabs.add("Profile")
        self.tab_calc = self.tabs.add("Calculator")
        self.tab_food = self.tabs.add("Food Logger")
        self.tab_ex = self.tabs.add("Exercise Logger")
        self.tab_meal = self.tabs.add("Meal Planner")
        self.tab_prog = self.tabs.add("Progress")
        self.tab_export = self.tabs.add("Export")

        self.profile_tab = ProfileTab(self.tab_profile, self)
        self.calc_tab = CalcTab(self.tab_calc, self)
        self.food_tab = FoodTab(self.tab_food, self)
        self.ex_tab = ExerciseTab(self.tab_ex, self)
        self.meal_tab = MealTab(self.tab_meal, self)
        self.prog_tab = ProgressTab(self.tab_prog, self)
        self.export_tab = ExportTab(self.tab_export, self)

    def toggle_mode(self):
        is_on = self.mode_switch.get()
        if is_on:
            ctk.set_appearance_mode("light")
            self.mode_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("dark")
            self.mode_switch.configure(text="Light Mode")

    def create_profile_dialog(self):
        d = ctk.CTkInputDialog(text="Enter new profile name:", title="New Profile")
        name = d.get_input()
        if not name:
            return
        name = name.strip()
        with db_connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO users(name) VALUES(?)", (name,))
                conn.commit()
            except sqlite3.IntegrityError:
                messagebox.showerror("Exists", "A profile with that name already exists.")
                return
        self.refresh_user_select()
        self.user_select.set(name)
        self.on_user_select(name)

    def refresh_user_select(self):
        with db_connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM users ORDER BY name COLLATE NOCASE")
            names = [r[0] for r in cur.fetchall()]
        self.user_select.configure(values=names if names else ["No profiles yet"])

    def on_user_select(self, name):
        with db_connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE name=?", (name,))
            row = cur.fetchone()
        if row:
            self.current_user_id = row[0]
            self.load_current_user()

    def load_current_user(self):
        user_id = getattr(self, "current_user_id", None)
        if not user_id:
            return
        with db_connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT name, gender, age, height_cm, weight_kg, activity, goal, macro_json "
                "FROM users WHERE id=?", (user_id,)
            )
            r = cur.fetchone()
        if not r:
            return
        name, gender, age, height, weight, activity, goal, macro_json = r
        self.current_user = {
            "name": name,
            "gender": gender,
            "age": age,
            "height": height,
            "weight": weight,
            "activity": activity,
            "goal": goal,
            "macro": json.loads(macro_json or '{"protein":30,"carb":45,"fat":25}')
        }

        # Update all tabs
        if getattr(self, "profile_tab", None):
            self.profile_tab.populate_from_user(self.current_user)
        if getattr(self, "calc_tab", None):
            self.calc_tab.calculate_now()
        if getattr(self, "food_tab", None):
            self.food_tab.refresh_food_list()
        if getattr(self, "ex_tab", None):
            self.ex_tab.refresh_exercise_list()
        if getattr(self, "prog_tab", None):
            self.prog_tab.refresh_progress_chart()

    def load_first_user_or_prompt(self):
        with db_connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM users ORDER BY id LIMIT 1")
            r = cur.fetchone()
        self.refresh_user_select()
        if r:
            self.user_select.set(r[0])
            self.on_user_select(r[0])
