import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime
import os
import matplotlib.pyplot as plt

from core.db import db_connect
from core.helpers import today_str

class ExportTab:
    def __init__(self, tab_view, main_app):
        self.tab_view = tab_view
        self.main_app = main_app
        self.frame = ctk.CTkFrame(self.tab_view)
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)
        self._build_ui()

    def _build_ui(self):
        outer = self.frame

        ctk.CTkLabel(
            outer, 
            text="Export today's (or chosen day) logs to CSV. Also export charts as PNG."
        ).pack(anchor="w")

        row = ctk.CTkFrame(outer)
        row.pack(fill="x", pady=10)

        self.exp_date = ctk.CTkEntry(row, placeholder_text="YYYY-MM-DD")
        self.exp_date.insert(0, today_str())
        self.exp_date.pack(side="left", padx=6)

        ctk.CTkButton(row, text="Export Day to CSV", command=self.export_day_csv).pack(side="left", padx=6)
        ctk.CTkButton(row, text="Save Macro Pie as PNG", command=self.save_macro_png).pack(side="left", padx=6)
        ctk.CTkButton(row, text="Save Progress Chart as PNG", command=self.save_progress_png).pack(side="left", padx=6)

    def export_day_csv(self):
        if not getattr(self.main_app, "current_user_id", None):
            return

        d = (self.exp_date.get() or today_str()).strip()
        try:
            datetime.fromisoformat(d)
        except ValueError:
            messagebox.showerror("Date", "Please enter date as YYYY-MM-DD")
            return

        folder = filedialog.askdirectory(title="Choose export folder")
        if not folder:
            return

        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE id=?", (self.main_app.current_user_id,))
        uname_row = cur.fetchone()
        uname = uname_row[0] if uname_row else "user"

        cur.execute("SELECT name, calories FROM foods WHERE user_id=? AND log_date=?", 
                    (self.main_app.current_user_id, d))
        foods = cur.fetchall()

        cur.execute("SELECT name, calories_burned FROM exercises WHERE user_id=? AND log_date=?", 
                    (self.main_app.current_user_id, d))
        exs = cur.fetchall()
        conn.close()

        f_food = os.path.join(folder, f"{uname}_{d}_foods.csv")
        with open(f_food, "w", encoding="utf-8") as f:
            f.write("Food,Calories\n")
            for n, c in foods:
                f.write(f"{n},{c}\n")

        f_ex = os.path.join(folder, f"{uname}_{d}_exercises.csv")
        with open(f_ex, "w", encoding="utf-8") as f:
            f.write("Exercise,CaloriesBurned\n")
            for n, c in exs:
                f.write(f"{n},{c}\n")

        messagebox.showinfo("Exported", f"Saved:\n{f_food}\n{f_ex}")

    def save_macro_png(self):
        target = getattr(self.main_app, "current_target", None)
        if not target:
            messagebox.showerror("No Data", "Calculate your target first in Calculator tab.")
            return

        macro = getattr(self.main_app, "current_user", {}).get("macro", {"protein": 30, "carb": 45, "fat": 25})
        p, c, f = macro.get("protein", 30), macro.get("carb", 45), macro.get("fat", 25)

        fig, ax = plt.subplots(figsize=(4.2, 4.2))
        ax.pie([p, c, f], labels=[f"Protein {p}%", f"Carbs {c}%", f"Fat {f}%"], autopct="%1.0f%%", startangle=90)
        ax.set_title("Macro Split")

        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")], title="Save macro chart")
        if not path:
            plt.close(fig)
            return

        fig.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        messagebox.showinfo("Saved", f"Chart saved to {path}")

    def save_progress_png(self):
        if not getattr(self.main_app, "current_user_id", None):
            return

        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT log_date, weight_kg FROM weights WHERE user_id=? ORDER BY log_date", 
                    (self.main_app.current_user_id,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            messagebox.showerror("No Data", "Add some weight entries first.")
            return

        dates = [datetime.fromisoformat(r[0]) for r in rows]
        weights = [r[1] for r in rows]

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(dates, weights, marker="o")
        ax.set_title("Weight Progress")
        ax.set_xlabel("Date")
        ax.set_ylabel("Weight (kg)")
        fig.autofmt_xdate()

        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")], title="Save progress chart")
        if not path:
            plt.close(fig)
            return

        fig.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        messagebox.showinfo("Saved", f"Chart saved to {path}")
