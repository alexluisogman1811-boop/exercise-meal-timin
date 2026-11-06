"""Meal plan by time: timeline of slots, recommendations and avoid warnings."""
from datetime import datetime

import streamlit as st

import config
from core import calc, rules, ui

ui.setup()
user = ui.require_profile()
ui.log_view("plan")
data = ui.get_dataset()
ui.show_data_banners(data)

st.title("🕒 แผนมื้ออาหารตามเวลา")
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
        for r in recs:
            with st.expander(f"✅ {r['name_th']} · {r['qty']:g} × {r['serving_desc']} · "
                             f"{r['kcal']:.0f} kcal · โปรตีน {r['protein']:.0f} ก."):
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
