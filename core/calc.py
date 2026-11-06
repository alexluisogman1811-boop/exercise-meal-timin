"""Pure calculation functions: BMR, TDEE, macro targets, serving math, SUS.

No Streamlit and no database here, so every function can be unit tested.
All constants come from config.py.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence

import config


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def safe_number(value: object, default: float = 0.0) -> float:
    """Return value as a float that is never NaN, infinite or negative."""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number) or number < 0:
        return default
    return number


def clamp(value: float, low: float, high: float) -> float:
    """Keep value inside [low, high]."""
    return max(low, min(high, value))


# --------------------------------------------------------------------------
# Input validation
# --------------------------------------------------------------------------
def validate_inputs(age: object, weight_kg: object, height_cm: object) -> list[str]:
    """Check body inputs and return a list of friendly Thai error messages.

    An empty list means every input is valid.
    """
    errors: list[str] = []
    checks = [
        (age, config.AGE_RANGE, "อายุ", "ปี"),
        (weight_kg, config.WEIGHT_RANGE_KG, "น้ำหนัก", "กิโลกรัม"),
        (height_cm, config.HEIGHT_RANGE_CM, "ส่วนสูง", "เซนติเมตร"),
    ]
    for value, (low, high), name, unit in checks:
        try:
            number = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            errors.append(f"กรุณากรอก{name}เป็นตัวเลข")
            continue
        if math.isnan(number) or not (low <= number <= high):
            errors.append(f"{name}ต้องอยู่ระหว่าง {low:g}-{high:g} {unit}")
    return errors


# --------------------------------------------------------------------------
# Energy
# --------------------------------------------------------------------------
def bmr_mifflin(sex: str, weight_kg: float, height_cm: float, age: float) -> float:
    """Basal metabolic rate (kcal/day), Mifflin-St Jeor 1990.

    male   = 10*kg + 6.25*cm - 5*age + 5
    female = 10*kg + 6.25*cm - 5*age - 161
    """
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    value = base + 5 if sex == "male" else base - 161
    return safe_number(value)


def tdee(bmr: float, activity_level: str) -> float:
    """Total daily energy expenditure = BMR * activity factor."""
    factor = config.ACTIVITY_FACTORS[activity_level]
    return safe_number(bmr * factor)


def target_kcal(tdee_kcal: float, bmr: float, goal: str,
                factor: float | None = None) -> tuple[float, list[str]]:
    """Daily energy target for the goal, with safety guards.

    The goal factor is kept inside config.GOAL_FACTOR_LIMITS, and a fat-loss
    target is never allowed below BMR. Returns (kcal, Thai notes).
    """
    notes: list[str] = []
    low, high = config.GOAL_FACTOR_LIMITS[goal]
    chosen = config.GOAL_FACTORS[goal] if factor is None else factor
    if not (low <= chosen <= high):
        notes.append(f"ปรับตัวคูณเป้าหมายให้อยู่ในช่วงที่ปลอดภัย ({low:g}-{high:g})")
        chosen = clamp(chosen, low, high)
    kcal = tdee_kcal * chosen
    if goal == "lose_fat" and kcal < bmr:
        notes.append(
            "พลังงานเป้าหมายต่ำกว่าพลังงานพื้นฐาน (BMR) จึงปรับขึ้นเท่ากับ BMR "
            "เพื่อความปลอดภัย การลดพลังงานมากเกินไปอาจทำให้เสียมวลกล้ามเนื้อ"
        )
        kcal = bmr
    return safe_number(kcal), notes


def protein_target_g(weight_kg: float, goal: str, factor: float | None = None) -> float:
    """Protein g/day = weight * factor (factor kept inside 1.2-2.0 g/kg)."""
    chosen = config.PROTEIN_G_PER_KG[goal] if factor is None else factor
    chosen = clamp(chosen, *config.PROTEIN_G_PER_KG_LIMITS)
    return safe_number(weight_kg * chosen)


def macro_targets(kcal: float, weight_kg: float, goal: str, activity_level: str,
                  fat_pct: float | None = None,
                  protein_factor: float | None = None) -> dict:
    """Split target energy into protein, fat and carbohydrate grams.

    Protein comes first (g/kg), fat is a % of energy, carbohydrate fills the
    rest. Energy of the three always adds up to kcal. Returns a dict with
    protein_g, fat_g, carb_g, carb_g_per_kg and Thai notes.
    """
    e = config.ENERGY_PER_G
    notes: list[str] = []
    pct = config.FAT_PCT if fat_pct is None else clamp(fat_pct, *config.FAT_PCT_LIMITS)

    protein_g = protein_target_g(weight_kg, goal, protein_factor)
    fat_g = kcal * pct / e["fat"]
    carb_kcal = kcal - protein_g * e["protein"] - fat_g * e["fat"]
    if carb_kcal < 0:
        # Very low energy target: keep protein, shrink fat so nothing is negative.
        fat_g = max(0.0, (kcal - protein_g * e["protein"]) / e["fat"])
        carb_kcal = 0.0
        notes.append("พลังงานเป้าหมายต่ำมาก จึงลดสัดส่วนไขมันและคาร์โบไฮเดรตลง")
    carb_g = carb_kcal / e["carb"]
    carb_per_kg = carb_g / weight_kg if weight_kg > 0 else 0.0

    low, high = config.CARB_G_PER_KG_RANGE
    if activity_level == "very_heavy":
        high = config.CARB_G_PER_KG_MAX_VERY_HEAVY
    if carb_per_kg < low:
        notes.append(
            f"คาร์โบไฮเดรต {carb_per_kg:.1f} ก./กก. ต่ำกว่าช่วงแนะนำ {low:g}-{high:g} ก./กก. "
            "อาจทำให้พลังงานไม่พอสำหรับการฝึก"
        )
    elif carb_per_kg > high:
        notes.append(
            f"คาร์โบไฮเดรต {carb_per_kg:.1f} ก./กก. สูงกว่าช่วงแนะนำ {low:g}-{high:g} ก./กก."
        )
    return {
        "protein_g": safe_number(protein_g),
        "fat_g": safe_number(fat_g),
        "carb_g": safe_number(carb_g),
        "carb_g_per_kg": safe_number(carb_per_kg),
        "fat_pct": pct,
        "notes": notes,
    }


def water_ml(weight_kg: float) -> tuple[float, float]:
    """Baseline water guideline (mL/day) as a (low, high) range."""
    low, high = config.WATER_ML_PER_KG
    return safe_number(weight_kg * low), safe_number(weight_kg * high)


def compute_needs(profile: Mapping) -> dict:
    """Run the whole needs calculation for a profile dict.

    Profile keys: sex, age, weight_kg, height_cm, activity_level, goal.
    """
    w = float(profile["weight_kg"])
    bmr = bmr_mifflin(profile["sex"], w, float(profile["height_cm"]), float(profile["age"]))
    total = tdee(bmr, profile["activity_level"])
    kcal, notes = target_kcal(total, bmr, profile["goal"])
    macros = macro_targets(kcal, w, profile["goal"], profile["activity_level"])
    water_low, water_high = water_ml(w)
    return {
        "bmr": bmr, "tdee": total, "target_kcal": kcal,
        "protein_g": macros["protein_g"], "fat_g": macros["fat_g"],
        "carb_g": macros["carb_g"], "carb_g_per_kg": macros["carb_g_per_kg"],
        "fat_pct": macros["fat_pct"],
        "water_ml_low": water_low, "water_ml_high": water_high,
        "notes": notes + macros["notes"],
    }


def macro_energy_kcal(protein_g: float, carb_g: float, fat_g: float) -> float:
    """Energy (kcal) from macronutrient grams using Atwater factors."""
    e = config.ENERGY_PER_G
    return protein_g * e["protein"] + carb_g * e["carb"] + fat_g * e["fat"]


# --------------------------------------------------------------------------
# Serving math
# --------------------------------------------------------------------------
NUTRIENT_COLUMNS = {
    "kcal": "kcal_100g", "protein": "protein_100g", "carb": "carb_100g",
    "fat": "fat_100g", "fiber": "fiber_100g", "sugar": "sugar_100g",
    "sodium_mg": "sodium_mg_100g",
}


def per_serving(food: Mapping, qty: float = 1.0) -> dict:
    """Nutrients for qty servings: value_100g * serving_g / 100 * qty."""
    grams = safe_number(food.get("serving_g")) * safe_number(qty)
    return {
        key: safe_number(food.get(col)) * grams / 100
        for key, col in NUTRIENT_COLUMNS.items()
    } | {"grams": grams}


def kcal_check_ratio(protein: float, carb: float, fat: float, kcal: float) -> float:
    """Relative gap |4P+4C+9F - kcal| / kcal (inf when kcal is 0)."""
    if kcal <= 0:
        return math.inf if macro_energy_kcal(protein, carb, fat) > 0 else 0.0
    return abs(macro_energy_kcal(protein, carb, fat) - kcal) / kcal


# --------------------------------------------------------------------------
# Splitting the day across time slots
# --------------------------------------------------------------------------
def slot_split(duration_min: float) -> dict[str, float]:
    """Fraction of the daily targets per slot (sums to 1.0).

    Sessions of 60 min or less have no "during" slot; its share is spread
    proportionally over the remaining slots.
    """
    pct = dict(config.SLOT_SPLIT_PCT)
    if duration_min <= 60:
        pct.pop("during", None)
    total = sum(pct.values())
    return {slot: value / total for slot, value in pct.items()}


def slot_targets(needs: Mapping, duration_min: float) -> dict[str, dict[str, float]]:
    """Per-slot kcal / protein / carb / fat targets from the daily needs."""
    return {
        slot: {
            "kcal": needs["target_kcal"] * share,
            "protein": needs["protein_g"] * share,
            "carb": needs["carb_g"] * share,
            "fat": needs["fat_g"] * share,
        }
        for slot, share in slot_split(duration_min).items()
    }


def suggested_portion(food_kcal_per_serving: float, slot_kcal: float) -> float:
    """Servings so one food covers about half of the slot energy.

    Rounded to config.PORTION_STEP and kept inside config.PORTION_RANGE.
    """
    if food_kcal_per_serving <= 0:
        return 1.0
    raw = (slot_kcal / 2) / food_kcal_per_serving
    step = config.PORTION_STEP
    return clamp(round(raw / step) * step, *config.PORTION_RANGE)


# --------------------------------------------------------------------------
# Adherence and questionnaires
# --------------------------------------------------------------------------
def kcal_adherence_pct(actual: float, target: float) -> float:
    """100 % when intake equals target, falling by the % distance from it."""
    if target <= 0:
        return 0.0
    return clamp(100 - abs(actual - target) / target * 100, 0, 100)


def protein_adherence_pct(actual: float, target: float) -> float:
    """Share of the protein target reached, capped at 100 %."""
    if target <= 0:
        return 0.0
    return clamp(actual / target * 100, 0, 100)


def sus_score(answers: Sequence[int]) -> float:
    """System Usability Scale score (0-100), Brooke 1996.

    Odd items contribute (answer - 1), even items (5 - answer); the sum is
    multiplied by 2.5. Answers must be 10 integers from 1 to 5.
    """
    if len(answers) != 10 or any(a not in (1, 2, 3, 4, 5) for a in answers):
        raise ValueError("SUS needs 10 answers from 1 to 5")
    total = sum((a - 1) if i % 2 == 0 else (5 - a) for i, a in enumerate(answers))
    return total * 2.5
