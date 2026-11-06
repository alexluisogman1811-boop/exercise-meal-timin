# 🍱 Exercise Meal Timing (MVP)

Personalized, time-based meal planning and food selection web app for people who exercise.
High-school research project. UI in Thai, code in English.

> ⚕️ ไม่ใช่เครื่องมือวินิจฉัยหรือรักษาโรค / Not a diagnostic or treatment tool.
> For healthy people aged 15-45 only.

---

## เริ่มต้นใช้งาน (ภาษาไทย)

**วิธีง่ายที่สุด (Windows):** ดับเบิลคลิก `run.bat` — ครั้งแรกจะติดตั้งโปรแกรมให้อัตโนมัติ (ประมาณ 2 นาที) แล้วเปิดแอปในเบราว์เซอร์

หรือทำเอง:

1. ติดตั้ง Python 3.11 ขึ้นไป
2. เปิด Terminal ในโฟลเดอร์โปรเจกต์ แล้วรัน
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows  (Mac/Linux: source .venv/bin/activate)
   pip install -r requirements.txt
   ```
3. ตั้งรหัสผู้ดูแล: คัดลอก `.streamlit/secrets.toml.example` เป็น `.streamlit/secrets.toml` แล้วเปลี่ยนรหัสผ่าน
4. รันแอป: `streamlit run app.py` แล้วเปิด http://localhost:8501
5. รันการทดสอบ: `python -m pytest`

ถ้ายังไม่มีข้อมูลอาหารจริงใน `data/foods.csv` แอปจะใช้ **ข้อมูลตัวอย่าง (DEMO) 10 รายการ** และขึ้นป้าย "ข้อมูลตัวอย่าง ไม่ใช่ค่าจริง"

## Quick start (English)

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # then edit the password
streamlit run app.py
python -m pytest                  # all tests must pass
```

---

## Project structure

| Path | What it does |
|---|---|
| `app.py` | Navigation (Thai page titles), home page, disclaimer, consent |
| `pages/1_Profile.py` … `pages/7_Feedback_SUS.py` | The 7 user pages |
| `pages/8_Admin.py` | Password-protected admin: data checks, ignored rules, usage, CSV export |
| `config.py` | **Every constant and assumption**, each with its source |
| `core/calc.py` | BMR, TDEE, goal, macros, water, serving math, slot split, SUS (pure functions) |
| `core/rules.py` | Condition parser, `check_avoid`, `recommend`, clock times per slot |
| `core/data_loader.py` | Load + validate CSVs, derived levels, kcal check, DEMO fallback |
| `core/db.py` | All SQLite access (swap this file for Google Sheets / Supabase later) |
| `core/ui.py` | Shared Streamlit helpers (guards, footer, chips, cached data) |
| `data/` | `foods.csv`, `meal_timing_rules.csv`, `food_benefits.csv` (+ `data/demo/`) |
| `tools/import_workbook.py` | Converts the Excel workbook to the CSV files |
| `tests/` | pytest suite |
| `METHODS.md` | Every formula and assumption (for the research report) |

---

## Updating the food data / การอัปเดตข้อมูลอาหาร

### Option A: from the Excel workbook
```bash
python tools/import_workbook.py path\to\workbook.xlsx
```
- Sheet **ฐานข้อมูลอาหาร** → `data/foods.csv` (the row with id `ตัวอย่าง` is skipped)
- Sheet **อาหารที่ไม่ควรบริโภค** → `data/meal_timing_rules.csv`
- The script *suggests* a machine-readable `condition_expr` for each rule from the Thai text.
  **Check every one by hand.** Rules with an empty or unreadable `condition_expr` are not enforced and are listed on the admin page.

### Option B: edit the CSV directly
Open in Excel or Google Sheets and save as **CSV UTF-8**.

`foods.csv` columns:
`food_id, name_th, category, state, cooking, serving_desc, serving_g, kcal_100g, protein_100g, carb_100g, fat_100g, fiber_100g, sugar_100g, sodium_mg_100g, easy_digest, tags, source, source_date`

- `state`: write `ของเหลว` for drinks (drinks use per-100 mL thresholds)
- `easy_digest`: `ใช่` / `ไม่`
- `tags`: separate with `;` e.g. `โปรตีน;ย่อยช้า`. Tags used by the app: `ย่อยช้า`, `เกลือแร่`, `คาเฟอีน`, `แอลกอฮอล์`, `เผ็ด`, and allergy words (see `config.ALLERGY_KEYWORDS`)
- `source` must not be empty — foods without a source are never recommended

`food_benefits.csv`: `food_id, benefit_text, key_nutrient, source` — keep the text short, general and sourced. No medical claims.

`meal_timing_rules.csv`:
`rule_id, group, examples, avoid_when, slots, reason, condition, reference, reviewer, condition_expr, except_expr, severity`

- `slots`: comma list of `pre_3h, pre_1h, during, post_2h, bedtime, other_meal`
- `condition`: original Thai text (shown to users)
- `condition_expr`: what the app evaluates, e.g. `fat_level == high OR cooking contains ทอด|เจียว`
  - operators: `== != > >= < <= contains not_contains`; join with `AND` / `OR` (AND first)
  - fields: any food column, `fat_level`, `sugar_level`, `fiber_level` (`low/medium/high`), `is_liquid`, `easy_digest` (`true/false`), `kcal_serving`, `slot`, `profile.<field>` (e.g. `profile.duration_min`)
- `except_expr`: optional; when true the rule does **not** fire (e.g. `slot == during AND tags contains เกลือแร่`)
- `severity`: `high`, `medium` or `low`
- `reference` empty → rule ignored (not enforced) and listed in the admin page

After editing, open **ผู้ดูแลระบบ → โหลดไฟล์ข้อมูลใหม่**, or restart the app. Run `python -m pytest` to check the files.

---

## Deploy to Streamlit Community Cloud (free)

1. Push this folder to a GitHub repository (`app.db` and `secrets.toml` are ignored by `.gitignore`).
2. Go to https://share.streamlit.io → **Create app** → choose the repo, branch, and `app.py`.
3. **Advanced settings** → Python version **3.11** (or newer); **Secrets**: paste
   `admin_password = "your-long-password"`
4. Deploy. Every `git push` redeploys the app.

> ⚠️ **Important for research data:** Streamlit Community Cloud does **not** keep files permanently.
> `app.db` is wiped when the app restarts, sleeps for a long time, or is redeployed.
> Download the research ZIP from the admin page **after every data-collection session**,
> or move storage to Supabase / Google Sheets by re-implementing the functions in `core/db.py`.

## Exporting research data

Admin page (`ผู้ดูแลระบบ`) → enter the password → tab **ส่งออกข้อมูล**:
`users.csv`, `food_logs.csv`, `daily_summary.csv`, `usage_logs.csv`, `feedback.csv`, `session_lengths.csv`,
or everything in one ZIP. CSVs are UTF-8 with BOM, so Thai opens correctly in Excel.
Each user can also download their own data on the history page and delete all of it on the home page.

## Privacy

- No real names, phone numbers or photos; a nickname and a random 8-character `user_id` only.
- Data is used for research only (stated on the consent screen).
- Users under 18 must confirm parent/guardian consent.
- "ลบข้อมูลของฉัน" on the home page deletes all of a user's rows.
- All SQL uses parameterized queries.

## License / สัญญาอนุญาต

Code: [MIT License](LICENSE) — free to use, copy and modify; keep the copyright notice.
โค้ดเปิดเผยภายใต้สัญญาอนุญาต MIT ใช้ แก้ไข และเผยแพร่ต่อได้ฟรี โดยคงข้อความลิขสิทธิ์ไว้

The DEMO food values are invented for testing. Nutrition data you import from other sources
(e.g. Thai food composition tables) keeps its own terms — check them before publishing `data/foods.csv`.
This software is educational and is not medical advice.

## Contributing

Issues and pull requests are welcome. Please run `python -m pytest` before sending changes,
and put every new number or assumption in `config.py` with its source.
