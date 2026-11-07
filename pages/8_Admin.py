"""Admin: data checks, ignored rules, usage summary and research data export.

The password is read from st.secrets["admin_password"] (never stored in code).
"""
import hmac
import io
import zipfile

import pandas as pd
import streamlit as st

import config
from core import db, ui
from core.data_loader import review_status

ui.setup()
st.title("🗝️ ผู้ดูแลระบบ")
ui.spell("admin")


def admin_password() -> str | None:
    """Password from .streamlit/secrets.toml or the Cloud secrets box."""
    try:
        return st.secrets.get("admin_password")
    except Exception:  # no secrets file at all
        return None


expected = admin_password()
if not expected:
    st.warning("ยังไม่ได้ตั้งรหัสผู้ดูแล ให้เพิ่ม admin_password ใน .streamlit/secrets.toml "
               "(ดูตัวอย่างใน .streamlit/secrets.toml.example)")
    ui.footer()
    st.stop()

if not st.session_state.get("is_admin"):
    pw = st.text_input("รหัสผ่านผู้ดูแล", type="password")
    if st.button("เข้าสู่ระบบ"):
        if hmac.compare_digest(pw.encode(), str(expected).encode()):
            st.session_state["is_admin"] = True
            st.rerun()
        st.error("รหัสผ่านไม่ถูกต้อง")
    ui.footer()
    st.stop()

data = ui.get_dataset()
if st.button("🔄 โหลดไฟล์ข้อมูลใหม่ (หลังแก้ CSV)"):
    ui.get_dataset.clear()
    st.rerun()

tab_data, tab_rules, tab_review, tab_usage, tab_export = st.tabs(
    ["ข้อมูลอาหาร", "กฎ", "การตรวจรับรอง", "การใช้งาน", "ส่งออกข้อมูล"])

with tab_review:
    review = review_status(data)
    done = int(review["ตรวจแล้ว"].sum())
    st.metric("ครูตรวจรับรองแล้ว", f"{done} / {len(review)} รายการ")
    st.progress(done / len(review) if len(review) else 0.0)
    st.caption("วิธีบันทึกผลตรวจ: ให้ครูกรอกชื่อในคอลัมน์ reviewer และวันที่ตรวจ (YYYY-MM-DD) ในคอลัมน์ "
               "review_date ของไฟล์ data/foods.csv และ data/meal_timing_rules.csv แล้วกด “โหลดไฟล์ข้อมูลใหม่”")
    shown = review.assign(ตรวจแล้ว=review["ตรวจแล้ว"].map({True: "✅ ตรวจแล้ว", False: "⏳ รอตรวจ"}))
    st.dataframe(shown, hide_index=True)
    st.download_button("⬇️ หลักฐานการตรวจรับรอง (CSV สำหรับภาคผนวก)",
                       shown.to_csv(index=False).encode("utf-8-sig"),
                       file_name="teacher_review_evidence.csv", mime="text/csv")

with tab_data:
    st.write(f"อาหารที่ใช้ได้: **{len(data.foods)}** รายการ" + (" (DEMO)" if data.is_demo else ""))
    if data.errors:
        st.error("ปัญหาที่พบในข้อมูล")
        for err in data.errors:
            st.write("• " + err)
    else:
        st.success("ไม่พบปัญหาในโครงสร้างข้อมูล")
    st.subheader("ต้องตรวจสอบแหล่งข้อมูล (needs source check)")
    st.caption(f"|4P+4C+9F − kcal| / kcal > {config.KCAL_CHECK_TOLERANCE:.0%}")
    flagged = data.flagged_foods
    if flagged.empty:
        st.write("ไม่มี")
    else:
        st.dataframe(flagged[["food_id", "name_th", "kcal_100g", "protein_100g", "carb_100g",
                              "fat_100g", "kcal_gap", "source"]], hide_index=True)

with tab_rules:
    st.subheader("กฎที่ไม่ถูกบังคับใช้")
    if data.ignored_rules:
        st.warning("กฎต่อไปนี้ถูกข้าม (ไม่มีแหล่งอ้างอิง หรืออ่านเงื่อนไขไม่ได้)")
        st.dataframe(pd.DataFrame(data.ignored_rules), hide_index=True)
    else:
        st.success("บังคับใช้ทุกกฎ")
    st.subheader("กฎทั้งหมด")
    st.dataframe(pd.DataFrame([{
        "rule_id": r["rule_id"], "กลุ่ม": r["group"], "ช่วงเวลา": ", ".join(r["slot_list"]),
        "เงื่อนไข (ข้อความ)": r["condition"], "condition_expr": r.get("condition_expr", ""),
        "ข้อยกเว้น": r.get("except_expr", ""), "บังคับใช้": "ใช่" if r["enforced"] else "ไม่",
        "ผู้ตรวจ": r["reviewer"],
    } for r in data.rules]), hide_index=True)

with tab_usage:
    sessions = db.session_lengths()
    users = db.export_table("users")
    c1, c2, c3 = st.columns(3)
    c1.metric("ผู้ใช้", len(users))
    c2.metric("จำนวนเซสชัน", len(sessions))
    c3.metric("เวลาใช้งานเฉลี่ย", f"{sessions['minutes'].mean():.1f} นาที" if len(sessions) else "-")
    usage = db.export_table("usage_logs")
    if not usage.empty:
        st.bar_chart(usage.groupby("page").size().rename("จำนวนครั้ง"))
    feedback = db.export_table("feedback")
    if not feedback.empty:
        st.metric("คะแนน SUS เฉลี่ย", f"{feedback['sus_score'].mean():.1f} (n={len(feedback)})")

with tab_export:
    st.write("ไฟล์ CSV ใช้ UTF-8 เปิดใน Excel ได้ภาษาไทยถูกต้อง")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for table in db.EXPORT_TABLES:
            df = db.export_table(table)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            zf.writestr(f"{table}.csv", csv)
            st.download_button(f"⬇️ {table}.csv ({len(df)} แถว)", csv,
                               file_name=f"{table}.csv", mime="text/csv", key=f"dl_{table}")
        zf.writestr("session_lengths.csv", db.session_lengths().to_csv(index=False).encode("utf-8-sig"))
    st.download_button("⬇️ ดาวน์โหลดทั้งหมด (ZIP)", buffer.getvalue(),
                       file_name="research_data.zip", mime="application/zip", type="primary")
ui.footer()
