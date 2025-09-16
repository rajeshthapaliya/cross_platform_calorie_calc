import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from core.db import db_connect
from core.helpers import today_str

class FoodTab:
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

        self.food_date = ctk.CTkEntry(top, placeholder_text="YYYY-MM-DD")
        self.food_date.insert(0, today_str())
        self.food_date.pack(side="left", padx=6)

        self.food_name = ctk.CTkEntry(top, placeholder_text="Food name")
        self.food_name.pack(side="left", padx=6, fill="x", expand=True)

        self.food_kcal = ctk.CTkEntry(top, placeholder_text="Calories (kcal)")
        self.food_kcal.pack(side="left", padx=6)

        ctk.CTkButton(top, text="Add", command=self.add_food).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Reset Day", fg_color="#c0392b", command=self.reset_food_day).pack(side="left", padx=6)

        mid = ctk.CTkFrame(outer)
        mid.pack(fill="both", expand=True, pady=8)

        self.food_listbox = tk.Listbox(mid, height=14)
        self.food_listbox.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        sb = tk.Scrollbar(mid, command=self.food_listbox.yview)
        sb.pack(side="left", fill="y")
        self.food_listbox.config(yscrollcommand=sb.set)

        right = ctk.CTkFrame(outer)
        right.pack(fill="x", padx=6, pady=8)

        self.lbl_food_summary = ctk.CTkLabel(right, text="Daily summary will appear here.")
        self.lbl_food_summary.pack(anchor="w")
        
    def add_food(self):
        user_id = getattr(self.main_app, "current_user_id", None)
        if not user_id:
            messagebox.showerror("No Profile", "Please create/select a profile first.")
            return

        d = (self.food_date.get() or today_str()).strip()
        try:
            datetime.fromisoformat(d)
        except ValueError:
            messagebox.showerror("Date", "Please enter date as YYYY-MM-DD")
            return

        name = self.food_name.get().strip()
        if not name:
            messagebox.showerror("Food", "Please enter a food name.")
            return

        try:
            kcal = float(self.food_kcal.get())
        except ValueError:
            messagebox.showerror("Calories", "Please enter a valid number for calories.")
            return

        with db_connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO foods(user_id, log_date, name, calories) VALUES(?,?,?,?)", 
                (user_id, d, name, kcal)
            )
            conn.commit()

        self.food_name.delete(0, "end")
        self.food_kcal.delete(0, "end")
        self.refresh_food_list()

    def reset_food_day(self):
        user_id = getattr(self.main_app, "current_user_id", None)
        if not user_id:
            return

        d = (self.food_date.get() or today_str()).strip()
        if messagebox.askyesno("Reset Day", f"Clear all foods for {d}?"):
            with db_connect() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM foods WHERE user_id=? AND log_date=?", (user_id, d))
                conn.commit()
            self.refresh_food_list()

    def refresh_food_list(self):
        self.food_listbox.delete(0, "end")
        user_id = getattr(self.main_app, "current_user_id", None)
        if not user_id:
            return

        d = (self.food_date.get() or today_str()).strip()
        with db_connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT name, calories FROM foods WHERE user_id=? AND log_date=? ORDER BY id DESC", 
                (user_id, d)
            )
            rows = cur.fetchall()

        total = sum(c for n, c in rows)
        for n, cals in rows:
            self.food_listbox.insert("end", f"{n} — {cals:.0f} kcal")

        target = getattr(self.main_app, "current_target", 2000)
        remaining = target - total
        self.lbl_food_summary.configure(
            text=f"Target: {target:.0f} kcal • Consumed: {total:.0f} kcal • Remaining: {remaining:.0f} kcal"
        )
