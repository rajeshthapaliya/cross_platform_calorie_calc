import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.db import db_connect
from core.helpers import today_str

class ProgressTab:
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

        self.w_date = ctk.CTkEntry(top, placeholder_text="YYYY-MM-DD")
        self.w_date.insert(0, today_str())
        self.w_date.pack(side="left", padx=6)

        self.w_weight = ctk.CTkEntry(top, placeholder_text="Weight (kg)")
        self.w_weight.pack(side="left", padx=6)

        ctk.CTkButton(top, text="Add Weight", command=self.add_weight).pack(side="left", padx=6)

        self.prog_chart = ctk.CTkFrame(outer)
        self.prog_chart.pack(fill="both", expand=True, pady=8)

    def add_weight(self):
        if not getattr(self.main_app, "current_user_id", None):
            messagebox.showerror("No Profile", "Please select or create a profile first.")
            return
        d = (self.w_date.get() or today_str()).strip()
        try:
            datetime.fromisoformat(d)
            w = float(self.w_weight.get())
        except Exception:
            messagebox.showerror("Invalid", "Please enter valid date (YYYY-MM-DD) and weight.")
            return
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO weights(user_id, log_date, weight_kg) VALUES(?,?,?)",
            (self.main_app.current_user_id, d, w)
        )
        conn.commit()
        conn.close()
        self.w_weight.delete(0, "end")
        self.refresh_progress_chart()

    def refresh_progress_chart(self):
        for w in self.prog_chart.winfo_children():
            w.destroy()

        if not getattr(self.main_app, "current_user_id", None):
            return

        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT log_date, weight_kg FROM weights WHERE user_id=? ORDER BY log_date",
            (self.main_app.current_user_id,)
        )
        rows = cur.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(self.prog_chart, text="No weight data yet.", font=("Arial", 14)).pack(pady=20)
            return

        dates = [datetime.fromisoformat(r[0]) for r in rows]
        weights = [r[1] for r in rows]

        fig, ax = plt.subplots(figsize=(6.5, 3.8))
        ax.plot(dates, weights, marker="o")
        ax.set_title("Weight Progress", fontsize=14, fontname="Arial")
        ax.set_xlabel("Date", fontsize=12, fontname="Arial")
        ax.set_ylabel("Weight (kg)", fontsize=12, fontname="Arial")
        fig.autofmt_xdate()

        canvas = FigureCanvasTkAgg(fig, master=self.prog_chart)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=6, fill="both", expand=True)
