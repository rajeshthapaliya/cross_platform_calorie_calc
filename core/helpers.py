from datetime import date

ACTIVITY_FACTORS = {
    "Sedentary": 1.2,
    "Light": 1.375,
    "Moderate": 1.55,
    "Active": 1.725,
    "Very Active": 1.9,
}

def today_str():
    """Returns today's date in YYYY-MM-DD format."""
    return date.today().strftime("%Y-%m-%d")

def calc_bmr(gender, weight_kg, height_cm, age_years):
    """Calculates Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation."""
    gender = gender.lower()
    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years - 161
    return bmr

def calc_tdee(bmr, activity_level):
    """Calculates Total Daily Energy Expenditure (TDEE)."""
    factor = ACTIVITY_FACTORS.get(activity_level, 1.55)
    return bmr * factor

def apply_goal(tdee, goal):
    """Adjusts TDEE based on the user's goal."""
    goal = goal.lower()
    if goal == "lose":
        return tdee - 500
    elif goal == "gain":
        return tdee + 500
    else:  # Maintain
        return tdee
