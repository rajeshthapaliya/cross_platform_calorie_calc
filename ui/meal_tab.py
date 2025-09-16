import customtkinter as ctk

class MealTab:
    def __init__(self, tab_view, main_app):
        self.tab_view = tab_view
        self.main_app = main_app
        self.frame = ctk.CTkFrame(self.tab_view)
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)
        self._build_ui()

    def _build_ui(self):
        outer = self.frame

        self.meal_info = ctk.CTkLabel(
            outer, text="Use the Calculator first (or 'Use Profile Values'), then see suggested per-meal budget."
        )
        self.meal_info.pack(anchor="w")

        self.meal_plan_scroll = ctk.CTkScrollableFrame(outer, corner_radius=16)
        self.meal_plan_scroll.pack(fill="both", expand=True, pady=12)

        ctk.CTkButton(outer, text="Generate Meal Plan", command=self.generate_meal_plan).pack(pady=8)
    
    def generate_meal_plan(self):
        # Clear previous entries
        for w in self.meal_plan_scroll.winfo_children():
            w.destroy()

        target = getattr(self.main_app, "current_target", None)
        if not target:
            self.meal_info.configure(text="Please calculate your target calories first.")
            return

        splits = {
            "Breakfast": 0.25,
            "Lunch": 0.35,
            "Dinner": 0.30,
            "Snacks": 0.10,
        }
        macro = getattr(self.main_app.current_user or {}, "macro", {"protein": 30, "carb": 45, "fat": 25})

        for meal, frac in splits.items():
            kcal = target * frac
            p_g = kcal * macro.get("protein", 30) / 100 / 4
            c_g = kcal * macro.get("carb", 45) / 100 / 4
            f_g = kcal * macro.get("fat", 25) / 100 / 9

            card = ctk.CTkFrame(self.meal_plan_scroll, corner_radius=16)
            card.pack(fill="x", padx=6, pady=6)

            ctk.CTkLabel(card, text=f"{meal}", font=("Arial", 18, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
            ctk.CTkLabel(
                card, text=f"Budget: {kcal:.0f} kcal  •  Protein {p_g:.0f} g  •  Carbs {c_g:.0f} g  •  Fat {f_g:.0f} g"
            ).pack(anchor="w", padx=12, pady=(0, 10))

            ideas = {
                "Breakfast": "Oats + milk + banana; Omelette; Greek yogurt bowl",
                "Lunch": "Rice + dal + chicken/soy; Veg salad; Curd",
                "Dinner": "Grilled paneer/chicken + veggies; Chapati; Soup",
                "Snacks": "Fruits, nuts, peanut butter toast, lassi",
            }
            ctk.CTkLabel(card, text=f"Ideas: {ideas.get(meal, '')}", text_color="#9aa0a6").pack(
                anchor="w", padx=12, pady=(0, 12)
            )
