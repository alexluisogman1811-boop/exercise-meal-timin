"""All constants and editable assumptions for the app.

Every number here is an ASSUMPTION that a teacher / nutrition advisor can
change without touching the logic. Each value has a comment naming its source.
See METHODS.md for the full list of formulas and references.
"""
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "app.db"

FOODS_CSV = DATA_DIR / "foods.csv"
RULES_CSV = DATA_DIR / "meal_timing_rules.csv"
BENEFITS_CSV = DATA_DIR / "food_benefits.csv"
DEMO_DIR = DATA_DIR / "demo"  # used when the real CSVs are empty or missing

# --------------------------------------------------------------------------
# Energy per gram of macronutrient (kcal/g)
# Source: Atwater general factors (FAO 2003, "Food energy - methods of
# analysis and conversion factors").
# --------------------------------------------------------------------------
ENERGY_PER_G = {"protein": 4.0, "carb": 4.0, "fat": 9.0}

# --------------------------------------------------------------------------
# Input limits (target group of the research project: healthy, 15-45 years)
# --------------------------------------------------------------------------
AGE_RANGE = (15, 45)
WEIGHT_RANGE_KG = (30.0, 200.0)
HEIGHT_RANGE_CM = (120.0, 220.0)
DURATION_RANGE_MIN = (10, 240)

# --------------------------------------------------------------------------
# Activity factors for TDEE = BMR * factor
# Source: standard activity multipliers used with BMR equations
# (e.g. McArdle, Katch & Katch, Exercise Physiology).
# --------------------------------------------------------------------------
ACTIVITY_FACTORS = {
    "light": 1.375,       # exercise 1-3 days/week
    "moderate": 1.55,     # exercise 3-5 days/week
    "heavy": 1.725,       # exercise 6-7 days/week
    "very_heavy": 1.9,    # hard training twice a day / physical job
}
ACTIVITY_LABELS_TH = {
    "light": "เบา (ออกกำลังกาย 1-3 วัน/สัปดาห์)",
    "moderate": "ปานกลาง (3-5 วัน/สัปดาห์)",
    "heavy": "หนัก (6-7 วัน/สัปดาห์)",
    "very_heavy": "หนักมาก (ฝึกวันละ 2 ครั้ง)",
}

# --------------------------------------------------------------------------
# Goal energy adjustment (multiplier on TDEE)
# Lose fat: 15-20 % deficit (factor 0.80-0.85); slow loss preserves lean mass
#   (Helms et al. 2014, J Int Soc Sports Nutr 11:20).
# Gain muscle: 10-15 % surplus (Iraki et al. 2019, Sports 7(7):154).
# GOAL_FACTOR_LIMITS is the safety guard: the app never goes outside it.
# --------------------------------------------------------------------------
GOAL_FACTORS = {"lose_fat": 0.85, "maintain": 1.00, "gain_muscle": 1.10}
GOAL_FACTOR_LIMITS = {
    "lose_fat": (0.80, 0.85),
    "maintain": (1.00, 1.00),
    "gain_muscle": (1.10, 1.15),
}
GOAL_LABELS_TH = {
    "lose_fat": "ลดไขมัน",
    "maintain": "รักษาน้ำหนัก",
    "gain_muscle": "เพิ่มกล้ามเนื้อ",
}

# --------------------------------------------------------------------------
# Protein (g per kg body weight per day)
# Source: ISSN position stand on protein and exercise, 1.4-2.0 g/kg
#   (Jäger et al. 2017, J Int Soc Sports Nutr 14:20); ACSM 2016: 1.2-2.0 g/kg.
# --------------------------------------------------------------------------
PROTEIN_G_PER_KG = {"lose_fat": 1.8, "maintain": 1.4, "gain_muscle": 1.8}
PROTEIN_G_PER_KG_LIMITS = (1.2, 2.0)

# --------------------------------------------------------------------------
# Fat (% of target energy)
# Source: Acceptable Macronutrient Distribution Range 20-35 %
#   (Institute of Medicine, Dietary Reference Intakes 2005).
# --------------------------------------------------------------------------
FAT_PCT = 0.25
FAT_PCT_LIMITS = (0.20, 0.35)

# --------------------------------------------------------------------------
# Carbohydrate reference range (g per kg per day)
# Source: Thomas, Erdman & Burke 2016, ACSM/AND/DC Joint Position Statement,
#   Med Sci Sports Exerc 48(3):543-568: 3-7 g/kg moderate, up to 10 g/kg very heavy.
# --------------------------------------------------------------------------
CARB_G_PER_KG_RANGE = (3.0, 7.0)
CARB_G_PER_KG_MAX_VERY_HEAVY = 10.0

# --------------------------------------------------------------------------
# Water baseline (mL per kg per day) - guideline only, not a prescription.
# Source: common clinical rule of thumb (30-40 mL/kg/day); actual needs
#   rise with sweat loss, heat and training time.
# --------------------------------------------------------------------------
WATER_ML_PER_KG = (30, 40)

# --------------------------------------------------------------------------
# Nutrient level thresholds (g per 100 g)
# Source: UK Department of Health / FSA front-of-pack labelling guide (2016).
#   Solids: fat low <=3, high >17.5; sugars low <=5, high >22.5.
#   Drinks (per 100 mL): fat low <=1.5, high >8.75; sugars low <=2.5, high >11.25.
# Fibre high >=6 g/100 g: EU Regulation (EC) 1924/2006 "high fibre" claim;
#   "source of fibre" >=3 g/100 g used as the low/medium cut-off.
# --------------------------------------------------------------------------
LEVEL_THRESHOLDS = {
    "solid": {
        "fat": {"low": 3.0, "high": 17.5},
        "sugar": {"low": 5.0, "high": 22.5},
        "fiber": {"low": 3.0, "high": 6.0},
    },
    "liquid": {
        "fat": {"low": 1.5, "high": 8.75},
        "sugar": {"low": 2.5, "high": 11.25},
        "fiber": {"low": 3.0, "high": 6.0},
    },
}
# Words in the "state" column that mean the food is a drink.
LIQUID_STATE_WORDS = ["เหลว", "เครื่องดื่ม", "liquid", "drink"]
LEVEL_LABELS_TH = {"low": "ต่ำ", "medium": "ปานกลาง", "high": "สูง"}

# Spot-check against INMUCAL (proposal 6.8): a nutrient "matches" when the app
# value is within this relative difference of the INMUCAL value. Assumption -
# USDA and Thai tables differ in varieties and recipes, so 10 % is allowed.
INMUCAL_TOLERANCE = 0.10
INMUCAL_SAMPLE_SEED = 2026

# Rows whose |4P + 4C + 9F - kcal| / kcal is above this are flagged
# "needs source check" (alcohol, polyols and rounding cause real gaps).
KCAL_CHECK_TOLERANCE = 0.15

# --------------------------------------------------------------------------
# Time slots around exercise
# Source for slot guidance: Thomas et al. 2016 (ACSM); Kerksick et al. 2017,
#   ISSN position stand: nutrient timing, J Int Soc Sports Nutr 14:33;
#   Snijders et al. 2015 (pre-sleep protein), J Nutr 145(6):1178-84.
# --------------------------------------------------------------------------
SLOTS = ["other_meal", "pre_3h", "pre_1h", "during", "post_2h", "bedtime"]
EXERCISE_SLOTS = ["pre_3h", "pre_1h", "during", "post_2h", "bedtime"]

SLOT_LABELS_TH = {
    "other_meal": "มื้อหลักอื่นของวัน",
    "pre_3h": "ก่อนออกกำลังกาย 3-4 ชม.",
    "pre_1h": "ก่อนออกกำลังกาย 30-60 นาที",
    "during": "ระหว่างออกกำลังกาย (เกิน 60 นาที)",
    "post_2h": "หลังออกกำลังกาย ภายใน 2 ชม.",
    "bedtime": "ก่อนนอน",
}

SLOT_GUIDANCE_TH = {
    "other_meal": {
        "text": "มื้อหลักที่สมดุล: ข้าว/แป้ง ผัก โปรตีน และผลไม้",
        "source": "Thomas et al. 2016 (ACSM/AND/DC Joint Position Statement)",
    },
    "pre_3h": {
        "text": "มื้อหลัก เน้นคาร์โบไฮเดรตเชิงซ้อน โปรตีนปานกลาง ไขมันและใยอาหารต่ำ",
        "source": "Thomas et al. 2016; Kerksick et al. 2017 (ISSN nutrient timing)",
    },
    "pre_1h": {
        "text": "คาร์โบไฮเดรตที่ย่อยง่าย ไขมันและใยอาหารต่ำ ปริมาณน้อย",
        "source": "Thomas et al. 2016; Kerksick et al. 2017",
    },
    "during": {
        "text": "คาร์โบไฮเดรตประมาณ 30-60 กรัม/ชั่วโมง ร่วมกับน้ำและเกลือแร่",
        "source": "Thomas et al. 2016 (ACSM)",
    },
    "post_2h": {
        "text": "โปรตีน 0.25-0.3 กรัม/กก. (ราว 20-40 กรัม) ร่วมกับคาร์โบไฮเดรตเพื่อเติมไกลโคเจน และดื่มน้ำ",
        "source": "Jäger et al. 2017 (ISSN protein); Kerksick et al. 2017",
    },
    "bedtime": {
        "text": "โปรตีนที่ย่อยช้า (เช่น นม ไข่) ปริมาณพอดี ไม่อิ่มจนเกินไป",
        "source": "Snijders et al. 2015 (J Nutr); Kinsey & Ormsbee 2015 (Nutrients)",
    },
}

# Share of the daily targets (kcal, protein, carb, fat) given to each slot.
# Must sum to 100 (a unit test checks this). When the session is <= 60 min
# there is no "during" slot and its share is spread over the others.
# Assumption by the project team - adjust to the user's real eating pattern.
SLOT_SPLIT_PCT = {
    "other_meal": 25,
    "pre_3h": 25,
    "pre_1h": 10,
    "during": 5,
    "post_2h": 25,
    "bedtime": 10,
}

# Ideal energy share (protein, carb, fat) of a food for each slot, used to rank
# recommendations. Derived from the slot guidance above (assumption).
SLOT_MACRO_SHARE = {
    "other_meal": {"protein": 0.25, "carb": 0.50, "fat": 0.25},
    "pre_3h": {"protein": 0.20, "carb": 0.65, "fat": 0.15},
    "pre_1h": {"protein": 0.10, "carb": 0.85, "fat": 0.05},
    "during": {"protein": 0.00, "carb": 1.00, "fat": 0.00},
    "post_2h": {"protein": 0.35, "carb": 0.55, "fat": 0.10},
    "bedtime": {"protein": 0.50, "carb": 0.30, "fat": 0.20},
}
# Slots where easy-to-digest, low-fat and low-fibre foods are preferred.
PRE_SLOTS = ["pre_3h", "pre_1h", "during"]

# Post-exercise protein (g per kg) - Jäger et al. 2017.
POST_PROTEIN_G_PER_KG = (0.25, 0.30)
# Carbohydrate during sessions > 60 min (g per hour) - Thomas et al. 2016.
DURING_CARB_G_PER_H = (30, 60)

DEFAULT_BEDTIME = "22:00"
# A pre-exercise meal earlier than this clock hour is shown with a note.
EARLIEST_REASONABLE_HOUR = 5

RECOMMEND_MIN, RECOMMEND_MAX = 3, 5
# Suggested portion is rounded to this step and kept inside these limits.
PORTION_STEP = 0.5
PORTION_RANGE = (0.5, 2.0)

SEVERITY_LABELS_TH = {"high": "สูง", "medium": "ปานกลาง", "low": "ต่ำ"}

# --------------------------------------------------------------------------
# Allergies: keywords searched in a food's name_th, category and tags.
# Assumption - the food table has no allergen column yet.
# --------------------------------------------------------------------------
ALLERGY_KEYWORDS = {
    "milk": ["นม", "โยเกิร์ต", "ชีส", "เวย์", "เนย"],
    "egg": ["ไข่"],
    "peanut": ["ถั่วลิสง"],
    "seafood": ["กุ้ง", "ปู", "หอย", "ปลาหมึก", "อาหารทะเล"],
    "fish": ["ปลา"],
    "soy": ["ถั่วเหลือง", "เต้าหู้", "นมถั่วเหลือง"],
    "wheat": ["ข้าวสาลี", "ขนมปัง", "บะหมี่", "กลูเตน"],
}
ALLERGY_LABELS_TH = {
    "milk": "นมวัว", "egg": "ไข่", "peanut": "ถั่วลิสง", "seafood": "อาหารทะเล (กุ้ง ปู หอย)",
    "fish": "ปลา", "soy": "ถั่วเหลือง", "wheat": "ข้าวสาลี/กลูเตน",
}
# Lactose intolerance uses the milk keywords, except foods tagged lactose-free.
LACTOSE_FREE_WORDS = ["แลคโตสฟรี", "ไม่มีแลคโตส", "lactose-free"]

EXERCISE_TYPES_TH = {"weights": "เวทเทรนนิ่ง", "cardio": "คาร์ดิโอ", "team_sport": "กีฬาประเภททีม"}
SEX_LABELS_TH = {"male": "ชาย", "female": "หญิง"}

# Usage logs: gaps longer than this start a new session.
SESSION_GAP_MIN = 30

DISCLAIMER_TH = (
    "แอปนี้เป็นเครื่องมือให้ความรู้ด้านโภชนาการสำหรับโครงงานวิจัยระดับมัธยมศึกษา "
    "ไม่ใช่เครื่องมือวินิจฉัยหรือรักษาโรค ค่าที่คำนวณเป็นค่าประมาณ "
    "ไม่เหมาะกับผู้มีโรคประจำตัว ผู้ตั้งครรภ์หรือให้นมบุตร นักกีฬาอาชีพ "
    "และผู้มีภาวะการกินผิดปกติ หากมีข้อสงสัยควรปรึกษาแพทย์หรือนักกำหนดอาหาร"
)
