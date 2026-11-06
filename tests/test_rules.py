"""Tests for core/rules.py (avoid rules, recommendations, clock times)."""
import pandas as pd
import pytest

import config
from core import rules
from core.data_loader import prepare_foods, prepare_rules, read_csv

PROFILE = {"weight_kg": 60, "duration_min": 90, "allergies": [], "lactose_intolerance": False}


@pytest.fixture(scope="module")
def foods():
    df, _ = prepare_foods(read_csv(config.DEMO_DIR / "foods.csv"))
    return df.to_dict("records")


@pytest.fixture(scope="module")
def rule_list():
    parsed, _, _ = prepare_rules(read_csv(config.DEMO_DIR / "meal_timing_rules.csv"))
    return parsed


def by_id(foods, food_id):
    return next(f for f in foods if f["food_id"] == food_id)


def make_food(**overrides):
    """A food row built through prepare_foods so derived columns are real."""
    base = {"food_id": "T1", "name_th": "ทดสอบ", "category": "เครื่องดื่ม", "state": "ของเหลว",
            "cooking": "พร้อมดื่ม", "serving_desc": "1 ขวด", "serving_g": "250", "kcal_100g": "60",
            "protein_100g": "0", "carb_100g": "15", "fat_100g": "0", "fiber_100g": "0",
            "sugar_100g": "15", "sodium_mg_100g": "50", "easy_digest": "ใช่", "tags": "",
            "source": "test", "source_date": "2026-01-01"}
    base.update({k: str(v) for k, v in overrides.items()})
    df, _ = prepare_foods(pd.DataFrame([base]))
    return df.to_dict("records")[0]


def test_fried_high_fat_food_pre_1h_warned_and_excluded(foods, rule_list):
    fried = by_id(foods, "D06")
    warnings = rules.check_avoid(fried, "pre_1h", PROFILE, rule_list)
    assert "R01" in [w["rule_id"] for w in warnings]
    assert all(w["reference"] for w in warnings)
    recs = rules.recommend(foods, "pre_1h", PROFILE, rule_list, 200)
    assert "D06" not in [r["food_id"] for r in recs]


def test_sugary_drink_during_blocked_unless_rule_allows(rule_list):
    sweet_tea = make_food(tags="คาเฟอีน")
    assert rules.check_avoid(sweet_tea, "during", PROFILE, rule_list)
    # The same sugar level in an electrolyte drink is allowed DURING (R03 exception) ...
    sports = make_food(tags="เกลือแร่")
    assert rules.check_avoid(sports, "during", PROFILE, rule_list) == []
    # ... but the exception does not apply before exercise.
    assert "R03" in [w["rule_id"] for w in rules.check_avoid(sports, "pre_1h", PROFILE, rule_list)]


def test_alcohol_after_exercise_warned(foods, rule_list):
    beer = by_id(foods, "D10")
    warnings = rules.check_avoid(beer, "post_2h", PROFILE, rule_list)
    assert "R04" in [w["rule_id"] for w in warnings]
    assert "D10" not in [r["food_id"] for r in rules.recommend(foods, "post_2h", PROFILE, rule_list)]


@pytest.mark.parametrize("slot", config.SLOTS)
def test_recommendations_have_source_and_no_warnings(foods, rule_list, slot):
    recs = rules.recommend(foods, slot, PROFILE, rule_list, 400)
    assert 1 <= len(recs) <= config.RECOMMEND_MAX
    for r in recs:
        assert r["source"].strip()
        assert r["reasons"]
        assert rules.check_avoid(by_id(foods, r["food_id"]), slot, PROFILE, rule_list) == []


def test_food_without_source_never_recommended(rule_list):
    food = make_food(source="", tags="เกลือแร่", sugar_100g=5)
    assert rules.recommend([food], "during", PROFILE, rule_list) == []


def test_rule_without_reference_not_enforced(rule_list):
    spicy = make_food(tags="เผ็ด", sugar_100g=1, state="ของแข็ง")
    assert all(w["rule_id"] != "R07" for w in rules.check_avoid(spicy, "pre_1h", PROFILE, rule_list))


def test_allergy_and_lactose_warnings(foods, rule_list):
    milk = by_id(foods, "D05")
    profile = PROFILE | {"lactose_intolerance": True}
    assert "LACTOSE" in [w["rule_id"] for w in rules.check_avoid(milk, "bedtime", profile, rule_list)]
    egg = by_id(foods, "D03")
    profile = PROFILE | {"allergies": ["egg"]}
    assert "ALLERGY-egg" in [w["rule_id"] for w in rules.check_avoid(egg, "post_2h", profile, rule_list)]


def test_profile_fields_in_conditions():
    cond = rules.parse_condition("profile.duration_min > 60 AND slot == during")
    assert rules.evaluate(cond, rules.build_context({}, "during", {"duration_min": 90}))
    assert not rules.evaluate(cond, rules.build_context({}, "during", {"duration_min": 45}))


def test_slot_times():
    t = rules.slot_times("17:00", 90, "22:00")
    assert (t["pre_3h"]["start"], t["pre_3h"]["end"]) == ("13:00", "14:00")
    assert (t["pre_1h"]["start"], t["pre_1h"]["end"]) == ("16:00", "16:30")
    assert (t["during"]["start"], t["during"]["end"]) == ("17:00", "18:30")
    assert (t["post_2h"]["start"], t["post_2h"]["end"]) == ("18:30", "20:30")
    assert t["bedtime"]["end"] == "22:00"
    assert "during" not in rules.slot_times("17:00", 60)
    early = rules.slot_times("06:00", 45)
    assert early["pre_3h"]["note"]    # 02:00 is too early -> explained
