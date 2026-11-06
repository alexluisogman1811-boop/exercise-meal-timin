"""Tests for core/calc.py."""
import math

import pytest

import config
from core import calc


# ---------------------------------------------------------------- BMR
@pytest.mark.parametrize("sex, kg, cm, age, expected", [
    # male:   10*70 + 6.25*175 - 5*25 + 5   = 700 + 1093.75 - 125 + 5   = 1673.75
    ("male", 70, 175, 25, 1673.75),
    # female: 10*55 + 6.25*160 - 5*30 - 161 = 550 + 1000 - 150 - 161    = 1239
    ("female", 55, 160, 30, 1239.0),
    # male:   10*60 + 6.25*170 - 5*16 + 5   = 600 + 1062.5 - 80 + 5     = 1587.5
    ("male", 60, 170, 16, 1587.5),
    # female: 10*80 + 6.25*165 - 5*45 - 161 = 800 + 1031.25 - 225 - 161 = 1445.25
    ("female", 80, 165, 45, 1445.25),
])
def test_bmr_known_cases(sex, kg, cm, age, expected):
    assert calc.bmr_mifflin(sex, kg, cm, age) == pytest.approx(expected)


# ---------------------------------------------------------------- TDEE
@pytest.mark.parametrize("level, factor", [
    ("light", 1.375), ("moderate", 1.55), ("heavy", 1.725), ("very_heavy", 1.9),
])
def test_tdee_factors(level, factor):
    assert calc.tdee(1500, level) == pytest.approx(1500 * factor)


# ---------------------------------------------------------------- goal
def test_goal_adjustments_defaults():
    assert calc.target_kcal(2500, 1600, "lose_fat")[0] == pytest.approx(2500 * 0.85)
    assert calc.target_kcal(2500, 1600, "maintain")[0] == pytest.approx(2500)
    assert calc.target_kcal(2500, 1600, "gain_muscle")[0] == pytest.approx(2500 * 1.10)


def test_goal_factor_is_clamped_to_safe_range():
    kcal, notes = calc.target_kcal(2500, 1600, "lose_fat", factor=0.5)
    assert kcal == pytest.approx(2500 * 0.80)
    assert notes
    kcal, _ = calc.target_kcal(2500, 1600, "gain_muscle", factor=1.5)
    assert kcal == pytest.approx(2500 * 1.15)


def test_lose_fat_never_below_bmr():
    # 1500 * 0.85 = 1275 < BMR 1400 -> raised to 1400 with an explanation
    kcal, notes = calc.target_kcal(1500, 1400, "lose_fat")
    assert kcal == pytest.approx(1400)
    assert any("BMR" in n for n in notes)


# ---------------------------------------------------------------- macros
@pytest.mark.parametrize("kcal, kg, goal, level", [
    (2000, 60, "maintain", "moderate"),
    (1500, 50, "lose_fat", "light"),
    (3200, 80, "gain_muscle", "very_heavy"),
    (1200, 90, "lose_fat", "light"),  # very low target: carb clamped, still sums
])
def test_macro_energy_sums_to_target(kcal, kg, goal, level):
    m = calc.macro_targets(kcal, kg, goal, level)
    energy = calc.macro_energy_kcal(m["protein_g"], m["carb_g"], m["fat_g"])
    assert abs(energy - kcal) / kcal <= 0.01
    assert all(m[k] >= 0 for k in ("protein_g", "carb_g", "fat_g"))


def test_protein_factor_and_fat_share():
    m = calc.macro_targets(2000, 60, "maintain", "moderate")
    assert m["protein_g"] == pytest.approx(60 * 1.4)
    assert m["fat_g"] * 9 == pytest.approx(2000 * 0.25)
    assert calc.protein_target_g(60, "maintain", factor=3.0) == pytest.approx(60 * 2.0)


def test_carb_note_outside_range():
    # 1200 kcal for 90 kg leaves very little carbohydrate -> below 3 g/kg note
    m = calc.macro_targets(1200, 90, "lose_fat", "light")
    assert m["carb_g_per_kg"] < 3
    assert m["notes"]


def test_compute_needs_no_nan_or_negative():
    needs = calc.compute_needs({"sex": "female", "age": 17, "weight_kg": 48, "height_cm": 155,
                                "activity_level": "light", "goal": "lose_fat"})
    for key, value in needs.items():
        if isinstance(value, float):
            assert value >= 0 and not math.isnan(value), key
    assert needs["target_kcal"] >= needs["bmr"]
    assert needs["water_ml_low"] == pytest.approx(48 * 30)


# ---------------------------------------------------------------- inputs
def test_validate_inputs():
    assert calc.validate_inputs(20, 60, 170) == []
    errors = calc.validate_inputs(14, 250, "abc")
    assert len(errors) == 3
    assert calc.safe_number(float("nan")) == 0.0
    assert calc.safe_number(-5) == 0.0


# ---------------------------------------------------------------- servings
def test_per_serving_math():
    food = {"serving_g": 150, "kcal_100g": 130, "protein_100g": 2.7, "carb_100g": 28.2,
            "fat_100g": 0.3, "fiber_100g": 0.4, "sugar_100g": 0.1, "sodium_mg_100g": 1}
    one = calc.per_serving(food)
    assert one["kcal"] == pytest.approx(195)          # 130 * 150 / 100
    two = calc.per_serving(food, 2)
    assert two["protein"] == pytest.approx(2.7 * 3)   # 2.7 * 300 / 100


# ---------------------------------------------------------------- slots
def test_slot_split_config_sums_to_100():
    assert sum(config.SLOT_SPLIT_PCT.values()) == pytest.approx(100)
    assert set(config.SLOT_SPLIT_PCT) == set(config.SLOTS)


@pytest.mark.parametrize("duration", [45, 60, 90])
def test_slot_split_sums_to_one(duration):
    split = calc.slot_split(duration)
    assert sum(split.values()) == pytest.approx(1.0)
    assert ("during" in split) == (duration > 60)


def test_macro_share_table_sums_to_one():
    for slot, share in config.SLOT_MACRO_SHARE.items():
        assert sum(share.values()) == pytest.approx(1.0), slot


# ---------------------------------------------------------------- SUS
def test_sus_score():
    assert calc.sus_score([5, 1] * 5) == 100
    assert calc.sus_score([1, 5] * 5) == 0
    assert calc.sus_score([3] * 10) == 50
    with pytest.raises(ValueError):
        calc.sus_score([3] * 9)


def test_adherence():
    assert calc.kcal_adherence_pct(2000, 2000) == 100
    assert calc.kcal_adherence_pct(2200, 2000) == pytest.approx(90)
    assert calc.protein_adherence_pct(150, 100) == 100
