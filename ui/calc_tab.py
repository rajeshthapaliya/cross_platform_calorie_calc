import customtkinter as ctk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from core.helpers import calc_bmr, calc_tdee, apply_goal, ACTIVITY_FACTORS

class CalcTab:
    def __init__(self, tab_view, main_app):
        self.tab_view = tab_view
        self.main_app = main_app
        self.frame = ctk.CTkFrame(self.tab_view)
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)
        self.chart_canvas = None
        self._build_ui()

    def _build_ui(self):
        left = ctk.CTkFrame(self.frame)
        left.pack(side="left", fill="y", padx=12, pady=12)

        self.calc_gender = ctk.CTkComboBox(left, values=["Male", "Female"])
        self.calc_gender.set("Male")
        self.calc_gender.pack(pady=8, fill="x")

        self.calc_weight = ctk.CTkEntry(left, placeholder_text="Weight (kg)")
        self.calc_weight.pack(pady=8, fill="x")

        self.calc_height = ctk.CTkEntry(left, placeholder_text="Height (cm)")
        self.calc_height.pack(pady=8, fill="x")

        self.calc_age = ctk.CTkEntry(left, placeholder_text="Age (years)")
        self.calc_age.pack(pady=8, fill="x")

        self.calc_activity = ctk.CTkComboBox(left, values=list(ACTIVITY_FACTORS.keys()))
        self.calc_activity.set("Moderate")
        self.calc_activity.pack(pady=8, fill="x")

        self.calc_goal = ctk.CTkComboBox(left, values=["Lose", "Maintain", "Gain"])
        self.calc_goal.set("Maintain")
        self.calc_goal.pack(pady=8, fill="x")

        ctk.CTkButton(left, text="Use Profile Values", command=self.fill_from_profile).pack(pady=10, fill="x")
        ctk.CTkButton(left, text="Calculate", command=self.calculate_now).pack(pady=6, fill="x")

        right = ctk.CTkFrame(self.frame)
        right.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        self.lbl_summary = ctk.CTkLabel(right, text="Enter values and click Calculate.", justify="left")
        self.lbl_summary.pack(pady=8, anchor="w")

        self.chart_area = ctk.CTkFrame(right)
        self.chart_area.pack(fill="both", expand=True, pady=8)

    def fill_from_profile(self):
        if not self.main_app.current_user:
            return
        u = self.main_app.current_user
        self.calc_gender.set(u.get("gender", "Male"))
        self.calc_weight.delete(0, "end"); self.calc_weight.insert(0, str(u.get("weight", 70)))
        self.calc_height.delete(0, "end"); self.calc_height.insert(0, str(u.get("height", 170)))
        self.calc_age.delete(0, "end"); self.calc_age.insert(0, str(u.get("age", 25)))
        self.calc_activity.set(u.get("activity", "Moderate"))
        self.calc_goal.set(u.get("goal", "Maintain"))
        self.calculate_now()

    def calculate_now(self):
        try:
            gender = self.calc_gender.get()
            weight = float(self.calc_weight.get() or 70)
            height = float(self.calc_height.get() or 170)
            age = int(self.calc_age.get() or 25)
            activity = self.calc_activity.get() or "Moderate"
            goal = self.calc_goal.get() or "Maintain"
        except ValueError:
            messagebox.showerror("Invalid", "Please enter valid numeric values.")
            return

        bmr = calc_bmr(gender, weight, height, age)
        tdee = calc_tdee(bmr, activity)
        target = apply_goal(tdee, goal)

        macro = (self.main_app.current_user or {}).get("macro", {"protein": 30, "carb": 45, "fat": 25})
        p_pct, c_pct, f_pct = macro["protein"], macro["carb"], macro["fat"]
        p_g = target * p_pct / 100 / 4
        c_g = target * c_pct / 100 / 4
        f_g = target * f_pct / 100 / 9

        bmi = weight / ((height / 100) ** 2)
        if bmi < 18.5:
            bmi_cat = "Underweight"
        elif bmi < 25:
            bmi_cat = "Normal"
        elif bmi < 30:
            bmi_cat = "Overweight"
        else:
            bmi_cat = "Obese"

        self.lbl_summary.configure(text=(
            f"BMR: {bmr:.0f} kcal/day\n"
            f"TDEE: {tdee:.0f} kcal/day\n"
            f"Target (goal: {goal}): {target:.0f} kcal/day\n"
            f"BMI: {bmi:.1f} ({bmi_cat})\n\n"
            f"Macros — Protein: {p_g:.0f} g, Carbs: {c_g:.0f} g, Fat: {f_g:.0f} g"
        ))

        # Clear previous chart
        for w in self.chart_area.winfo_children():
            w.destroy()
        plt.close("all")  # Close any previous figures to prevent Mac memory leak

        fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        ax.pie([p_pct, c_pct, f_pct], labels=[f"Protein {p_pct}%", f"Carbs {c_pct}%", f"Fat {f_pct}%"],
               autopct="%1.0f%%", startangle=90)
        ax.set_title("Macro Split")

        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(pady=4)

        self.main_app.current_target = target
