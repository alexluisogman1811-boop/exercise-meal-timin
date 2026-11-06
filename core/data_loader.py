"""Load and validate the CSV data files.

Nothing here raises on bad data: problems are collected as Thai messages in
Dataset.errors / Dataset.warnings so the app can show them instead of crashing.
If foods.csv (or the rules / benefits file) is missing or empty, the DEMO
files in data/demo/ are used and Dataset.is_demo is set.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

import config
from core import calc
from core.rules import ConditionError, parse_condition

FOOD_COLUMNS = [
    "food_id", "name_th", "category", "state", "cooking", "serving_desc", "serving_g",
    "kcal_100g", "protein_100g", "carb_100g", "fat_100g", "fiber_100g", "sugar_100g",
    "sodium_mg_100g", "easy_digest", "tags", "source", "source_date",
]
# Allowed range for each numeric column (per 100 g unless stated).
NUMERIC_RANGES = {
    "serving_g": (0.1, 2000), "kcal_100g": (0, 900), "protein_100g": (0, 100),
    "carb_100g": (0, 100), "fat_100g": (0, 100), "fiber_100g": (0, 100),
    "sugar_100g": (0, 100), "sodium_mg_100g": (0, 40000),
}
RULE_COLUMNS = ["rule_id", "group", "examples", "avoid_when", "slots", "reason",
                "condition", "reference", "reviewer"]
RULE_OPTIONAL_COLUMNS = ["condition_expr", "except_expr", "severity"]
BENEFIT_COLUMNS = ["food_id", "benefit_text", "key_nutrient"]

TRUE_WORDS = {"1", "y", "yes", "true", "ใช่", "ง่าย", "ย่อยง่าย", "✓"}
# Thai words that may appear in the "slots" column of the workbook.
SLOT_WORDS_TH = {
    "3-4": "pre_3h", "3 ชม": "pre_3h", "30-60": "pre_1h", "1 ชม": "pre_1h",
    "ระหว่าง": "during", "หลัง": "post_2h", "ก่อนนอน": "bedtime",
}


@dataclass
class Dataset:
    """Everything the app needs from /data, plus validation results."""
    foods: pd.DataFrame
    rules: list[dict]
    benefits: dict[str, dict]
    is_demo: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ignored_rules: list[dict] = field(default_factory=list)

    @property
    def flagged_foods(self) -> pd.DataFrame:
        """Foods whose 4P+4C+9F energy differs from kcal by more than the tolerance."""
        if self.foods.empty:
            return self.foods
        return self.foods[self.foods["needs_source_check"]]


# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------
def read_csv(path: Path) -> pd.DataFrame | None:
    """Read a UTF-8 CSV as text columns; None if missing, empty or unreadable."""
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        return None
    df.columns = [c.strip() for c in df.columns]
    return None if df.empty else df


def missing_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    """Required columns that are not in df."""
    return [c for c in required if c not in df.columns]


def nutrient_level(value: float, nutrient: str, is_liquid: bool) -> str:
    """Classify a per-100 g value as low / medium / high using config thresholds."""
    limits = config.LEVEL_THRESHOLDS["liquid" if is_liquid else "solid"][nutrient]
    if nutrient == "fiber":
        if value >= limits["high"]:
            return "high"
        return "low" if value < limits["low"] else "medium"
    if value > limits["high"]:
        return "high"
    return "low" if value <= limits["low"] else "medium"


# --------------------------------------------------------------------------
# Foods
# --------------------------------------------------------------------------
def prepare_foods(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Validate the food table and add derived columns.

    Rows with missing ids or out-of-range numbers are dropped (and reported).
    Derived: is_liquid, fat/sugar/fiber_level, easy_digest (bool),
    kcal_serving, kcal_gap and needs_source_check.
    """
    errors: list[str] = []
    missing = missing_columns(raw, FOOD_COLUMNS)
    if missing:
        return pd.DataFrame(columns=FOOD_COLUMNS), [f"foods.csv ขาดคอลัมน์: {', '.join(missing)}"]

    df = raw[FOOD_COLUMNS].copy()
    df["food_id"] = df["food_id"].str.strip()
    df = df[(df["food_id"] != "") & (df["food_id"] != "ตัวอย่าง")]

    dupes = df.loc[df["food_id"].duplicated(), "food_id"].unique().tolist()
    if dupes:
        errors.append(f"foods.csv มี food_id ซ้ำ (ใช้แถวแรก): {', '.join(dupes)}")
        df = df.drop_duplicates("food_id", keep="first")

    bad_rows: set[int] = set()
    for col, (low, high) in NUMERIC_RANGES.items():
        df[col] = pd.to_numeric(df[col].str.replace(",", "").str.strip(), errors="coerce")
        bad = df[df[col].isna() | (df[col] < low) | (df[col] > high)]
        for idx, row in bad.iterrows():
            errors.append(f"อาหาร {row['food_id']}: ค่า {col} ไม่ถูกต้อง (ต้องอยู่ระหว่าง {low:g}-{high:g})")
            bad_rows.add(idx)
    df = df.drop(index=list(bad_rows))

    for _, row in df[df["source"].str.strip() == ""].iterrows():
        errors.append(f"อาหาร {row['food_id']}: ไม่มีแหล่งอ้างอิง (source) จะไม่ถูกนำไปแนะนำ")

    df["is_liquid"] = df["state"].apply(
        lambda s: any(w in str(s).lower() for w in config.LIQUID_STATE_WORDS))
    for nutrient in ("fat", "sugar", "fiber"):
        df[f"{nutrient}_level"] = [
            nutrient_level(v, nutrient, liq) for v, liq in zip(df[f"{nutrient}_100g"], df["is_liquid"])
        ]
    df["easy_digest"] = df["easy_digest"].str.strip().str.lower().isin(TRUE_WORDS)
    df["kcal_serving"] = df["kcal_100g"] * df["serving_g"] / 100
    df["kcal_gap"] = [
        calc.kcal_check_ratio(p, c, f, k)
        for p, c, f, k in zip(df["protein_100g"], df["carb_100g"], df["fat_100g"], df["kcal_100g"])
    ]
    df["needs_source_check"] = df["kcal_gap"] > config.KCAL_CHECK_TOLERANCE
    return df.reset_index(drop=True), errors


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------
def parse_slots(text: str) -> list[str]:
    """Turn '"pre_3h, pre_1h"' or Thai slot words into a list of slot codes."""
    slots: list[str] = []
    for part in str(text).replace(";", ",").split(","):
        part = part.strip()
        if part in config.EXERCISE_SLOTS or part in config.SLOTS:
            slots.append(part)
            continue
        for word, code in SLOT_WORDS_TH.items():
            if word in part and code not in slots:
                slots.append(code)
    if str(text).strip() in ("ทุกช่วง", "all"):
        slots = list(config.SLOTS)
    return slots


def prepare_rules(raw: pd.DataFrame) -> tuple[list[dict], list[dict], list[str]]:
    """Validate rules and parse their conditions.

    Returns (rules, ignored, errors). Every rule is returned; rules that
    cannot be enforced (empty reference, bad condition, no slots) have
    enforced=False and are also listed in ignored with the reason.
    """
    missing = missing_columns(raw, RULE_COLUMNS)
    if missing:
        return [], [], [f"meal_timing_rules.csv ขาดคอลัมน์: {', '.join(missing)}"]
    df = raw.copy()
    for col in RULE_OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    rules, ignored, errors = [], [], []
    for rec in df.to_dict("records"):
        rec = {k: str(v).strip() for k, v in rec.items()}
        if not rec["rule_id"]:
            continue
        rec["severity"] = rec["severity"].lower() if rec["severity"].lower() in config.SEVERITY_LABELS_TH else "medium"
        rec["slot_list"] = parse_slots(rec["slots"])
        problems = []
        # condition_expr is preferred; the original text is tried as a fallback.
        expr = rec["condition_expr"] or rec["condition"]
        try:
            rec["parsed"] = parse_condition(expr)
        except ConditionError as exc:
            rec["parsed"] = []
            problems.append(str(exc))
        rec["parsed_except"] = []
        if rec["except_expr"]:
            try:
                rec["parsed_except"] = parse_condition(rec["except_expr"])
            except ConditionError as exc:
                problems.append(f"ข้อยกเว้น: {exc}")
        if not rec["reference"]:
            problems.append("ไม่มีแหล่งอ้างอิง (reference)")
        if not rec["slot_list"]:
            problems.append(f"ไม่รู้จักช่วงเวลา '{rec['slots']}'")
        rec["enforced"] = not problems
        if problems:
            ignored.append({"rule_id": rec["rule_id"], "group": rec["group"],
                            "problem": "; ".join(problems)})
        rules.append(rec)
    dupes = pd.Series([r["rule_id"] for r in rules]).duplicated()
    if dupes.any():
        errors.append("meal_timing_rules.csv มี rule_id ซ้ำ")
    return rules, ignored, errors


# --------------------------------------------------------------------------
# Benefits and full dataset
# --------------------------------------------------------------------------
def prepare_benefits(raw: pd.DataFrame | None) -> tuple[dict[str, dict], list[str]]:
    """Index benefits by food_id."""
    if raw is None:
        return {}, []
    missing = missing_columns(raw, BENEFIT_COLUMNS)
    if missing:
        return {}, [f"food_benefits.csv ขาดคอลัมน์: {', '.join(missing)}"]
    return {str(r["food_id"]).strip(): r for r in raw.to_dict("records")}, []


def load_dataset(data_dir: Path = config.DATA_DIR) -> Dataset:
    """Load foods, rules and benefits; fall back to DEMO files when empty."""
    demo_dir = data_dir / "demo"
    errors: list[str] = []
    is_demo = False

    foods_raw = read_csv(data_dir / "foods.csv")
    if foods_raw is None:
        foods_raw, is_demo = read_csv(demo_dir / "foods.csv"), True
    rules_raw = read_csv(data_dir / "meal_timing_rules.csv")
    if rules_raw is None:
        rules_raw = read_csv(demo_dir / "meal_timing_rules.csv")
    benefits_raw = read_csv(data_dir / "food_benefits.csv")
    if benefits_raw is None or is_demo:
        # Demo foods must use demo benefits, otherwise ids would not match.
        benefits_raw = read_csv(demo_dir / "food_benefits.csv")

    if foods_raw is None:
        foods, food_errors = pd.DataFrame(columns=FOOD_COLUMNS), ["ไม่พบข้อมูลอาหารเลย (รวมถึงข้อมูลตัวอย่าง)"]
    else:
        foods, food_errors = prepare_foods(foods_raw)
    errors += food_errors

    if rules_raw is None:
        rules, ignored = [], []
        errors.append("ไม่พบไฟล์กฎ meal_timing_rules.csv จึงยังไม่มีคำเตือนอาหาร")
    else:
        rules, ignored, rule_errors = prepare_rules(rules_raw)
        errors += rule_errors

    benefits, benefit_errors = prepare_benefits(benefits_raw)
    errors += benefit_errors

    warnings = [f"กฎ {r['rule_id']} ไม่ถูกบังคับใช้: {r['problem']}" for r in ignored]
    return Dataset(foods=foods, rules=rules, benefits=benefits, is_demo=is_demo,
                   errors=errors, warnings=warnings, ignored_rules=ignored)
