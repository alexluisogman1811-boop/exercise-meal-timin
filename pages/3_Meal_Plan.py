"""Meal plan by time: timeline of slots, recommendations and avoid warnings.

Each recommended food has a tick box: ticking saves it (with the suggested
portion) to today's food log, unticking removes it again.
"""
import html
from datetime import date, datetime

import streamlit as st

import config
from core import calc, db, rules, ui

ui.setup()
user = ui.require_profile()
ui.log_view("plan")
data = ui.get_dataset()
ui.show_data_banners(data)

st.title("🌠 แผนมื้ออาหารตามเวลา")
ui.spell("plan")
st.caption(f"ออกกำลังกาย {user['start_time']} น. นาน {user['duration_min']} นาที "
           f"({config.EXERCISE_TYPES_TH.get(user['exercise_type'], '')}) · เข้านอน {user['bedtime']} น.")

if data.foods.empty:
    st.warning("ยังไม่มีข้อมูลอาหารให้แนะนำ")
    ui.footer()
    st.stop()

if st.session_state.get("_plan_logged") != ui.user_id():
    ui.log_action("plan", "view_plan")
    st.session_state["_plan_logged"] = ui.user_id()

needs = ui.needs_for(user)
targets = calc.slot_targets(needs, user["duration_min"])
times = rules.slot_times(user["start_time"], user["duration_min"], user["bedtime"] or config.DEFAULT_BEDTIME)
foods = data.foods.to_dict("records")
uid = user["user_id"]
today = date.today().isoformat()

# {(slot, food_id): [log_id, ...]} for foods already saved today.
saved: dict[tuple[str, str], list[int]] = {}
for row in db.get_food_logs(uid, today).itertuples():
    saved.setdefault((row.slot, row.food_id), []).append(row.log_id)


def toggle_saved(key: str, slot: str, rec: dict) -> None:
    """Tick box callback: add the food to today's log, or remove it."""
    if st.session_state[key]:
        db.add_food_log(uid, rec["food_id"], rec["qty"], f"{today}T{datetime.now():%H:%M:%S}",
                        slot, {k: rec[k] for k in ("kcal", "protein", "carb", "fat")})
        ui.log_action("plan", "add_log")
        text, kind = f"✅ Scriptum! บันทึก “{rec['name_th']}” ลงบันทึกอาหารแล้ว ({rec['kcal']:.0f} kcal)", "ok"
    else:
        for log_id in saved.get((slot, rec["food_id"]), []):
            db.delete_food_log(log_id, uid)
        ui.log_action("plan", "delete_log")
        text, kind = f"↩️ นำ “{rec['name_th']}” ออกจากบันทึกอาหารแล้ว", "undo"
    st.toast(text, duration="long")
    # Also shown as a banner inside this slot's card on the rerun.
    st.session_state["_saved_msg"] = (slot, rec["food_id"], text, kind)


# {slot: [(food, warnings)]} - foods that trigger at least one rule in that slot.
avoid = {
    slot: [(f, w) for f in foods if (w := rules.check_avoid(f, slot, user, data.rules))]
    for slot in config.SLOTS
}

for slot, window in times.items():
    with st.container(border=True):
        st.subheader(f"{window['start']}-{window['end']} น. · {config.SLOT_LABELS_TH[slot]}")
        guide = config.SLOT_GUIDANCE_TH[slot]
        st.write(f"💡 {guide['text']}")
        st.caption(f"อ้างอิง: {guide['source']}")
        t = targets[slot]
        st.write(f"เป้าหมายช่วงนี้ประมาณ **{t['kcal']:,.0f} kcal** · โปรตีน {t['protein']:.0f} ก. · "
                 f"คาร์โบไฮเดรต {t['carb']:.0f} ก.")
        if slot == "post_2h":
            low, high = (user["weight_kg"] * f for f in config.POST_PROTEIN_G_PER_KG)
            st.write(f"โปรตีนหลังออกกำลังกายที่แนะนำ: {low:.0f}-{high:.0f} ก.")
        if window["note"]:
            st.info(window["note"])

        recs = rules.recommend(foods, slot, user, data.rules, t["kcal"], data.benefits)
        if not recs:
            st.warning("ยังไม่มีอาหารในฐานข้อมูลที่ผ่านเงื่อนไขของช่วงนี้")
        elif len(recs) < config.RECOMMEND_MIN:
            st.caption("มีอาหารที่เหมาะน้อยกว่า 3 รายการ ควรเพิ่มรายการอาหารในฐานข้อมูล")
        if recs:
            st.caption("☑️ ติ๊กเมนูที่กินแล้ว ระบบจะบันทึกลง “บันทึกอาหาร” ของวันนี้ให้อัตโนมัติ")
        msg = st.session_state.get("_saved_msg")
        for r in recs:
            key = f"eat_{today}_{slot}_{r['food_id']}"
            # Sync the box with the database every run (e.g. after deleting on the log page).
            st.session_state[key] = (slot, r["food_id"]) in saved
            st.checkbox(f"✨ {r['name_th']} · {r['qty']:g} × {r['serving_desc']} · "
                        f"{r['kcal']:.0f} kcal · โปรตีน {r['protein']:.0f} ก.",
                        key=key, on_change=toggle_saved, args=(key, slot, r))
            if msg and msg[:2] == (slot, r["food_id"]):
                st.markdown(f'<div class="saved-banner saved-{msg[3]}">{html.escape(msg[2])}</div>',
                            unsafe_allow_html=True)
                del st.session_state["_saved_msg"]
            with st.expander("📜 เหตุผลและประโยชน์"):
                st.write("**ทำไมจึงแนะนำ:** " + " · ".join(r["reasons"]))
                if r["benefit"]:
                    st.write(f"**ประโยชน์:** {r['benefit']} (สารอาหารเด่น: {r['key_nutrient']})")
                    st.caption(f"ที่มาของประโยชน์: {r['benefit_source']}")
                st.caption(f"ข้อมูลโภชนาการ: {r['source']} · ตรวจกฎแล้ว: "
                           f"{', '.join(r['checked_rules']) or 'ไม่มีกฎสำหรับช่วงนี้'} · "
                           f"แนวทาง: {r['guidance_source']}")

        if avoid[slot]:
            st.markdown("**ควรเลี่ยงในช่วงนี้:** " + " ".join(
                ui.chip(f"⚠ {f['name_th']} ({', '.join(w['rule_id'] for w in ws)})")
                for f, ws in avoid[slot]), unsafe_allow_html=True)

st.divider()
st.subheader("⚠️ อาหารที่ควรเลี่ยงตอนนี้")
# Default to the slot happening now, or the next one today.
now = datetime.now().strftime("%H:%M")
upcoming = [i for i, w in enumerate(times.values()) if w["end"] >= now]
slot_choice = st.selectbox("เลือกช่วงเวลา", list(times), index=upcoming[0] if upcoming else 0,
                           format_func=lambda s: f"{times[s]['start']} น. · {config.SLOT_LABELS_TH[s]}")
if not avoid[slot_choice]:
    st.success("ไม่พบอาหารในฐานข้อมูลที่ควรเลี่ยงในช่วงนี้")
for food, warnings in avoid[slot_choice]:
    with st.container(border=True):
        st.markdown(f"**⚠ {food['name_th']}**")
        for w in warnings:
            st.write(f"[{w['rule_id']}] ระดับ{config.SEVERITY_LABELS_TH.get(w['severity'], '')} — {w['reason']}")
            st.caption(f"เงื่อนไข: {w['condition']} · อ้างอิง: {w['reference']}")
ui.footer()
