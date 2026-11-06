"""Streamlit helpers shared by all pages (session, guards, styling, footer).

Kept separate from calc/rules so those stay pure and testable.
"""
from __future__ import annotations

import html

import streamlit as st

import config
from core import calc, db
from core.data_loader import Dataset, load_dataset

# Okabe-Ito colour-blind safe palette; colours are always paired with icons/text.
COLORS = {"blue": "#0072B2", "orange": "#E69F00", "vermillion": "#D55E00",
          "green": "#009E73", "grey": "#6B7280"}

CSS = """
<style>
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    min-height: 3rem; font-size: 1.05rem; width: 100%;
}
.chip { display:inline-block; padding:0.2rem 0.6rem; margin:0.15rem; border-radius:1rem;
        font-size:0.9rem; border:2px solid; }
.chip-avoid { border-color:#D55E00; color:#A63D00; background:#FDEBE1; }
.chip-ok { border-color:#0072B2; color:#00507D; background:#E3F0F9; }
.footer { font-size:0.8rem; color:#6B7280; border-top:1px solid #E5E7EB;
          margin-top:2rem; padding-top:0.6rem; }
</style>
"""


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
    st.markdown(CSS, unsafe_allow_html=True)


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
