"""Feedback: System Usability Scale (Thai), satisfaction and comment."""
import streamlit as st

from core import calc, db, ui

ui.setup()
uid = ui.require_consent()
ui.log_view("feedback")
st.title("🎤 แบบประเมินการใช้งาน")
ui.spell("feedback")
st.caption("1 = ไม่เห็นด้วยอย่างยิ่ง · 5 = เห็นด้วยอย่างยิ่ง")

# Standard SUS items (Brooke 1996), Thai wording. Odd = positive, even = negative.
SUS_ITEMS = [
    "ฉันคิดว่าฉันอยากใช้ระบบนี้บ่อย ๆ",
    "ฉันคิดว่าระบบนี้ซับซ้อนเกินความจำเป็น",
    "ฉันคิดว่าระบบนี้ใช้งานง่าย",
    "ฉันคิดว่าต้องมีผู้เชี่ยวชาญช่วย ฉันจึงจะใช้ระบบนี้ได้",
    "ฉันคิดว่าฟังก์ชันต่าง ๆ ในระบบนี้ทำงานเข้ากันได้ดี",
    "ฉันคิดว่าระบบนี้มีความไม่สอดคล้องกันมากเกินไป",
    "ฉันคิดว่าคนส่วนใหญ่จะเรียนรู้วิธีใช้ระบบนี้ได้อย่างรวดเร็ว",
    "ฉันคิดว่าระบบนี้ใช้งานยุ่งยากมาก",
    "ฉันรู้สึกมั่นใจมากเมื่อใช้ระบบนี้",
    "ฉันต้องเรียนรู้หลายอย่างก่อนจึงจะเริ่มใช้ระบบนี้ได้",
]
SATISFACTION_ITEMS = {
    "ease": "ความง่ายในการใช้งาน",
    "usefulness": "ความเป็นประโยชน์ของคำแนะนำอาหาร",
    "warnings": "ความชัดเจนของคำเตือนอาหารที่ควรเลี่ยง",
    "design": "ความสวยงามและการจัดหน้าจอ",
    "overall": "ความพึงพอใจโดยรวม",
}
SCALE = [1, 2, 3, 4, 5]

with st.form("sus"):
    st.subheader("ส่วนที่ 1: ความง่ายในการใช้งาน (SUS)")
    answers = [st.radio(f"{i}. {text}", SCALE, index=None, horizontal=True, key=f"sus{i}")
               for i, text in enumerate(SUS_ITEMS, start=1)]
    st.subheader("ส่วนที่ 2: ความพึงพอใจ (1 = น้อยที่สุด · 5 = มากที่สุด)")
    satisfaction = {key: st.radio(text, SCALE, index=None, horizontal=True, key=f"sat_{key}")
                    for key, text in SATISFACTION_ITEMS.items()}
    comment = st.text_area("ข้อเสนอแนะเพิ่มเติม (ไม่บังคับ)", max_chars=1000)
    sent = st.form_submit_button("ส่งแบบประเมิน", type="primary")

if sent:
    if None in answers or None in satisfaction.values():
        st.error("กรุณาตอบให้ครบทุกข้อ")
    else:
        score = calc.sus_score(answers)
        db.save_feedback(uid, answers, score, satisfaction, comment.strip())
        ui.log_action("feedback", "submit_sus")
        st.success(f"ขอบคุณที่ช่วยประเมิน! คะแนน SUS ของคุณ = {score:.1f} / 100")
        st.caption("คะแนนเฉลี่ยทั่วไปของ SUS อยู่ที่ประมาณ 68 (Sauro 2011)")
ui.footer()
