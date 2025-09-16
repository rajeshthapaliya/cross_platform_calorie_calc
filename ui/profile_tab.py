import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json

from core.db import db_connect
from core.helpers import ACTIVITY_FACTORS

class ProfileTab:
    def __init__(self, tab_view, main_app):
        self.tab_view = tab_view
        self.main_app = main_app
        self.frame = ctk.CTkFrame(self.tab_view)
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)
        self._build_ui()

    def _build_ui(self):
        # Left: form
        lf = ctk.CTkFrame(self.frame)
        lf.pack(side="left", fill="y", padx=16, pady=16)

        self.entry_name = ctk.CTkEntry(lf, placeholder_text="Name")
        self.entry_name.pack(pady=8, fill="x")

        self.gender_box = ctk.CTkComboBox(lf, values=["Male", "Female"])
        self.gender_box.set("Male")
        self.gender_box.pack(pady=8, fill="x")

        self.spin_age = ctk.CTkEntry(lf, placeholder_text="Age (years)")
        self.spin_age.insert(0, "25")
        self.spin_age.pack(pady=8, fill="x")

        self.entry_height = ctk.CTkEntry(lf, placeholder_text="Height (cm)")
        self.entry_height.insert(0, "170")
        self.entry_height.pack(pady=8, fill="x")

        self.entry_weight = ctk.CTkEntry(lf, placeholder_text="Weight (kg)")
        self.entry_weight.insert(0, "70")
        self.entry_weight.pack(pady=8, fill="x")

        self.activity_box = ctk.CTkComboBox(lf, values=list(ACTIVITY_FACTORS.keys()))
        self.activity_box.set("Moderate")
        self.activity_box.pack(pady=8, fill="x")

        self.goal_box = ctk.CTkComboBox(lf, values=["Lose", "Maintain", "Gain"])
        self.goal_box.set("Maintain")
        self.goal_box.pack(pady=8, fill="x")

        save_btn = ctk.CTkButton(lf, text="Save/Update Profile", command=self.save_profile)
        save_btn.pack(pady=12, fill="x")

        # Right: Macro sliders
        rf = ctk.CTkFrame(self.frame)
        rf.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(rf, text="Macro Split (%)", font=("Arial", 18, "bold")).pack(pady=6)

        self.s_pro = ctk.CTkSlider(rf, from_=10, to=50, number_of_steps=40, command=self._on_macro_change)
        self.s_carb = ctk.CTkSlider(rf, from_=20, to=70, number_of_steps=50, command=self._on_macro_change)
        self.s_fat = ctk.CTkSlider(rf, from_=10, to=40, number_of_steps=30, command=self._on_macro_change)
        for s in (self.s_pro, self.s_carb, self.s_fat):
            s.set(30 if s is self.s_pro else 45 if s is self.s_carb else 25)
            s.pack(pady=16, fill="x")

        self.macro_label = ctk.CTkLabel(rf, text="Protein 30% • Carbs 45% • Fat 25% (must total 100%)")
        self.macro_label.pack(pady=6)

        self.macro_warn = ctk.CTkLabel(rf, text="", text_color="orange")
        self.macro_warn.pack(pady=4)

    def _on_macro_change(self, *_):
        p = round(self.s_pro.get())
        c = round(self.s_carb.get())
        f = round(self.s_fat.get())
        total = p + c + f
        self.macro_label.configure(text=f"Protein {p}% • Carbs {c}% • Fat {f}% (total {total}%)")
        self.macro_warn.configure(text="" if total == 100 else "⚠️ Macros must total 100% for accurate planning.")

    def save_profile(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showerror("Required", "Please enter a profile name.")
            return
        try:
            age = int(self.spin_age.get())
            height = float(self.entry_height.get())
            weight = float(self.entry_weight.get())
        except ValueError:
            messagebox.showerror("Invalid", "Please enter valid numeric values for age/height/weight.")
            return
        gender = self.gender_box.get()
        activity = self.activity_box.get()
        goal = self.goal_box.get()
        macro = {"protein": round(self.s_pro.get()), "carb": round(self.s_carb.get()), "fat": round(self.s_fat.get())}

        if sum(macro.values()) != 100:
            messagebox.showerror("Macros", "Protein + Carbs + Fat must equal 100%.")
            return

        conn = db_connect()
        cur = conn.cursor()
        macro_json = json.dumps(macro)
        cur.execute("SELECT id FROM users WHERE name=?", (name,))
        row = cur.fetchone()
        if row:
            uid = row[0]
            cur.execute(
                """
                UPDATE users SET gender=?, age=?, height_cm=?, weight_kg=?, activity=?, goal=?, macro_json=?
                WHERE id=?
                """,
                (gender, age, height, weight, activity, goal, macro_json, uid),
            )
            self.main_app.current_user_id = uid
        else:
            cur.execute(
                """
                INSERT INTO users(name, gender, age, height_cm, weight_kg, activity, goal, macro_json)
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (name, gender, age, height, weight, activity, goal, macro_json),
            )
            self.main_app.current_user_id = cur.lastrowid
        conn.commit()
        conn.close()

        # Refresh main app data safely
        if hasattr(self.main_app, "refresh_user_select"):
            self.main_app.refresh_user_select()
        if hasattr(self.main_app, "load_current_user"):
            self.main_app.load_current_user()
        messagebox.showinfo("Saved", f"Profile '{name}' saved.")

    def populate_from_user(self, user_data):
        self.entry_name.delete(0, "end"); self.entry_name.insert(0, user_data.get("name", ""))
        self.gender_box.set(user_data.get("gender", "Male"))
        self.spin_age.delete(0, "end"); self.spin_age.insert(0, str(user_data.get("age", 25)))
        self.entry_height.delete(0, "end"); self.entry_height.insert(0, str(user_data.get("height", 170)))
        self.entry_weight.delete(0, "end"); self.entry_weight.insert(0, str(user_data.get("weight", 70)))
        self.activity_box.set(user_data.get("activity", "Moderate"))
        self.goal_box.set(user_data.get("goal", "Maintain"))
        macro = user_data.get("macro", {"protein":30, "carb":45, "fat":25})
        self.s_pro.set(macro.get("protein", 30))
        self.s_carb.set(macro.get("carb", 45))
        self.s_fat.set(macro.get("fat", 25))
        self._on_macro_change()
