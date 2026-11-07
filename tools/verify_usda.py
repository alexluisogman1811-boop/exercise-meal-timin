"""Check every nutrient in data/foods.csv against USDA FoodData Central, exactly.

Rows with an fdc_id are compared value by value (per 100 g) with the USDA
record. Any difference is printed and the script exits with code 1.

Usage (from the project folder), pick one source:
    python tools/verify_usda.py --sr-dir path/to/FoodData_Central_sr_legacy_food_csv_2018-04
        (the free SR Legacy CSV download from https://fdc.nal.usda.gov/download-datasets)
    python tools/verify_usda.py --api
        (online API; set FDC_API_KEY or it uses the rate-limited DEMO_KEY)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

# USDA nutrient id -> foods.csv column
NUTRIENTS = {
    "1008": "kcal_100g", "1003": "protein_100g", "1005": "carb_100g", "1004": "fat_100g",
    "1079": "fiber_100g", "2000": "sugar_100g", "1093": "sodium_mg_100g",
}


def from_sr_dir(sr_dir: Path, ids: set[str]) -> dict[str, dict[str, float]]:
    """Per-100 g values for the ids from the SR Legacy CSV files."""
    values: dict[str, dict[str, float]] = {i: {} for i in ids}
    with open(sr_dir / "food_nutrient.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["fdc_id"] in ids and row["nutrient_id"] in NUTRIENTS:
                values[row["fdc_id"]][NUTRIENTS[row["nutrient_id"]]] = float(row["amount"])
    return values


def from_api(ids: set[str]) -> dict[str, dict[str, float]]:
    """Per-100 g values for the ids from the FoodData Central API."""
    key = os.environ.get("FDC_API_KEY", "DEMO_KEY")
    values: dict[str, dict[str, float]] = {}
    for fdc_id in sorted(ids):
        url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={key}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        values[fdc_id] = {
            NUTRIENTS[str(n["nutrient"]["id"])]: float(n["amount"])
            for n in data.get("foodNutrients", [])
            if str(n.get("nutrient", {}).get("id")) in NUTRIENTS and "amount" in n
        }
        time.sleep(1)
    return values


def main() -> int:
    """Compare foods.csv with USDA and report every mismatch."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sr-dir", type=Path, help="folder of the SR Legacy CSV download")
    group.add_argument("--api", action="store_true", help="use the online FDC API")
    args = parser.parse_args()

    with open(config.FOODS_CSV, encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("fdc_id", "").strip()]
    ids = {r["fdc_id"].strip() for r in rows}
    usda = from_sr_dir(args.sr_dir, ids) if args.sr_dir else from_api(ids)

    problems = 0
    for row in rows:
        fdc_id = row["fdc_id"].strip()
        for column in NUTRIENTS.values():
            ours = float(row[column])
            theirs = usda.get(fdc_id, {}).get(column, 0.0)  # USDA omits nutrients it reports as 0
            status = "OK " if ours == theirs else "BAD"
            problems += status == "BAD"
            if status == "BAD":
                print(f"{status} {row['food_id']} (FDC {fdc_id}) {column}: csv={ours} usda={theirs}")
        print(f"checked {row['food_id']} FDC {fdc_id}: {row['name_th']}")
    print(f"\n{len(rows)} foods x {len(NUTRIENTS)} nutrients checked, {problems} mismatch(es)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
