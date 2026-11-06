"""Entry point: page navigation (Thai titles) + the home page.

Run with:  streamlit run app.py
"""
import streamlit as st

import config
from core import db, ui

st.set_page_config(page_title="วางแผนมื้ออาหารตามเวลาออกกำลังกาย", page_icon="🍱",
                   layout="centered")


def delete_my_data_box(uid: str) -> None:
    """'Delete my data' with a confirmation checkbox."""
    with st.expander("🗑️ ลบข้อมูลของฉัน"):
        st.write("ระบบจะลบโปรไฟล์ บันทึกอาหาร ประวัติการใช้งาน และแบบประเมินของคุณทั้งหมด และกู้คืนไม่ได้")
        sure = st.checkbox("ฉันต้องการลบข้อมูลทั้งหมดของฉัน", key="confirm_delete")
        if st.button("ลบข้อมูลถาวร", disabled=not sure):
            db.delete_user_data(uid)
            for key in ("user_id", "_last_page"):
                st.session_state.pop(key, None)
            st.success("ลบข้อมูลเรียบร้อยแล้ว")
            st.rerun()


def home() -> None:
    """Purpose, how to use, disclaimer and consent."""
    ui.setup()
    ui.log_view("home")
    st.title("🌌 ตำราเวทแห่งดวงดาว")
    ui.spell("home")
    st.markdown("#### วางแผนมื้ออาหารตามเวลาออกกำลังกาย")
    st.write("ยินดีต้อนรับนักเวทสายฟิตสู่จักรวาลแห่งโภชนาการ! ตำราแห่งดวงดาวเล่มนี้จะแนะนำอาหารไทยที่เหมาะกับแต่ละช่วงเวลา "
             "ก่อน ระหว่าง และหลังออกกำลังกาย เตือนอาหารที่ควรเลี่ยง "
             "และคำนวณพลังงานกับสารอาหารที่ร่างกายต้องการ")

    with st.container(border=True):
        st.subheader("📜 วิธีใช้ตำรา")
        st.markdown(
            "1. อ่านข้อตกลงและกดยินยอม\n"
            "2. กรอก **ข้อมูลส่วนตัว** (ใช้ชื่อเล่น ไม่ต้องใช้ชื่อจริง)\n"
            "3. ดู **ความต้องการพลังงาน** และ **แผนมื้ออาหารตามเวลา**\n"
            "4. **บันทึกอาหาร** ที่กินจริง แล้วดู **รายงาน** ย้อนหลัง\n"
            "5. ช่วยตอบ **แบบประเมินความพึงพอใจ** เมื่อใช้งานเสร็จ")

    st.error("⚕️ **ข้อควรทราบ:** " + config.DISCLAIMER_TH, icon=None)

    uid = ui.user_id()
    if uid:
        st.success(f"คุณยินยอมแล้ว รหัสผู้ใช้ของคุณคือ **{uid}** (จดไว้เพื่อกลับมาใช้ต่อ)")
        ui.link("profile", "ไปกรอกข้อมูลส่วนตัว", "👤")
        delete_my_data_box(uid)
        ui.footer()
        return

    st.subheader("คัดกรองและขอความยินยอม")
    excluded = st.radio(
        "คุณมีข้อใดข้อหนึ่งต่อไปนี้หรือไม่: โรคประจำตัว, ตั้งครรภ์หรือให้นมบุตร, "
        "เป็นนักกีฬาอาชีพ, มีภาวะการกินผิดปกติ",
        ["ไม่มี", "มี"], index=None, horizontal=True)
    if excluded == "มี":
        st.warning("ขออภัย แอปนี้ออกแบบสำหรับผู้มีสุขภาพดีทั่วไปเท่านั้น "
                   "กรุณาปรึกษาแพทย์หรือนักกำหนดอาหารเพื่อรับคำแนะนำที่เหมาะกับคุณ")
        ui.footer()
        return

    age_group = st.radio("ช่วงอายุของคุณ", ["18-45 ปี", "15-17 ปี"], index=None, horizontal=True)
    guardian = False
    if age_group == "15-17 ปี":
        guardian = st.checkbox("ผู้ปกครองของฉันรับทราบและยินยอมให้เข้าร่วมการวิจัยนี้แล้ว")
    consent = st.checkbox(
        "ฉันได้อ่านข้อควรทราบแล้ว และยินยอมให้เก็บข้อมูลแบบไม่ระบุตัวตน "
        "(ชื่อเล่นและรหัสสุ่ม) เพื่อใช้ในงานวิจัยเท่านั้น")
    ready = (excluded == "ไม่มี" and age_group is not None and consent
             and (age_group == "18-45 ปี" or guardian))
    if st.button("ยินยอมและเริ่มใช้งาน", type="primary", disabled=not ready):
        new_id = db.new_user_id()
        db.create_user(new_id, guardian_consent=guardian)
        st.session_state["user_id"] = new_id
        ui.log_action("home", "consent")
        st.rerun()

    with st.expander("เคยใช้งานแล้ว? กรอกรหัสผู้ใช้เพื่อใช้ต่อ"):
        old_id = st.text_input("รหัสผู้ใช้ (8 ตัวอักษร)", max_chars=8).strip().lower()
        if st.button("ใช้รหัสนี้"):
            if old_id and db.get_user(old_id):
                st.session_state["user_id"] = old_id
                st.rerun()
            else:
                st.error("ไม่พบรหัสผู้ใช้นี้ กรุณาตรวจสอบอีกครั้ง")
    ui.footer()


pages = {
    "home": st.Page(home, title="หน้าแรก", icon="🌌", default=True),
    "profile": st.Page("pages/1_Profile.py", title="ข้อมูลส่วนตัว", icon="🧙"),
    "needs": st.Page("pages/2_Needs_Summary.py", title="ความต้องการพลังงาน", icon="⚗️"),
    "plan": st.Page("pages/3_Meal_Plan.py", title="แผนมื้ออาหารตามเวลา", icon="🌠"),
    "food": st.Page("pages/4_Food_Detail.py", title="ข้อมูลอาหาร", icon="🪐"),
    "log": st.Page("pages/5_Food_Log.py", title="บันทึกอาหาร", icon="✒️"),
    "history": st.Page("pages/6_History_Report.py", title="ประวัติและรายงาน", icon="🔭"),
    "feedback": st.Page("pages/7_Feedback_SUS.py", title="แบบประเมิน", icon="🦉"),
    "admin": st.Page("pages/8_Admin.py", title="ผู้ดูแลระบบ", icon="🗝️"),
}
st.session_state["_pages"] = pages

# The built-in menu is hidden; the quest checklist in the sidebar replaces it.
nav = st.navigation(list(pages.values()), position="hidden")
# Log the view before drawing the checklist so the current page is ticked at once.
current = next(k for k, p in pages.items() if p.url_path == nav.url_path)
if current != "admin":
    ui.log_view(current)
ui.render_menu(pages)
nav.run()
