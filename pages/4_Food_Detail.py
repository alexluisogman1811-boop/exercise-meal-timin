"""Food detail: search / filter, nutrients per 100 g and per serving, slot status."""
import pandas as pd
import streamlit as st

import config
from core import calc, rules, ui

ui.setup()
ui.log_view("food")
data = ui.get_dataset()
ui.show_data_banners(data)
st.title("📖 คลังข้อมูลอาหาร")

foods = data.foods
if foods.empty:
    st.warning("ยังไม่มีข้อมูลอาหาร")
    ui.footer()
    st.stop()

query = st.text_input("ค้นหาชื่ออาหาร", placeholder="เช่น ไก่ ข้าว นม")
c1, c2 = st.columns(2)
categories = c1.multiselect("หมวดอาหาร", sorted(foods["category"].unique()))
all_tags = sorted({t.strip() for tags in foods["tags"] for t in str(tags).split(";") if t.strip()})
tags = c2.multiselect("แท็ก", all_tags)

shown = foods
if query:
    shown = shown[shown["name_th"].str.contains(query, case=False, regex=False)]
if categories:
    shown = shown[shown["category"].isin(categories)]
if tags:
    shown = shown[shown["tags"].apply(lambda s: any(t in str(s).split(";") for t in tags))]

if shown.empty:
    st.info("ไม่พบอาหารที่ตรงกับการค้นหา")
    ui.footer()
    st.stop()

st.caption(f"พบ {len(shown)} รายการ")
food_id = st.selectbox("เลือกอาหาร", shown["food_id"].tolist(),
                       format_func=lambda i: shown.set_index("food_id").loc[i, "name_th"])
food = shown.set_index("food_id").loc[food_id].to_dict() | {"food_id": food_id}

st.subheader(food["name_th"])
grams = "" if "ก." in str(food["serving_desc"]) or "มล." in str(food["serving_desc"]) else f" ({food['serving_g']:g} ก.)"
st.caption(f"{food['category']} · {food['cooking']} · 1 หน่วยบริโภค = {food['serving_desc']}{grams}")
if food["needs_source_check"]:
    st.warning("ค่าพลังงานไม่สอดคล้องกับสารอาหารหลัก (ต่างเกิน 15%) — รอตรวจสอบแหล่งข้อมูล")

serving = calc.per_serving(food)
labels = {"kcal": "พลังงาน (kcal)", "protein": "โปรตีน (ก.)", "carb": "คาร์โบไฮเดรต (ก.)",
          "fat": "ไขมัน (ก.)", "fiber": "ใยอาหาร (ก.)", "sugar": "น้ำตาล (ก.)",
          "sodium_mg": "โซเดียม (มก.)"}
table = pd.DataFrame({
    "สารอาหาร": list(labels.values()),
    "ต่อ 100 ก.": [f"{food[calc.NUTRIENT_COLUMNS[k]]:g}" for k in labels],
    "ต่อ 1 หน่วยบริโภค": [f"{serving[k]:.1f}" for k in labels],
})
st.table(table.set_index("สารอาหาร"))

L = config.LEVEL_LABELS_TH
st.write(f"ไขมัน: **{L[food['fat_level']]}** · ใยอาหาร: **{L[food['fiber_level']]}** · "
         f"น้ำตาล: **{L[food['sugar_level']]}** · ย่อยง่าย: **{'ใช่' if food['easy_digest'] else 'ไม่'}**")
st.caption("เกณฑ์ระดับ: ดู config.py และ METHODS.md")

benefit = data.benefits.get(str(food_id))
if benefit:
    st.success(f"**ประโยชน์:** {benefit['benefit_text']} (สารอาหารเด่น: {benefit['key_nutrient']})")
    st.caption(f"ที่มา: {benefit.get('source', '')}")
st.caption(f"แหล่งข้อมูลโภชนาการ: {food['source'] or '— ไม่มี —'} ({food['source_date']})")

st.subheader("เหมาะกับช่วงเวลาไหน")
user = ui.current_user() if ui.user_id() else None
rows = []
for slot in config.SLOTS:
    warnings = rules.check_avoid(food, slot, user, data.rules)
    rows.append({
        "ช่วงเวลา": config.SLOT_LABELS_TH[slot],
        "สถานะ": "⚠ ควรเลี่ยง" if warnings else "✓ กินได้",
        "เหตุผล / กฎ": " | ".join(f"[{w['rule_id']}] {w['reason']}" for w in warnings) or "-",
    })
st.table(pd.DataFrame(rows).set_index("ช่วงเวลา"))
if not user:
    st.caption("ยังไม่ได้ตรวจการแพ้อาหาร เพราะยังไม่ได้กรอกข้อมูลส่วนตัว")
ui.footer()
