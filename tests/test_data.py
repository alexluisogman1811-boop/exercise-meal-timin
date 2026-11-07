"""Tests for core/data_loader.py and the shipped CSV files."""
import shutil

import pandas as pd
import pytest

import config
from core import calc, db
from core.data_loader import (FOOD_COLUMNS, load_dataset, nutrient_level, prepare_foods,
                              prepare_rules, read_csv)
from core.rules import ConditionError, parse_condition

DEMO = config.DEMO_DIR


def demo_foods_raw() -> pd.DataFrame:
    return read_csv(DEMO / "foods.csv")


def test_demo_schema_and_ids():
    foods, errors = prepare_foods(demo_foods_raw())
    assert errors == []
    assert len(foods) == 10                     # "ตัวอย่าง" row skipped
    assert foods["food_id"].is_unique
    assert (foods["source"].str.strip() != "").all()


def test_missing_column_is_reported_not_raised():
    raw = demo_foods_raw().drop(columns=["kcal_100g"])
    foods, errors = prepare_foods(raw)
    assert foods.empty and "kcal_100g" in errors[0]


def test_duplicate_ids_and_bad_numbers_reported():
    raw = demo_foods_raw()
    raw = pd.concat([raw, raw.iloc[[1]]], ignore_index=True)   # duplicate D01
    raw.loc[2, "fat_100g"] = "-4"                               # out of range
    foods, errors = prepare_foods(raw)
    assert any("ซ้ำ" in e for e in errors)
    assert any("fat_100g" in e for e in errors)
    assert foods["food_id"].is_unique


def test_empty_source_reported():
    raw = demo_foods_raw()
    raw.loc[1, "source"] = ""
    _, errors = prepare_foods(raw)
    assert any("source" in e for e in errors)


def test_kcal_check_function():
    # rice: 4*2.7 + 4*28.2 + 9*0.3 = 126.3 vs 130 -> about 3 %
    assert calc.kcal_check_ratio(2.7, 28.2, 0.3, 130) == pytest.approx(3.7 / 130)
    foods, _ = prepare_foods(demo_foods_raw())
    flagged = foods[foods["needs_source_check"]]["food_id"].tolist()
    assert flagged == ["D10"]   # beer: alcohol energy is not in 4P+4C+9F


def test_nutrient_levels_use_config_thresholds():
    assert nutrient_level(3.0, "fat", False) == "low"
    assert nutrient_level(17.6, "fat", False) == "high"
    assert nutrient_level(22.6, "sugar", False) == "high"
    assert nutrient_level(12.0, "sugar", True) == "high"     # drinks: > 11.25 g/100 mL
    assert nutrient_level(6.0, "fiber", False) == "high"


@pytest.mark.parametrize("path", [config.RULES_CSV, DEMO / "meal_timing_rules.csv"])
def test_all_shipped_rule_conditions_parse(path):
    rules, ignored, errors = prepare_rules(read_csv(path))
    assert errors == []
    for rule in rules:
        if rule["reference"]:
            assert rule["enforced"], rule["rule_id"]
            assert rule["parsed"]
    if path == config.RULES_CSV:
        # Proposal 6.8: a rule without a reference is not put in the app at all.
        assert ignored == [] and all(r["reference"] for r in rules)
    else:
        # The DEMO copy keeps R07 (no reference) to prove such rules are ignored.
        assert [r["rule_id"] for r in ignored] == ["R07"]


def test_parse_condition_structure():
    parsed = parse_condition("fat_level == high AND kcal_100g > 200 OR cooking contains ทอด")
    assert parsed == [[("fat_level", "==", "high"), ("kcal_100g", ">", "200")],
                      [("cooking", "contains", "ทอด")]]
    with pytest.raises(ConditionError):
        parse_condition("ไขมันสูง")
    with pytest.raises(ConditionError):
        parse_condition("")


def test_demo_fallback_when_csvs_empty(tmp_path):
    shutil.copytree(DEMO, tmp_path / "demo")
    (tmp_path / "foods.csv").write_text(",".join(FOOD_COLUMNS) + "\n", encoding="utf-8")
    ds = load_dataset(tmp_path)
    assert ds.is_demo and len(ds.foods) == 10 and ds.rules and ds.benefits


def test_real_data_used_when_present(tmp_path):
    shutil.copytree(DEMO, tmp_path / "demo")
    shutil.copy(DEMO / "foods.csv", tmp_path / "foods.csv")
    assert not load_dataset(tmp_path).is_demo


def test_db_roundtrip(tmp_path):
    path = tmp_path / "t.db"
    db.init_db(path)
    db.create_user("abc12345", False, path)
    db.save_profile("abc12345", {"nickname": "บี", "sex": "male", "age": 20, "weight_kg": 60,
                                 "height_cm": 170, "target_kcal": 2000, "target_protein": 84,
                                 "allergies": ["egg"]}, path)
    assert db.get_user("abc12345", path)["allergies"] == ["egg"]
    db.add_food_log("abc12345", "D01", 2, "2026-11-06T08:00:00", "pre_3h",
                    {"kcal": 390, "protein": 8.1, "carb": 84.6, "fat": 0.9}, path)
    summary = db.get_daily_summary("abc12345", path)
    assert summary.loc[0, "kcal_total"] == 390 and summary.loc[0, "goal_kcal"] == 2000
    db.delete_user_data("abc12345", path)
    assert db.get_user("abc12345", path) is None
    assert db.get_food_logs("abc12345", db_path=path).empty


def test_user_progress_checklist(tmp_path):
    path = tmp_path / "p.db"
    db.init_db(path)
    db.create_user("u1", False, path)
    assert not any(db.user_progress("u1", "2026-11-06", path).values())
    db.log_usage("u1", "plan", "view", path)
    db.add_food_log("u1", "D01", 1, "2026-11-06T08:00:00", "pre_3h",
                    {"kcal": 195, "protein": 4, "carb": 42, "fat": 0.5}, path)
    progress = db.user_progress("u1", "2026-11-06", path)
    assert progress["plan"] and progress["log"]
    assert not progress["feedback"] and not progress["needs"]
    assert not db.user_progress("u1", "2026-11-07", path)["log"]   # food log is per day


def test_theme_css_both_modes():
    from core import theme
    for dark in (False, True):
        css = theme.css(dark)
        assert css.startswith("<style>") and "--gold" in css and "{{" not in css
    assert theme.PALETTES["light"].keys() == theme.PALETTES["dark"].keys()


def test_save_feedback_roundtrip(tmp_path):
    path = tmp_path / "f.db"
    db.init_db(path)
    db.create_user("u2", False, path)
    answers = [4, 2, 4, 2, 4, 2, 4, 2, 4, 2]
    db.save_feedback("u2", answers, calc.sus_score(answers), {"overall": 5}, "ดีมาก", path)
    row = db.export_table("feedback", path).iloc[0]
    assert [row[f"sus_q{i}"] for i in range(1, 11)] == answers
    assert row["sus_score"] == 75.0 and "overall" in row["satisfaction"] and row["comment"] == "ดีมาก"
    assert db.user_progress("u2", "2026-11-07", path)["feedback"]


def test_review_status_counts_only_dated_reviews():
    from core.data_loader import review_status
    ds = load_dataset(config.DATA_DIR)
    status = review_status(ds)
    assert len(status) == len(ds.foods) + len(ds.rules)
    assert not status["ตรวจแล้ว"].any()          # nothing reviewed yet in the shipped files
    ds.foods.loc[0, ["reviewer", "review_date"]] = ["ครูสมศรี", "2026-11-10"]
    assert review_status(ds)["ตรวจแล้ว"].sum() == 1


def test_inmucal_sample_and_compare():
    import sys
    sys.path.insert(0, str(config.BASE_DIR / "tools"))
    import inmucal_check as ic
    ids = [f"F{i:02d}" for i in range(1, 11)]
    assert ic.sample_foods(ids, 3, 2026) == ic.sample_foods(ids, 3, 2026)   # reproducible
    foods = pd.DataFrame({"food_id": ["F01"], "name_th": ["ข้าว"], "kcal_100g": [130.0],
                          "protein_100g": [2.69], "carb_100g": [28.17], "fat_100g": [0.28]})
    check = pd.DataFrame([{"food_id": "F01", "inmucal_kcal_100g": "125", "inmucal_protein_100g": "3.5",
                           "inmucal_carb_100g": "", "inmucal_fat_100g": "0.28"}])
    report = ic.compare(foods, check).set_index("nutrient")
    assert report.loc["kcal_100g", "match"]                 # 4 % apart
    assert not report.loc["protein_100g", "match"]          # 23 % apart
    assert "carb_100g" not in report.index                  # blank = not checked yet
