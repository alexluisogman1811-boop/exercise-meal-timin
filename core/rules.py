"""Timing recommendation and avoid-rules engine.

Rules live in data/meal_timing_rules.csv. Each rule has a human text
("condition") for display and a machine-readable expression ("condition_expr")
that this module parses, for example:

    fat_level == high OR cooking contains ทอด|เจียว
    sugar_level == high AND is_liquid == true

Grammar (AND binds tighter than OR, no brackets):
    expr    := clause ( (AND | OR) clause )*
    clause  := field operator value
    operator:= == != > >= < <= contains not_contains
    value   := text or number; for contains, alternatives are split by "|"

Fields are food columns (see data_loader), "slot", or "profile.<key>"
(for example profile.duration_min).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

import config
from core import calc

OPERATORS = ["not_contains", "contains", ">=", "<=", "==", "!=", ">", "<"]
_CLAUSE_RE = re.compile(
    r"^\s*([\w.]+)\s+(" + "|".join(re.escape(o) for o in OPERATORS) + r")\s+(.+?)\s*$"
)

Clause = tuple[str, str, str]
Condition = list[list[Clause]]  # OR of AND-groups


class ConditionError(ValueError):
    """Raised when a condition expression cannot be parsed."""


# --------------------------------------------------------------------------
# Parsing and evaluation
# --------------------------------------------------------------------------
def parse_condition(expr: str) -> Condition:
    """Parse an expression into OR-groups of AND-clauses.

    Example: "a == 1 AND b > 2 OR c contains x" -> [[a,b], [c]].
    Raises ConditionError for empty or malformed text.
    """
    if not isinstance(expr, str) or not expr.strip():
        raise ConditionError("ไม่มีเงื่อนไขที่อ่านได้ด้วยเครื่อง (condition_expr ว่าง)")
    groups: Condition = []
    for or_part in re.split(r"\s+OR\s+", expr.strip()):
        group: list[Clause] = []
        for and_part in re.split(r"\s+AND\s+", or_part):
            match = _CLAUSE_RE.match(and_part)
            if not match:
                raise ConditionError(f"อ่านเงื่อนไขไม่ได้: '{and_part.strip()}'")
            group.append((match.group(1), match.group(2), match.group(3)))
        groups.append(group)
    return groups


def _as_number(value: Any) -> float | None:
    """Return value as float, or None if it is not numeric."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _eval_clause(clause: Clause, context: Mapping[str, Any]) -> bool:
    """Evaluate one clause against a context dict. Missing fields are False."""
    field, op, raw = clause
    if field not in context or context[field] is None:
        return False
    actual = context[field]
    if op in ("contains", "not_contains"):
        text = str(actual).casefold()
        found = any(alt.strip().casefold() in text for alt in raw.split("|") if alt.strip())
        return found if op == "contains" else not found

    a_num, b_num = _as_number(actual), _as_number(raw)
    if a_num is not None and b_num is not None:
        a, b = a_num, b_num
    else:
        a, b = str(actual).strip().casefold(), raw.strip().casefold()
        if op not in ("==", "!="):
            return False  # ordering only makes sense for numbers
    return {
        "==": a == b, "!=": a != b, ">": a > b,
        ">=": a >= b, "<": a < b, "<=": a <= b,
    }[op]


def evaluate(condition: Condition, context: Mapping[str, Any]) -> bool:
    """True if any OR-group has all of its AND-clauses true."""
    return any(all(_eval_clause(c, context) for c in group) for group in condition)


def build_context(food: Mapping, slot: str, profile: Mapping | None) -> dict:
    """Flatten a food, the slot and the profile into one lookup dict."""
    context = {k: v for k, v in dict(food).items()}
    context["is_liquid"] = "true" if food.get("is_liquid") else "false"
    context["easy_digest"] = "true" if food.get("easy_digest") else "false"
    context["slot"] = slot
    for key, value in dict(profile or {}).items():
        context[f"profile.{key}"] = value
    return context


# --------------------------------------------------------------------------
# Avoid checks
# --------------------------------------------------------------------------
def _allergy_warnings(food: Mapping, profile: Mapping | None) -> list[dict]:
    """Warnings from the user's allergy / lactose answers (profile rules)."""
    if not profile:
        return []
    text = " ".join(str(food.get(k, "")) for k in ("name_th", "category", "tags")).casefold()
    warnings = []
    for key in profile.get("allergies") or []:
        words = config.ALLERGY_KEYWORDS.get(key, [])
        if any(w.casefold() in text for w in words):
            warnings.append({
                "rule_id": f"ALLERGY-{key}", "group": "การแพ้อาหาร",
                "reason": f"คุณระบุว่าแพ้{config.ALLERGY_LABELS_TH.get(key, key)}",
                "severity": "high", "reference": "ข้อมูลโปรไฟล์ของผู้ใช้",
                "condition": "อาหารมีคำที่เกี่ยวกับสารก่อภูมิแพ้ที่ผู้ใช้ระบุ",
            })
    if profile.get("lactose_intolerance"):
        lactose_free = any(w.casefold() in text for w in config.LACTOSE_FREE_WORDS)
        if not lactose_free and any(w.casefold() in text for w in config.ALLERGY_KEYWORDS["milk"]):
            warnings.append({
                "rule_id": "LACTOSE", "group": "แพ้น้ำตาลแลคโตส",
                "reason": "อาจมีแลคโตส ซึ่งคุณระบุว่าย่อยไม่ได้ (เลือกชนิดแลคโตสฟรีแทน)",
                "severity": "medium", "reference": "ข้อมูลโปรไฟล์ของผู้ใช้",
                "condition": "อาหารประเภทนม/ผลิตภัณฑ์นม ที่ไม่ได้ระบุว่าแลคโตสฟรี",
            })
    return warnings


def check_avoid(food: Mapping, slot: str, profile: Mapping | None,
                rules: Sequence[Mapping]) -> list[dict]:
    """Evaluate every enforced rule against a food in a slot.

    Returns a list of warnings: rule_id, group, reason, severity, reference,
    condition (original text). Rules without a reference or with a condition
    that could not be parsed are not enforced (see data_loader).
    """
    context = build_context(food, slot, profile)
    warnings: list[dict] = []
    for rule in rules:
        if not rule.get("enforced") or slot not in rule.get("slot_list", []):
            continue
        if not evaluate(rule["parsed"], context):
            continue
        exception = rule.get("parsed_except")
        if exception and evaluate(exception, context):
            continue  # the rule itself allows this case
        warnings.append({
            "rule_id": rule["rule_id"], "group": rule.get("group", ""),
            "reason": rule.get("reason", ""), "severity": rule.get("severity", "medium"),
            "reference": rule.get("reference", ""), "condition": rule.get("condition", ""),
        })
    return warnings + _allergy_warnings(food, profile)


# --------------------------------------------------------------------------
# Recommendations
# --------------------------------------------------------------------------
def _energy_shares(food: Mapping) -> dict[str, float]:
    """Energy share of protein / carb / fat in a food (fractions)."""
    e = config.ENERGY_PER_G
    parts = {
        "protein": calc.safe_number(food.get("protein_100g")) * e["protein"],
        "carb": calc.safe_number(food.get("carb_100g")) * e["carb"],
        "fat": calc.safe_number(food.get("fat_100g")) * e["fat"],
    }
    total = sum(parts.values())
    return {k: (v / total if total > 0 else 0.0) for k, v in parts.items()}


def _score_food(food: Mapping, slot: str, profile: Mapping, slot_kcal: float) -> tuple[float, list[str], dict]:
    """Score how well a food fits a slot (0-1) and explain why in Thai."""
    shares = _energy_shares(food)
    ideal = config.SLOT_MACRO_SHARE[slot]
    macro_fit = 1 - sum(abs(shares[k] - ideal[k]) for k in ideal) / 2
    score = 0.5 * macro_fit
    reasons: list[str] = []
    if macro_fit >= 0.7:
        reasons.append(
            f"สัดส่วนพลังงานเหมาะกับช่วงนี้ (คาร์บ {shares['carb']:.0%} "
            f"โปรตีน {shares['protein']:.0%} ไขมัน {shares['fat']:.0%})"
        )

    serving_kcal = calc.per_serving(food)["kcal"]
    qty = calc.suggested_portion(serving_kcal, slot_kcal)
    portion = calc.per_serving(food, qty)
    tags = str(food.get("tags", ""))

    if slot in config.PRE_SLOTS:
        if food.get("easy_digest"):
            score += 0.15
            reasons.append("ย่อยง่าย ลดโอกาสจุกเสียดขณะออกกำลังกาย")
        if food.get("fat_level") == "low":
            score += 0.1
            reasons.append("ไขมันต่ำ")
        if food.get("fiber_level") == "low":
            score += 0.1
            reasons.append("ใยอาหารต่ำ ไม่ทำให้ท้องอืด")
        if slot == "during" and food.get("is_liquid"):
            score += 0.1
            reasons.append("เป็นเครื่องดื่ม ได้ทั้งน้ำและคาร์โบไฮเดรต")
        if slot == "during" and "เกลือแร่" in tags:
            score += 0.1
            reasons.append("มีเกลือแร่ช่วยทดแทนเหงื่อ")
    if slot == "post_2h":
        weight = calc.safe_number(profile.get("weight_kg"), 60)
        low, high = (weight * f for f in config.POST_PROTEIN_G_PER_KG)
        # Full marks from the low end of the target; fades only well above it.
        p = portion["protein"]
        fit = min(p / low, 1.0) if p <= high * 1.5 else max(0.0, 1 - (p - high * 1.5) / high)
        score += 0.25 * fit
        if portion["protein"] >= low * 0.5:
            reasons.append(
                f"โปรตีน {portion['protein']:.0f} ก. ช่วยฟื้นฟูกล้ามเนื้อ "
                f"(เป้าหลังออกกำลังกาย {low:.0f}-{high:.0f} ก.)"
            )
        if portion["carb"] >= 10:
            reasons.append("มีคาร์โบไฮเดรตช่วยเติมไกลโคเจน")
    if slot == "bedtime":
        if "ย่อยช้า" in tags:
            score += 0.15
            reasons.append("โปรตีนย่อยช้า เหมาะก่อนนอน")
        if portion["kcal"] <= slot_kcal:
            score += 0.1
            reasons.append("ปริมาณพอดี ไม่อิ่มเกินไป")
    if slot == "other_meal" and portion["protein"] >= 10:
        score += 0.1
        reasons.append("มีโปรตีนช่วยให้อิ่มนานและเสริมกล้ามเนื้อ")
    # General penalties so less healthy choices sink even where no rule bans them.
    if food.get("fat_level") == "high":
        score -= 0.2
    if food.get("sugar_level") == "high" and slot != "during":
        score -= 0.2
    if food.get("needs_source_check"):
        score -= 0.1
    if not reasons:
        reasons.append("เข้ากับแนวทางของช่วงเวลานี้ได้ในระดับหนึ่ง")
    return score, reasons, {"qty": qty, **portion}


def recommend(foods: Sequence[Mapping], slot: str, profile: Mapping,
              rules: Sequence[Mapping], slot_kcal: float = 400.0,
              benefits: Mapping[str, Mapping] | None = None) -> list[dict]:
    """Return up to config.RECOMMEND_MAX foods for a slot, best fit first.

    A food is a candidate only if it has a source, positive energy and
    triggers no warning from check_avoid for this slot.
    """
    benefits = benefits or {}
    slot_rules = [r["rule_id"] for r in rules if r.get("enforced") and slot in r.get("slot_list", [])]
    results = []
    for food in foods:
        if not str(food.get("source", "")).strip():
            continue
        if calc.safe_number(food.get("kcal_100g")) <= 0:
            continue
        if check_avoid(food, slot, profile, rules):
            continue
        score, reasons, portion = _score_food(food, slot, profile, slot_kcal)
        benefit = benefits.get(str(food["food_id"]), {})
        results.append({
            "food_id": food["food_id"], "name_th": food.get("name_th", ""),
            "serving_desc": food.get("serving_desc", ""), "score": round(score, 3),
            "qty": portion["qty"], "grams": portion["grams"], "kcal": portion["kcal"],
            "protein": portion["protein"], "carb": portion["carb"], "fat": portion["fat"],
            "reasons": reasons, "source": food.get("source", ""),
            "benefit": benefit.get("benefit_text", ""),
            "key_nutrient": benefit.get("key_nutrient", ""),
            "benefit_source": benefit.get("source", ""),
            "checked_rules": slot_rules,
            "guidance_source": config.SLOT_GUIDANCE_TH[slot]["source"],
        })
    results.sort(key=lambda r: (-r["score"], str(r["food_id"])))
    return results[: config.RECOMMEND_MAX]


# --------------------------------------------------------------------------
# Clock times
# --------------------------------------------------------------------------
def _parse_hhmm(text: str) -> datetime:
    """Parse 'HH:MM' into a datetime on a fixed reference day."""
    hour, minute = (int(x) for x in str(text).strip()[:5].split(":"))
    return datetime(2000, 1, 2, hour, minute)


def slot_times(start_time: str, duration_min: float,
               bedtime: str = config.DEFAULT_BEDTIME) -> dict[str, dict]:
    """Clock-time window for every slot from the exercise start and length.

    Returns {slot: {"start": "HH:MM", "end": "HH:MM", "sort": datetime,
    "note": str}}. "during" is included only for sessions over 60 min.
    """
    start = _parse_hhmm(start_time)
    end = start + timedelta(minutes=float(duration_min))
    bed = _parse_hhmm(bedtime)
    if bed <= end:
        bed += timedelta(days=1)  # bedtime after midnight
    other = start.replace(hour=7, minute=0) if start.hour >= 11 else start.replace(hour=12, minute=0)

    windows = {
        "other_meal": (other, other + timedelta(hours=1)),
        "pre_3h": (start - timedelta(hours=4), start - timedelta(hours=3)),
        "pre_1h": (start - timedelta(minutes=60), start - timedelta(minutes=30)),
        "during": (start, end),
        "post_2h": (end, end + timedelta(hours=2)),
        "bedtime": (bed - timedelta(hours=1), bed),
    }
    if duration_min <= 60:
        windows.pop("during")
    result = {}
    for slot, (a, b) in windows.items():
        note = ""
        if slot == "pre_3h" and (a.day < start.day or a.hour < config.EARLIEST_REASONABLE_HOUR):
            note = ("ช่วงนี้เช้ามืดเกินไป ถ้าออกกำลังกายตอนเช้า "
                    "ให้ใช้มื้อก่อนนอนของคืนก่อนและของว่าง 30-60 นาทีแทน")
        if slot == "during":
            low, high = config.DURING_CARB_G_PER_H
            hours = float(duration_min) / 60
            note = f"ควรได้คาร์โบไฮเดรตรวม {low * hours:.0f}-{high * hours:.0f} ก. ตลอดการฝึก"
        result[slot] = {"start": a.strftime("%H:%M"), "end": b.strftime("%H:%M"),
                        "sort": a, "note": note}
    return dict(sorted(result.items(), key=lambda kv: kv[1]["sort"]))
