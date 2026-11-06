"""Convert the project Excel workbook into the CSV files in /data.

Usage (from the project folder):
    python tools/import_workbook.py path/to/workbook.xlsx

- Sheet "ฐานข้อมูลอาหาร"      -> data/foods.csv  (row with id "ตัวอย่าง" is skipped)
- Sheet "อาหารที่ไม่ควรบริโภค" -> data/meal_timing_rules.csv

Columns are matched by English name if the sheet already uses them,
otherwise by position in the order listed in FOOD_COLUMNS / RULE_COLUMNS.
For rules, a machine-readable "condition_expr" is SUGGESTED from the Thai
condition text. Always check the suggestions by hand: rules whose
condition_expr is empty are shown in the admin page and are not enforced.
food_benefits.csv is written by hand and is not touched.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from core.data_loader import FOOD_COLUMNS, RULE_COLUMNS, parse_slots  # noqa: E402

FOOD_SHEET = "ฐานข้อมูลอาหาร"
RULE_SHEET = "อาหารที่ไม่ควรบริโภค"

# Thai phrase in a condition -> clause. Extend this table when new phrases appear.
PHRASE_TO_CLAUSE = {
    "ไขมันสูง": "fat_level == high",
    "ทอด": "cooking contains ทอด|เจียว",
    "ใยอาหารสูง": "fiber_level == high",
    "กากใยสูง": "fiber_level == high",
    "น้ำตาลสูง": "sugar_level == high",
    "หวานจัด": "sugar_level == high",
    "แอลกอฮอล์": "tags contains แอลกอฮอล์ OR category contains แอลกอฮอล์",
    "คาเฟอีน": "tags contains คาเฟอีน",
    "โซเดียมสูง": "sodium_mg_100g > 600",
    "เผ็ด": "tags contains เผ็ด",
    "ย่อยยาก": "easy_digest == false",
}


def suggest_condition_expr(text: str) -> str:
    """Build an OR-expression from known Thai phrases ('' if none found)."""
    clauses = [clause for phrase, clause in PHRASE_TO_CLAUSE.items() if phrase in str(text)]
    return " OR ".join(dict.fromkeys(clauses))


def take_columns(df: pd.DataFrame, wanted: list[str]) -> pd.DataFrame:
    """Use named columns if present, else the first len(wanted) columns by position."""
    df.columns = [str(c).strip() for c in df.columns]
    if all(c in df.columns for c in wanted):
        return df[wanted].copy()
    if df.shape[1] < len(wanted):
        raise SystemExit(f"Sheet has {df.shape[1]} columns, expected {len(wanted)}: {wanted}")
    out = df.iloc[:, : len(wanted)].copy()
    out.columns = wanted
    return out


def main(xlsx: str) -> None:
    """Read the workbook and write the two CSV files."""
    foods = take_columns(pd.read_excel(xlsx, sheet_name=FOOD_SHEET, dtype=str), FOOD_COLUMNS)
    foods = foods.fillna("")
    foods = foods[(foods["food_id"].str.strip() != "") & (foods["food_id"].str.strip() != "ตัวอย่าง")]
    foods.to_csv(config.FOODS_CSV, index=False, encoding="utf-8-sig")
    print(f"foods.csv: {len(foods)} rows")

    rules = take_columns(pd.read_excel(xlsx, sheet_name=RULE_SHEET, dtype=str), RULE_COLUMNS).fillna("")
    rules = rules[rules["rule_id"].str.strip() != ""]
    rules["condition_expr"] = rules["condition"].apply(suggest_condition_expr)
    rules["except_expr"] = ""
    rules["severity"] = "medium"
    rules["slots"] = rules["slots"].apply(lambda s: ",".join(parse_slots(s)) or s)
    rules.to_csv(config.RULES_CSV, index=False, encoding="utf-8-sig")
    empty = rules[rules["condition_expr"] == ""]["rule_id"].tolist()
    print(f"meal_timing_rules.csv: {len(rules)} rules")
    if empty:
        print("Write condition_expr by hand for:", ", ".join(empty))
    print("Check every suggested condition_expr before using the app for research.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tools/import_workbook.py workbook.xlsx")
    main(sys.argv[1])
