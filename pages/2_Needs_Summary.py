"""Needs summary: BMR, TDEE, targets, macro donut and plain explanations."""
import plotly.graph_objects as go
import streamlit as st

import config
from core import ui

ui.setup()
user = ui.require_profile()
ui.log_view("needs")
needs = ui.needs_for(user)
e = config.ENERGY_PER_G

st.title("⚡ ความต้องการพลังงานและสารอาหาร")
ui.spell("needs")
st.caption(f"เป้าหมาย: {config.GOAL_LABELS_TH[user['goal']]} · "
           f"กิจกรรม: {config.ACTIVITY_LABELS_TH[user['activity_level']]}")

c1, c2, c3 = st.columns(3)
c1.metric("BMR", f"{needs['bmr']:,.0f} kcal")
c2.metric("TDEE", f"{needs['tdee']:,.0f} kcal")
c3.metric("พลังงานเป้าหมาย", f"{needs['target_kcal']:,.0f} kcal")
c4, c5, c6, c7 = st.columns(4)
c4.metric("โปรตีน", f"{needs['protein_g']:.0f} ก.")
c5.metric("คาร์โบไฮเดรต", f"{needs['carb_g']:.0f} ก.")
c6.metric("ไขมัน", f"{needs['fat_g']:.0f} ก.")
c7.metric("น้ำ", f"{needs['water_ml_low'] / 1000:.1f}-{needs['water_ml_high'] / 1000:.1f} ล.")

for note in needs["notes"]:
    st.info(note)

energy = {
    "โปรตีน": needs["protein_g"] * e["protein"],
    "คาร์โบไฮเดรต": needs["carb_g"] * e["carb"],
    "ไขมัน": needs["fat_g"] * e["fat"],
}
fig = go.Figure(go.Pie(
    labels=list(energy), values=list(energy.values()), hole=0.55, sort=False,
    marker=dict(colors=ui.series_colors(),
                line=dict(color="white", width=2)),
    textinfo="label+percent", insidetextorientation="horizontal", hovertemplate="%{label}: %{value:.0f} kcal<extra></extra>"))
fig.update_layout(title="สัดส่วนพลังงานจากสารอาหารหลัก", showlegend=False,
                  margin=dict(l=10, r=10, t=50, b=10), height=340,
                  annotations=[dict(text=f"{needs['target_kcal']:,.0f}<br>kcal", showarrow=False,
                                    font_size=18)])
ui.style_chart(fig)
st.plotly_chart(fig, width="stretch")

st.subheader("ตัวเลขเหล่านี้หมายความว่าอะไร")
carb_low, carb_high = config.CARB_G_PER_KG_RANGE
if user["activity_level"] == "very_heavy":
    carb_high = config.CARB_G_PER_KG_MAX_VERY_HEAVY
st.markdown(f"""
- **BMR (พลังงานพื้นฐาน)** คือพลังงานที่ร่างกายใช้ขณะพักเฉย ๆ เช่น หายใจ หัวใจเต้น
  คำนวณด้วยสูตร Mifflin-St Jeor จากเพศ อายุ น้ำหนัก และส่วนสูง
- **TDEE (พลังงานที่ใช้ทั้งวัน)** = BMR × ตัวคูณกิจกรรม
  {config.ACTIVITY_FACTORS[user['activity_level']]}
- **พลังงานเป้าหมาย** = TDEE × {config.GOAL_FACTORS[user['goal']]:g} ตามเป้าหมาย
  "{config.GOAL_LABELS_TH[user['goal']]}" (ถ้าลดไขมัน จะไม่ต่ำกว่า BMR)
- **โปรตีน** {config.PROTEIN_G_PER_KG[user['goal']]:g} ก. ต่อน้ำหนักตัว 1 กก.
  ช่วยซ่อมแซมและสร้างกล้ามเนื้อ
- **ไขมัน** {needs['fat_pct']:.0%} ของพลังงานเป้าหมาย (ช่วงที่แนะนำ 20-35%)
- **คาร์โบไฮเดรต** คือพลังงานที่เหลือ = {needs['carb_g_per_kg']:.1f} ก./กก.
  (ช่วงอ้างอิงสำหรับคนออกกำลังกาย {carb_low:g}-{carb_high:g} ก./กก.)
- **น้ำ** 30-40 มล. ต่อน้ำหนักตัว 1 กก. เป็นแนวทางเบื้องต้นเท่านั้น
  วันที่อากาศร้อนหรือเหงื่อออกมากควรดื่มเพิ่ม
""")
st.caption("ค่าทั้งหมดเป็นค่าประมาณเพื่อการเรียนรู้ ดูสูตรและแหล่งอ้างอิงได้ในเอกสาร METHODS.md")
ui.link("plan", "ดูแผนมื้ออาหารตามเวลา", "🕒")
ui.footer()
