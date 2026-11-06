"""History and report: daily / weekly charts, adherence and CSV export."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import calc, db, ui

ui.setup()
user = ui.require_profile()
uid = user["user_id"]
ui.log_view("history")
st.title("📈 ประวัติและรายงาน")

summary = db.get_daily_summary(uid)
if summary.empty:
    st.info("ยังไม่มีข้อมูล เริ่มบันทึกอาหารก่อน แล้วกราฟจะแสดงที่นี่")
    ui.link("log", "ไปบันทึกอาหาร", "📝")
    ui.footer()
    st.stop()

needs = ui.needs_for(user)
summary["date"] = pd.to_datetime(summary["date"])
# Targets from the current profile (goal columns in the view may be empty for old rows).
summary["goal_kcal"] = summary["goal_kcal"].fillna(needs["target_kcal"])
summary["goal_protein"] = summary["goal_protein"].fillna(needs["protein_g"])

view = st.radio("มุมมอง", ["รายวัน", "รายสัปดาห์"], horizontal=True)
if view == "รายสัปดาห์":
    # Average per logged day within each week (week starting Monday).
    data = (summary.set_index("date")
            .resample("W-MON", label="left", closed="left")
            .mean(numeric_only=True).dropna(subset=["kcal_total"]).reset_index())
    x_title = "สัปดาห์ที่เริ่ม (ค่าเฉลี่ยต่อวัน)"
else:
    data = summary.tail(30)
    x_title = "วันที่"


def bar_vs_target(col: str, goal_col: str, title: str, unit: str) -> go.Figure:
    """Bar of intake with a dashed target line."""
    x = data["date"].dt.strftime("%d/%m/%Y")  # category axis: one bar per day/week
    fig = go.Figure()
    fig.add_bar(x=x, y=data[col], name="ที่กินจริง", marker_color=ui.COLORS["blue"])
    fig.add_scatter(x=x, y=data[goal_col], name="เป้าหมาย", mode="lines+markers",
                    line=dict(color=ui.COLORS["orange"], dash="dash", width=3))
    fig.update_xaxes(type="category")
    fig.update_layout(title=title, yaxis_title=unit, xaxis_title=x_title, height=320,
                      margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h", y=-0.3))
    return fig


st.plotly_chart(bar_vs_target("kcal_total", "goal_kcal", "พลังงาน", "kcal"), use_container_width=True)
st.plotly_chart(bar_vs_target("protein_total", "goal_protein", "โปรตีน", "กรัม"), use_container_width=True)

summary["kcal_adherence"] = [calc.kcal_adherence_pct(a, t) for a, t in zip(summary["kcal_total"], summary["goal_kcal"])]
summary["protein_adherence"] = [calc.protein_adherence_pct(a, t) for a, t in zip(summary["protein_total"], summary["goal_protein"])]
c1, c2, c3 = st.columns(3)
c1.metric("จำนวนวันที่บันทึก", f"{len(summary)} วัน")
c2.metric("ความใกล้เป้าพลังงาน (เฉลี่ย)", f"{summary['kcal_adherence'].mean():.0f}%")
c3.metric("โปรตีนถึงเป้า (เฉลี่ย)", f"{summary['protein_adherence'].mean():.0f}%")
st.caption("ความใกล้เป้าพลังงาน = 100% − ระยะห่างจากเป้าเป็น %; โปรตีนถึงเป้า = กินได้ / เป้า (สูงสุด 100%)")

st.subheader("ส่งออกข้อมูลของฉัน")
logs = db.get_food_logs(uid)
c4, c5 = st.columns(2)
c4.download_button("⬇️ สรุปรายวัน (CSV)", summary.to_csv(index=False).encode("utf-8-sig"),
                   file_name=f"daily_summary_{uid}.csv", mime="text/csv")
c5.download_button("⬇️ บันทึกอาหารทั้งหมด (CSV)", logs.to_csv(index=False).encode("utf-8-sig"),
                   file_name=f"food_logs_{uid}.csv", mime="text/csv")
ui.footer()
