"""Food log: add / edit / delete entries and compare the day with targets."""
from datetime import date, datetime

import streamlit as st

import config
from core import calc, db, rules, ui

ui.setup()
user = ui.require_profile()
uid = user["user_id"]
ui.log_view("log")
data = ui.get_dataset()
ui.show_data_banners(data)
st.title("✒️ บันทึกอาหาร")
ui.spell("log")

foods = data.foods.set_index("food_id") if not data.foods.empty else None
if foods is None:
    st.warning("ยังไม่มีข้อมูลอาหารให้เลือก")
    ui.footer()
    st.stop()

day = st.date_input("วันที่", value=date.today(), max_value=date.today(), format="DD/MM/YYYY")
day_text = day.isoformat()


def food_name(food_id: str) -> str:
    """Thai name of a food id (or the id if it was removed from the CSV)."""
    return foods.loc[food_id, "name_th"] if food_id in foods.index else f"{food_id} (ไม่มีในฐานข้อมูลแล้ว)"


with st.form("add_log", clear_on_submit=True):
    slot = st.selectbox("ช่วงเวลา", config.SLOTS, format_func=config.SLOT_LABELS_TH.get)
    food_id = st.selectbox("อาหาร", foods.index.tolist(),
                           format_func=lambda i: f"{foods.loc[i, 'name_th']} · {foods.loc[i, 'serving_desc']}")
    qty = st.number_input("จำนวนหน่วยบริโภค", min_value=0.5, max_value=10.0, value=1.0, step=0.5)
    if st.form_submit_button("➕ เพิ่มรายการ", type="primary"):
        food = foods.loc[food_id].to_dict() | {"food_id": food_id}
        now = datetime.now().strftime("%H:%M:%S")
        db.add_food_log(uid, food_id, qty, f"{day_text}T{now}", slot, calc.per_serving(food, qty))
        ui.log_action("log", "add_log")
        ui.flash(("success", f"บันทึก {food['name_th']} แล้ว"),
                 *[("warning", f"⚠ [{w['rule_id']}] {w['reason']}")
                   for w in rules.check_avoid(food, slot, user, data.rules)])
ui.show_flash()

logs = db.get_food_logs(uid, day_text)
needs = ui.needs_for(user)
totals = logs[["kcal", "protein_g", "carb_g", "fat_g"]].sum() if not logs.empty else None

st.subheader("รวมทั้งวันเทียบกับเป้าหมาย")
bars = [("พลังงาน", "kcal", needs["target_kcal"], "kcal"),
        ("โปรตีน", "protein_g", needs["protein_g"], "ก."),
        ("คาร์โบไฮเดรต", "carb_g", needs["carb_g"], "ก."),
        ("ไขมัน", "fat_g", needs["fat_g"], "ก.")]
for label, col, target, unit in bars:
    value = float(totals[col]) if totals is not None else 0.0
    ratio = value / target if target > 0 else 0
    flag = " (เกินเป้า)" if ratio > 1.1 else ""
    st.progress(min(ratio, 1.0), text=f"{label}: {value:,.0f} / {target:,.0f} {unit} ({ratio:.0%}){flag}")

st.subheader("รายการของวันนี้")
if logs.empty:
    st.info("ยังไม่มีรายการในวันนี้ เริ่มเพิ่มอาหารจากแบบฟอร์มด้านบน")
for row in logs.itertuples():
    with st.expander(f"{config.SLOT_LABELS_TH.get(row.slot, row.slot)} · {food_name(row.food_id)} × "
                     f"{row.qty:g} · {row.kcal:.0f} kcal"):
        c1, c2 = st.columns(2)
        new_qty = c1.number_input("จำนวน", 0.5, 10.0, float(row.qty), 0.5, key=f"qty_{row.log_id}")
        new_slot = c2.selectbox("ช่วงเวลา", config.SLOTS, index=config.SLOTS.index(row.slot)
                                if row.slot in config.SLOTS else 0,
                                format_func=config.SLOT_LABELS_TH.get, key=f"slot_{row.log_id}")
        b1, b2 = st.columns(2)
        if b1.button("💾 บันทึกการแก้ไข", key=f"save_{row.log_id}", disabled=row.food_id not in foods.index):
            food = foods.loc[row.food_id].to_dict()
            db.update_food_log(row.log_id, uid, new_qty, new_slot, calc.per_serving(food, new_qty))
            ui.log_action("log", "edit_log")
            st.rerun()
        if b2.button("🗑️ ลบ", key=f"del_{row.log_id}"):
            db.delete_food_log(row.log_id, uid)
            ui.log_action("log", "delete_log")
            st.rerun()
ui.footer()
