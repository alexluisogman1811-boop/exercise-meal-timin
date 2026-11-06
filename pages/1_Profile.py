"""Profile: body data, exercise habits, goal and allergies."""
from datetime import time

import streamlit as st

import config
from core import calc, db, ui

ui.setup()
uid = ui.require_consent()
ui.log_view("profile")
st.title("🧙 ข้อมูลส่วนตัว")
ui.spell("profile")
st.caption("ไม่ต้องใช้ชื่อจริง ข้อมูลใช้เพื่อคำนวณและการวิจัยเท่านั้น")

user = ui.current_user() or {}


def _index(options: list, value, default: int = 0) -> int:
    """Position of value in options (default if missing)."""
    return options.index(value) if value in options else default


def _time(text: str | None, fallback: time) -> time:
    """'HH:MM' -> time."""
    try:
        h, m = (int(x) for x in str(text).split(":"))
        return time(h, m)
    except (TypeError, ValueError):
        return fallback


with st.form("profile"):
    nickname = st.text_input("ชื่อเล่น", value=user.get("nickname") or "", max_chars=30)
    sexes = list(config.SEX_LABELS_TH)
    sex = st.radio("เพศ (ใช้ในสูตรคำนวณพลังงาน)", sexes, horizontal=True,
                   index=_index(sexes, user.get("sex")),
                   format_func=config.SEX_LABELS_TH.get)
    c1, c2, c3 = st.columns(3)
    age = c1.number_input("อายุ (ปี)", min_value=0, max_value=120, step=1,
                          value=int(user.get("age") or 20))
    weight = c2.number_input("น้ำหนัก (กก.)", min_value=0.0, max_value=400.0, step=0.5,
                             value=float(user.get("weight_kg") or 60.0))
    height = c3.number_input("ส่วนสูง (ซม.)", min_value=0.0, max_value=300.0, step=1.0,
                             value=float(user.get("height_cm") or 165.0))

    types = list(config.EXERCISE_TYPES_TH)
    exercise_type = st.radio("ประเภทการออกกำลังกายหลัก", types, horizontal=True,
                             index=_index(types, user.get("exercise_type")),
                             format_func=config.EXERCISE_TYPES_TH.get)
    levels = list(config.ACTIVITY_FACTORS)
    activity = st.radio("ความถี่ / ระดับกิจกรรม", levels,
                        index=_index(levels, user.get("activity_level"), 1),
                        format_func=config.ACTIVITY_LABELS_TH.get)
    goals = list(config.GOAL_FACTORS)
    goal = st.radio("เป้าหมาย", goals, horizontal=True,
                    index=_index(goals, user.get("goal"), 1),
                    format_func=config.GOAL_LABELS_TH.get)

    c4, c5, c6 = st.columns(3)
    start = c4.time_input("เวลาเริ่มออกกำลังกาย", step=900,
                          value=_time(user.get("start_time"), time(17, 0)))
    duration = c5.number_input("ระยะเวลา (นาที)", step=15,
                               min_value=config.DURATION_RANGE_MIN[0],
                               max_value=config.DURATION_RANGE_MIN[1],
                               value=int(user.get("duration_min") or 60))
    bedtime = c6.time_input("เวลาเข้านอน", step=900,
                            value=_time(user.get("bedtime"), time(22, 0)))

    st.markdown("**การแพ้อาหาร** (เลือกได้หลายข้อ)")
    allergy_cols = st.columns(2)
    allergies = [
        key for i, (key, label) in enumerate(config.ALLERGY_LABELS_TH.items())
        if allergy_cols[i % 2].checkbox(label, value=key in (user.get("allergies") or []),
                                        key=f"allergy_{key}")
    ]
    lactose = st.checkbox("ย่อยน้ำตาลแลคโตสในนมไม่ได้ (Lactose intolerance)",
                          value=bool(user.get("lactose_intolerance")))
    guardian = st.checkbox("(สำหรับผู้อายุต่ำกว่า 18 ปี) ผู้ปกครองยินยอมให้เข้าร่วมแล้ว",
                           value=bool(user.get("guardian_consent")))
    submitted = st.form_submit_button("บันทึกและคำนวณ", type="primary")

if submitted:
    errors = calc.validate_inputs(age, weight, height)
    if not nickname.strip():
        errors.append("กรุณากรอกชื่อเล่น")
    if age < 18 and not guardian:
        errors.append("ผู้มีอายุต่ำกว่า 18 ปี ต้องได้รับความยินยอมจากผู้ปกครองก่อน")
    if errors:
        for err in errors:
            st.error(err)
    else:
        profile = {
            "nickname": nickname.strip(), "sex": sex, "age": int(age), "weight_kg": weight,
            "height_cm": height, "activity_level": activity, "goal": goal,
            "exercise_type": exercise_type, "start_time": start.strftime("%H:%M"),
            "duration_min": int(duration), "bedtime": bedtime.strftime("%H:%M"),
            "allergies": allergies, "lactose_intolerance": lactose, "guardian_consent": guardian,
        }
        needs = calc.compute_needs(profile)
        profile.update(target_kcal=needs["target_kcal"], target_protein=needs["protein_g"],
                       target_carb=needs["carb_g"], target_fat=needs["fat_g"])
        db.save_profile(uid, profile)
        ui.log_action("profile", "calc")
        st.success(f"บันทึกแล้ว พลังงานเป้าหมายของคุณคือ {needs['target_kcal']:,.0f} กิโลแคลอรี/วัน")
        for note in needs["notes"]:
            st.info(note)
        ui.link("needs", "ดูสรุปความต้องการพลังงาน", "⚡")
        ui.link("plan", "ดูแผนมื้ออาหารตามเวลา", "🕒")

ui.footer()
