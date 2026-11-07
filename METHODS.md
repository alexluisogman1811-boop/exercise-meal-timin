# Methods: formulas and assumptions

All values below live in `config.py` and can be changed there. Code: `core/calc.py`, `core/rules.py`, `core/data_loader.py`.

## 1. Participants and scope
- Healthy people aged 15-45 who exercise regularly.
- Excluded (screening question on the home page): chronic disease, pregnancy or breastfeeding, professional athletes, eating disorders.
- Under 18: parent/guardian consent confirmation is required.
- The app is educational. It does not diagnose or treat anything.

## 2. Input validation
| Input | Allowed range |
|---|---|
| Age | 15-45 years |
| Weight | 30-200 kg |
| Height | 120-220 cm |
| Exercise duration | 10-240 min |

No output is ever negative or NaN (`calc.safe_number`).

## 3. Energy
| Step | Formula | Source |
|---|---|---|
| BMR, male | 10·kg + 6.25·cm − 5·age + 5 | Mifflin et al. 1990, *Am J Clin Nutr* 51:241-247 |
| BMR, female | 10·kg + 6.25·cm − 5·age − 161 | same |
| TDEE | BMR × activity factor: light 1.375, moderate 1.55, heavy 1.725, very heavy 1.9 | Standard activity multipliers (e.g. McArdle, Katch & Katch, *Exercise Physiology*) |
| Lose fat | TDEE × 0.85 (allowed 0.80-0.85) and **never below BMR** | Helms et al. 2014, *JISSN* 11:20 |
| Maintain | TDEE × 1.00 | — |
| Gain muscle | TDEE × 1.10 (allowed 1.10-1.15) | Iraki et al. 2019, *Sports* 7(7):154 |

Safety guards: the goal factor is clamped to the allowed range; if a fat-loss target falls below BMR it is raised to BMR and the user sees an explanation.

## 4. Macronutrients
| Nutrient | Rule | Source |
|---|---|---|
| Protein | weight × factor; lose fat 1.8, maintain 1.4, gain muscle 1.8 g/kg (clamped 1.2-2.0) | Jäger et al. 2017, *JISSN* 14:20; Thomas et al. 2016 |
| Fat | 25 % of target kcal (allowed 20-35 %) | IOM Dietary Reference Intakes 2005 (AMDR) |
| Carbohydrate | (target kcal − 4·protein − 9·fat) / 4 | — |
| Carb check | shown as g/kg; note if outside 3-7 g/kg (up to 10 g/kg for very heavy training) | Thomas, Erdman & Burke 2016, *Med Sci Sports Exerc* 48(3):543-568 |
| Water | 30-40 mL/kg/day, guideline only | Common clinical rule of thumb |

Energy per gram (Atwater): protein 4, carbohydrate 4, fat 9 kcal/g (FAO 2003).
If protein + fat would leave negative carbohydrate (very low target), fat is reduced so all three stay ≥ 0 and still add up to the target.

## 5. Serving math
- nutrient per serving = value per 100 g × serving_g / 100
- nutrient for a log = per serving × quantity
- Food logs store a snapshot of kcal/protein/carb/fat at logging time, so later edits to `foods.csv` do not change history.

## 5b. Food composition data
- `data/foods.csv` values per 100 g are copied exactly from **USDA FoodData Central, SR Legacy (April 2018)**; each row's `fdc_id` names the record (e.g. 168878 = Rice, white, long-grain, regular, enriched, cooked).
- Serving sizes use USDA's own portion weights (e.g. 1 large egg = 50 g, 1 medium banana = 118 g).
- Nutrients: energy (1008), protein (1003), carbohydrate by difference (1005), total fat (1004), fibre (1079), total sugars (2000), sodium (1093).
- `tools/verify_usda.py` compares all 70 values with USDA and must report 0 mismatches.
- Spot-check against INMUCAL (Institute of Nutrition, Mahidol University): `tools/inmucal_check.py` picks foods at random with a fixed seed (2026), the researcher types the INMUCAL values per 100 g, and the script reports the % difference for energy, protein, carbohydrate and fat. A value "matches" when it is within 10 % (assumption: USDA and Thai tables differ in varieties and recipes).
- Not USDA: `easy_digest` and `tags` (project classification). Thai dishes absent from USDA (e.g. Thai milk tea, kluai nam wa banana) were replaced by the closest real USDA item and named as such, not estimated.

## 6. Food levels (per 100 g; drinks per 100 mL)
| Level | Solids | Drinks | Source |
|---|---|---|---|
| Fat low / high | ≤ 3 / > 17.5 g | ≤ 1.5 / > 8.75 g | UK DH/FSA front-of-pack guide 2016 |
| Sugar low / high | ≤ 5 / > 22.5 g | ≤ 2.5 / > 11.25 g | same |
| Fibre high | ≥ 6 g (< 3 g = low) | same | EU Reg. 1924/2006 nutrition claims |

A food is a drink when its `state` contains ของเหลว / เครื่องดื่ม.

## 7. Data quality check
Energy gap = |4P + 4C + 9F − kcal| / kcal. Rows with a gap > 15 % are flagged **needs source check** and listed in the admin page (they still appear, with a warning, and rank lower). Known causes: alcohol (7 kcal/g), sugar alcohols, rounding, or a typing error.

## 8. Time slots
| Slot | Clock time | Guidance | Source |
|---|---|---|---|
| pre_3h | start − 4 h to start − 3 h | main meal, complex carbohydrate, moderate protein, low fat and fibre | Thomas 2016; Kerksick et al. 2017, *JISSN* 14:33 |
| pre_1h | start − 60 min to start − 30 min | easy-to-digest carbohydrate, low fat and fibre | same |
| during | start to end (only if > 60 min) | 30-60 g carbohydrate per hour + water + electrolytes | Thomas 2016 |
| post_2h | end to end + 2 h | 0.25-0.3 g protein/kg (≈ 20-40 g) + carbohydrate + fluids | Jäger 2017; Kerksick 2017 |
| bedtime | bedtime − 1 h to bedtime | slow-digesting protein, not too full | Snijders et al. 2015, *J Nutr* 145:1178; Kinsey & Ormsbee 2015, *Nutrients* 7:2648 |
| other_meal | 07:00 if exercise starts ≥ 11:00, otherwise 12:00 | balanced main meal | Thomas 2016 |

If the pre_3h window falls before 05:00 the app explains an alternative (previous night's bedtime snack + pre_1h snack).

**Daily split (assumption, sums to 100 %):** other_meal 25, pre_3h 25, pre_1h 10, during 5, post_2h 25, bedtime 10. With sessions ≤ 60 min the "during" share is spread proportionally over the other slots.

## 9. Avoid rules
- Every rule in the app's rule file has a published reference; a rule without one is not included (proposal 6.8). The loader also ignores any rule whose reference is empty, as a safety net.
- The teacher checks the rule table and the food list and records `reviewer` + `review_date` on each row; the admin page exports this as evidence for the appendix.
- Each rule in `meal_timing_rules.csv` keeps the original Thai condition for display and a machine-readable `condition_expr` (clauses `field operator value`, joined by AND/OR, AND first).
- A rule fires when the slot is in its `slots` list and `condition_expr` is true, unless `except_expr` is true.
- Rules with no `reference`, an unreadable condition, or unknown slots are **not enforced** and listed in the admin page.
- Profile rules: allergies (keyword match on name/category/tags, `config.ALLERGY_KEYWORDS`) and lactose intolerance (milk words, unless tagged lactose-free).
- A food with any warning for a slot is never recommended for that slot.

## 10. Recommendation score (heuristic, 3-5 foods per slot)
Candidates: has a source, kcal > 0, no warnings.
- 0.5 × macro fit, where macro fit = 1 − ½ Σ |food energy share − slot ideal share| over protein/carb/fat (ideal shares in `config.SLOT_MACRO_SHARE`)
- pre_3h / pre_1h / during: +0.15 easy to digest, +0.10 low fat, +0.10 low fibre; during: +0.10 drink, +0.10 electrolytes
- post_2h: +0.25 × protein fit (full when the portion reaches 0.25 g/kg)
- bedtime: +0.15 slow-digesting protein tag, +0.10 portion ≤ slot energy
- other_meal: +0.10 portion has ≥ 10 g protein
- Penalties: −0.2 high fat, −0.2 high sugar (except during), −0.1 needs source check

Suggested portion = (slot kcal / 2) / kcal per serving, rounded to 0.5 and kept within 0.5-2 servings (one food covers about half of the slot).
Every recommendation shows its reasons, the nutrient data source, the rules checked and the slot guidance source.

## 11. Outcome measures
- **Energy adherence** per day = max(0, 100 − |intake − target| / target × 100) %
- **Protein adherence** per day = min(100, intake / target × 100) %
- **System Usability Scale** (Brooke 1996): odd items (answer − 1), even items (5 − answer), sum × 2.5 → 0-100. Average ≈ 68 (Sauro 2011).
- **Satisfaction**: 5 items on a 1-5 scale, stored as JSON.
- **Usage**: every page view and key action (consent, calc, view_plan, add/edit/delete log, submit_sus) with a timestamp. A page view's `duration_sec` is the time until the user's next page view. Sessions are split by gaps > 30 min; session length = last − first event.

## 12. Limitations
- BMR equations and activity factors are population estimates (typically ±10 %).
- Slot split, ideal macro shares and recommendation weights are project assumptions, not published values.
- The DEMO dataset is invented for testing and must not be used for research results.
- Allergy matching is keyword-based and cannot guarantee a food is allergen-free.
- Rules in the shipped file are marked "รอครูที่ปรึกษาตรวจ" (awaiting advisor review).

## References
- Brooke J. SUS: a "quick and dirty" usability scale. In: *Usability Evaluation in Industry*. 1996.
- FAO. *Food energy – methods of analysis and conversion factors*. FAO Food and Nutrition Paper 77. 2003.
- Helms ER, Aragon AA, Fitschen PJ. Evidence-based recommendations for natural bodybuilding contest preparation. *J Int Soc Sports Nutr*. 2014;11:20.
- Institute of Medicine. *Dietary Reference Intakes for Energy, Carbohydrate, Fiber, Fat, Fatty Acids, Cholesterol, Protein, and Amino Acids*. 2005.
- Iraki J, et al. Nutrition recommendations for bodybuilders in the off-season. *Sports*. 2019;7(7):154.
- Jäger R, et al. ISSN position stand: protein and exercise. *J Int Soc Sports Nutr*. 2017;14:20.
- Kerksick CM, et al. ISSN position stand: nutrient timing. *J Int Soc Sports Nutr*. 2017;14:33.
- Kinsey AW, Ormsbee MJ. The health impact of nighttime eating. *Nutrients*. 2015;7(4):2648-2662.
- Mifflin MD, St Jeor ST, et al. A new predictive equation for resting energy expenditure in healthy individuals. *Am J Clin Nutr*. 1990;51(2):241-247.
- Parr EB, et al. Alcohol ingestion impairs maximal post-exercise rates of myofibrillar protein synthesis. *PLoS One*. 2014;9(2):e88384.
- Drake C, et al. Caffeine effects on sleep taken 0, 3, or 6 hours before going to bed. *J Clin Sleep Med*. 2013;9(11):1195-1200.
- Sauro J. *A Practical Guide to the System Usability Scale*. 2011.
- Snijders T, et al. Protein ingestion before sleep increases muscle mass and strength gains during prolonged resistance-type exercise training in healthy young men. *J Nutr*. 2015;145(6):1178-1184.
- U.S. Department of Agriculture, Agricultural Research Service. FoodData Central: SR Legacy. April 2018. https://fdc.nal.usda.gov
- Thomas DT, Erdman KA, Burke LM. ACSM/AND/DC Joint Position Statement: Nutrition and Athletic Performance. *Med Sci Sports Exerc*. 2016;48(3):543-568.
- UK Department of Health / Food Standards Agency. *Guide to creating a front of pack nutrition label for pre-packed products*. 2016.
- Regulation (EC) No 1924/2006 on nutrition and health claims made on foods.
