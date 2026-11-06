"""Streamlit helpers shared by all pages (session, guards, styling, footer).

Kept separate from calc/rules so those stay pure and testable.
"""
from __future__ import annotations

import html
from datetime import date

import streamlit as st

import config
from core import calc, db, theme
from core.data_loader import Dataset, load_dataset

# The sidebar menu is a quest checklist: (page key, Thai label) in suggested order.
QUESTS = [
    ("home", "ยินยอมเข้าร่วม"),
    ("profile", "กรอกข้อมูลส่วนตัว"),
    ("needs", "ดูพลังงานที่ต้องการ"),
    ("plan", "ดูแผนมื้ออาหารตามเวลา"),
    ("food", "สำรวจคลังอาหาร"),
    ("log", "บันทึกอาหารวันนี้"),
    ("history", "ดูรายงานย้อนหลัง"),
    ("feedback", "ทำแบบประเมิน"),
]


# Original rock-style taglines shown under each page title, with the Thai meaning.
SPELLS = {
    "home": ("Rise from the static.", "ลุกขึ้นมา เริ่มต้นใหม่ไปด้วยกัน"),
    "profile": ("Know your own pulse.", "รู้จักร่างกายของตัวเอง"),
    "needs": ("Fuel the fire within.", "เติมพลังให้ไฟในตัวคุณ"),
    "plan": ("Every hour has its anthem.", "ทุกช่วงเวลามีมื้อที่ใช่"),
    "food": ("Choose your armor.", "เลือกอาหารเป็นเกราะของคุณ"),
    "log": ("Write it in ink.", "จดทุกมื้อให้ชัดเจน"),
    "history": ("Look back, march forward.", "มองย้อนกลับ แล้วเดินหน้าต่อ"),
    "feedback": ("Let your voice be loud.", "บอกเราให้ดังที่สุด"),
    "admin": ("Behind the curtain.", "หลังเวทีของผู้ดูแล"),
}


def spell(page: str) -> None:
    """Typewriter tagline under a page title."""
    words, meaning = SPELLS[page]
    st.markdown(f'<div class="spell">🎸 {html.escape(words)}<small>— {html.escape(meaning)}</small></div>',
                unsafe_allow_html=True)


def is_dark() -> bool:
    """True when the night (dark) mode toggle is on."""
    return bool(st.session_state.get("dark_mode", True))


def series_colors() -> list[str]:
    """Three chart colours for the current mode."""
    return theme.SERIES["dark" if is_dark() else "light"]


def style_chart(fig) -> None:
    """Apply the current mode's fonts and colours to a Plotly figure."""
    fig.update_layout(**theme.chart_layout(is_dark()))


@st.cache_resource
def _init_db_once() -> bool:
    """Create the database tables once per server process."""
    db.init_db()
    return True


@st.cache_data(show_spinner="กำลังโหลดข้อมูลอาหาร...")
def get_dataset() -> Dataset:
    """Cached food / rules / benefits data."""
    return load_dataset()


def setup() -> None:
    """Call at the top of every page render: DB, CSS, data banners."""
    _init_db_once()
    st.markdown(theme.css(is_dark()), unsafe_allow_html=True)


def quest_status(user: dict | None) -> dict[str, bool]:
    """Which checklist steps the current user has completed."""
    uid = user_id()
    if not uid:
        return {key: False for key, _ in QUESTS}
    progress = db.user_progress(uid, date.today().isoformat())
    progress["home"] = True
    progress["profile"] = has_profile(user)
    return progress


def render_menu(pages: dict) -> None:
    """Sidebar: brand, day/night toggle and the quest checklist used as the menu."""
    with st.sidebar:
        st.markdown('<div class="brand">🥀 บันทึกพลังสายร็อก</div>', unsafe_allow_html=True)
        st.toggle("🖤 โหมดเวทีมืด", key="dark_mode", value=is_dark())
        done = quest_status(current_user())
        count = sum(done[key] for key, _ in QUESTS)
        st.markdown('<div class="quest-title">🎸 เซ็ตลิสต์ภารกิจ</div>', unsafe_allow_html=True)
        st.progress(count / len(QUESTS), text=f"สำเร็จแล้ว {count}/{len(QUESTS)} ภารกิจ")
        for i, (key, label) in enumerate(QUESTS, start=1):
            st.page_link(pages[key], label=f"{i}. {label}", icon="✅" if done[key] else "⬜")
        st.divider()
        st.page_link(pages["admin"], label="ห้องผู้ดูแล", icon="🗝️")
        if user_id():
            st.caption(f"รหัสผู้ใช้: {user_id()}")
        st.caption("⚕️ ไม่ใช่เครื่องมือวินิจฉัยหรือรักษาโรค")


def show_data_banners(dataset: Dataset) -> None:
    """Demo banner and data errors (never crash on bad data)."""
    if dataset.is_demo:
        st.warning("⚠️ ข้อมูลตัวอย่าง ไม่ใช่ค่าจริง (DEMO) — ยังไม่ได้นำเข้าฐานข้อมูลอาหารจริง")
    if dataset.errors:
        with st.expander(f"พบปัญหาในข้อมูล {len(dataset.errors)} รายการ (แสดงรายละเอียด)"):
            for err in dataset.errors:
                st.write("• " + err)


def user_id() -> str | None:
    """Current random user id from the session, if consent was given."""
    return st.session_state.get("user_id")


def current_user() -> dict | None:
    """The current user row, or None."""
    uid = user_id()
    return db.get_user(uid) if uid else None


def has_profile(user: dict | None) -> bool:
    """True when the body data needed for calculations is filled in."""
    return bool(user) and all(user.get(k) for k in ("sex", "age", "weight_kg", "height_cm",
                                                    "activity_level", "goal", "start_time"))


def link(name: str, label: str, icon: str | None = None) -> None:
    """Link to a page registered by app.py (works for the home function page too)."""
    page = st.session_state.get("_pages", {}).get(name)
    if page is not None:
        st.page_link(page, label=label, icon=icon)


def require_consent() -> str:
    """Stop the page unless the user accepted the consent on the home page."""
    uid = user_id()
    if not uid:
        st.info("กรุณาอ่านข้อตกลงและกดยินยอมที่หน้าแรกก่อนใช้งาน")
        link("home", "ไปหน้าแรก", "🏠")
        footer()
        st.stop()
    return uid


def require_profile() -> dict:
    """Stop the page unless consent and a complete profile exist."""
    require_consent()
    user = current_user()
    if not has_profile(user):
        st.info("กรุณากรอกข้อมูลส่วนตัวก่อน แล้วระบบจะคำนวณให้อัตโนมัติ")
        link("profile", "ไปกรอกข้อมูลส่วนตัว", "👤")
        footer()
        st.stop()
    return user  # type: ignore[return-value]


def log_view(page: str) -> None:
    """Log a page view once per visit (not on every Streamlit rerun)."""
    if st.session_state.get("_last_page") != page:
        st.session_state["_last_page"] = page
        db.log_usage(user_id(), page, "view")


def log_action(page: str, action: str) -> None:
    """Log a key action (calc, add_log, view_plan, ...)."""
    db.log_usage(user_id(), page, action)


def needs_for(user: dict) -> dict:
    """Daily needs for a stored user profile."""
    return calc.compute_needs(user)


def chip(text: str, kind: str = "avoid") -> str:
    """HTML for a small labelled chip (kind: avoid / ok)."""
    return f'<span class="chip chip-{kind}">{html.escape(text)}</span>'


def footer() -> None:
    """Disclaimer footer shown on every page."""
    st.markdown(f'<div class="footer">⚕️ {html.escape(config.DISCLAIMER_TH)}</div>',
                unsafe_allow_html=True)
