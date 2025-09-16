import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from core.db import db_connect
from core.helpers import today_str

class ExerciseTab:
    def __init__(self, tab_view, main_app):
        self.tab_view = tab_view
        self.main_app = main_app
        self.frame = ctk.CTkFrame(self.tab_view)
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)
        self._build_ui()
        
    def _build_ui(self):
        outer = self.frame
        
        top = ctk.CTkFrame(outer)
        top.pack(fill="x", pady=8)

        self.ex_date = ctk.CTkEntry(top, placeholder_text="YYYY-MM-DD")
        self.ex_date.insert(0, today_str())
        self.ex_date.pack(side="left", padx=6)

        self.ex_name = ctk.CTkEntry(top, placeholder_text="Exercise name")
        self.ex_name.pack(side="left", padx=6, fill="x", expand=True)

        self.ex_kcal = ctk.CTkEntry(top, placeholder_text="Calories burned")
        self.ex_kcal.pack(side="left", padx=6)

        ctk.CTkButton(top, text="Add", command=self.add_exercise).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Reset Day", fg_color="#c0392b", command=self.reset_ex_day).pack(side="left", padx=6)

        mid = ctk.CTkFrame(outer)
        mid.pack(fill="both", expand=True, pady=8)

        self.ex_listbox = tk.Listbox(mid, height=14)
        self.ex_listbox.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        sb = tk.Scrollbar(mid, command=self.ex_listbox.yview)
        sb.pack(side="left", fill="y")
        self.ex_listbox.config(yscrollcommand=sb.set)

        right = ctk.CTkFrame(outer)
        right.pack(fill="x", padx=6, pady=8)

        self.lbl_ex_summary = ctk.CTkLabel(right, text="Daily exercise summary will appear here.")
        self.lbl_ex_summary.pack(anchor="w")
        
    def add_exercise(self):
        if not getattr(self.main_app, "current_user_id", None):
            messagebox.showerror("No Profile", "Please create/select a profile first.")
            return

        d = (self.ex_date.get() or today_str()).strip()
        try:
            datetime.fromisoformat(d)
        except ValueError:
            messagebox.showerror("Date", "Please enter date as YYYY-MM-DD")
            return

        name = self.ex_name.get().strip()
        if not name:
            messagebox.showerror("Exercise", "Please enter an exercise name.")
            return

        try:
            kcal = float(self.ex_kcal.get())
        except (ValueError, TypeError):
            messagebox.showerror("Calories", "Please enter a valid number for calories burned.")
            return

        conn = db_connect()
        with conn:
            conn.execute(
                "INSERT INTO exercises(user_id, log_date, name, calories_burned) VALUES(?,?,?,?)",
                (self.main_app.current_user_id, d, name, kcal)
            )

        self.ex_name.delete(0, "end")
        self.ex_kcal.delete(0, "end")
        self.refresh_exercise_list()

    def reset_ex_day(self):
        if not getattr(self.main_app, "current_user_id", None):
            return
        d = (self.ex_date.get() or today_str()).strip()
        if messagebox.askyesno("Reset Exercises", f"Clear all exercises for {d}?"):
            conn = db_connect()
            with conn:
                conn.execute(
                    "DELETE FROM exercises WHERE user_id=? AND log_date=?",
                    (self.main_app.current_user_id, d)
                )
            self.refresh_exercise_list()

    def refresh_exercise_list(self):
        self.ex_listbox.delete(0, "end")
        if not getattr(self.main_app, "current_user_id", None):
            return

        d = (self.ex_date.get() or today_str()).strip()
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT name, calories_burned FROM exercises WHERE user_id=? AND log_date=? ORDER BY id DESC",
            (self.main_app.current_user_id, d)
        )
        rows = cur.fetchall()
        conn.close()

        total_burn = 0
        for n, cals in rows:
            self.ex_listbox.insert("end", f"{n} — {cals:.0f} kcal")
            total_burn += cals

        target = getattr(self.main_app, "current_target", 2000)
        foods_total = self._foods_total_for_date(d)
        net = foods_total - total_burn
        remaining = target - net

        self.lbl_ex_summary.configure(
            text=f"Burned: {total_burn:.0f} kcal • Food: {foods_total:.0f} kcal • Net: {net:.0f} kcal • Remaining vs Target: {remaining:.0f} kcal"
        )

    def _foods_total_for_date(self, d):
        if not getattr(self.main_app, "current_user_id", None):
            return 0
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT SUM(calories) FROM foods WHERE user_id=? AND log_date=?",
            (self.main_app.current_user_id, d)
        )
        s = cur.fetchone()[0]
        conn.close()
        return float(s or 0)
