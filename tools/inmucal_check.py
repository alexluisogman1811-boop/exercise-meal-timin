"""Spot-check the app's food values against INMUCAL (proposal section 6.8).

INMUCAL is the Thai nutrient calculation program of the Institute of Nutrition,
Mahidol University. It is a program, not a download, so its values are typed in
by hand. Two steps (run from the project folder):

1. Pick foods at random (reproducible with the seed) and make a form to fill:
       python tools/inmucal_check.py sample --n 5
   -> data/inmucal_check.csv  (look each food up in INMUCAL, type the per-100 g
      values, who checked and the date)

2. Compare the typed INMUCAL values with data/foods.csv:
       python tools/inmucal_check.py compare
   -> prints every difference and writes data/inmucal_check_report.csv
      (for the report appendix)
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

CHECK_CSV = config.DATA_DIR / "inmucal_check.csv"
REPORT_CSV = config.DATA_DIR / "inmucal_check_report.csv"
NUTRIENTS = ["kcal_100g", "protein_100g", "carb_100g", "fat_100g"]
FORM_COLUMNS = (["food_id", "name_th", "inmucal_food_name"]
                + [f"inmucal_{n}" for n in NUTRIENTS] + ["checked_by", "checked_date"])


def sample_foods(food_ids: list[str], n: int, seed: int) -> list[str]:
    """n food ids chosen at random; the same seed always gives the same pick."""
    return sorted(random.Random(seed).sample(sorted(food_ids), min(n, len(food_ids))))


def compare(foods: pd.DataFrame, check: pd.DataFrame,
            tolerance: float = config.INMUCAL_TOLERANCE) -> pd.DataFrame:
    """One row per (food, nutrient): app value, INMUCAL value, % difference, match."""
    app = foods.set_index("food_id")
    rows = []
    for rec in check.to_dict("records"):
        fid = str(rec["food_id"])
        for n in NUTRIENTS:
            ref = pd.to_numeric(rec.get(f"inmucal_{n}"), errors="coerce")
            if pd.isna(ref) or fid not in app.index:
                continue  # not filled in yet
            ours = float(app.loc[fid, n])
            diff = abs(ours - ref) / ref if ref else (0.0 if ours == 0 else float("inf"))
            rows.append({"food_id": fid, "name_th": app.loc[fid, "name_th"],
                         "inmucal_food_name": rec.get("inmucal_food_name", ""), "nutrient": n,
                         "app_value": ours, "inmucal_value": float(ref),
                         "diff_pct": round(diff * 100, 1), "match": diff <= tolerance,
                         "checked_by": rec.get("checked_by", ""), "checked_date": rec.get("checked_date", "")})
    return pd.DataFrame(rows)


def main() -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="INMUCAL spot-check")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample", help="pick foods and write the form to fill")
    s.add_argument("--n", type=int, default=5)
    s.add_argument("--seed", type=int, default=config.INMUCAL_SAMPLE_SEED)
    s.add_argument("--force", action="store_true", help="overwrite an existing form")
    sub.add_parser("compare", help="compare the filled form with foods.csv")
    args = parser.parse_args()

    foods = pd.read_csv(config.FOODS_CSV, dtype={"food_id": str}, encoding="utf-8-sig")
    if args.cmd == "sample":
        if CHECK_CSV.exists() and not args.force:
            print(f"{CHECK_CSV.name} already exists - use --force to overwrite it")
            return 1
        picked = sample_foods(foods["food_id"].tolist(), args.n, args.seed)
        form = pd.DataFrame([{c: "" for c in FORM_COLUMNS} for _ in picked])
        form["food_id"] = picked
        form["name_th"] = foods.set_index("food_id").loc[picked, "name_th"].tolist()
        form.to_csv(CHECK_CSV, index=False, encoding="utf-8-sig")
        print(f"Picked {len(picked)} foods (seed {args.seed}): {', '.join(picked)}")
        print(f"Fill in {CHECK_CSV} with INMUCAL values per 100 g, then run: compare")
        return 0

    if not CHECK_CSV.exists():
        print("No form yet - run: python tools/inmucal_check.py sample")
        return 1
    report = compare(foods, pd.read_csv(CHECK_CSV, dtype=str, encoding="utf-8-sig").fillna(""))
    if report.empty:
        print("No INMUCAL values filled in yet.")
        return 1
    report.to_csv(REPORT_CSV, index=False, encoding="utf-8-sig")
    for r in report.itertuples():
        mark = "OK  " if r.match else "DIFF"
        print(f"{mark} {r.food_id} {r.nutrient}: app={r.app_value:g} inmucal={r.inmucal_value:g} ({r.diff_pct}%)")
    matched = int(report["match"].sum())
    print(f"\n{matched}/{len(report)} values within {config.INMUCAL_TOLERANCE:.0%}; report: {REPORT_CSV.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
