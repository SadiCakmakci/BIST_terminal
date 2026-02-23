"""
ui.py
─────
All Streamlit rendering lives here.
This module is the ONLY place that calls st.* functions.

Data processing is delegated to:
  data_loader.py, classifier.py, period_filter.py, formatters.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from translations import get_t
from data_loader import load_file, get_sheet_names, LoadResult
from classifier import (
    StatementType,
    classify_dataframe,
    classification_summary,
    has_mixed_statements,
)
from period_filter import PeriodType, filter_columns
from formatters import format_dataframe

# ─────────────────────────────────────────────────────────────────────────────
# CSS — dark, refined terminal aesthetic
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; }

/* ── Base ────────────────────────────────────────────────────────────── */
.stApp {
    background: #080c12;
    color: #c9d1e0;
}

/* ── Top bar / header strip ──────────────────────────────────────────── */
.fin-header {
    background: linear-gradient(90deg, #0d1117 0%, #131b28 100%);
    border-bottom: 1px solid #1e2d40;
    padding: 1.1rem 1.6rem 0.9rem;
    margin-bottom: 0;
}
.fin-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.35rem;
    font-weight: 600;
    color: #58a6ff;
    letter-spacing: -0.3px;
    margin: 0;
}
.fin-tagline {
    font-size: 0.78rem;
    color: #4a5568;
    margin: 0.15rem 0 0;
    font-weight: 300;
    letter-spacing: 0.3px;
}

/* ── Control strip (row below header) ────────────────────────────────── */
.control-strip {
    background: #0d1117;
    border-bottom: 1px solid #1a2535;
    padding: 0.7rem 1.6rem;
}

/* ── Stat cards ──────────────────────────────────────────────────────── */
.stat-row { display: flex; gap: 12px; margin: 1rem 0 0.6rem; }
.stat-card {
    background: #0d1420;
    border: 1px solid #1e2d40;
    border-radius: 8px;
    padding: 0.65rem 1.1rem;
    min-width: 120px;
}
.stat-label {
    font-size: 0.65rem;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    font-weight: 600;
}
.stat-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.35rem;
    color: #58a6ff;
    margin-top: 0.1rem;
    font-weight: 500;
}

/* ── Section label ───────────────────────────────────────────────────── */
.section-tag {
    display: inline-block;
    background: #132236;
    color: #58a6ff;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.22rem 0.7rem;
    border-radius: 4px;
    letter-spacing: 0.8px;
    margin-bottom: 0.6rem;
    text-transform: uppercase;
}

/* ── Empty state ─────────────────────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #2d3748;
}
.empty-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.empty-text {
    font-size: 1rem;
    font-family: 'IBM Plex Mono', monospace;
    color: #2d3748;
}

/* ── Dataframe wrapper ───────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #1a2535 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── Button group (statement tabs) ──────────────────────────────────── */
div[data-testid="stHorizontalBlock"] button {
    background: #0d1117 !important;
    border: 1px solid #1e2d40 !important;
    color: #8896ae !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.82rem !important;
    border-radius: 6px !important;
    padding: 0.4rem 1rem !important;
}

/* ── Footer ──────────────────────────────────────────────────────────── */
.fin-footer {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #1e2d40;
    text-align: center;
    padding: 2rem 0 1rem;
    letter-spacing: 0.5px;
}

/* ── Alerts ──────────────────────────────────────────────────────────── */
.stAlert { border-radius: 8px !important; }

/* ── Radio / select labels ───────────────────────────────────────────── */
label { color: #8896ae !important; font-size: 0.82rem !important; }

/* ── Divider ─────────────────────────────────────────────────────────── */
hr { border-color: #1a2535; margin: 0.6rem 0; }
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Session state keys
# ─────────────────────────────────────────────────────────────────────────────
_KEY_LANG          = "fin_lang"
_KEY_RAW_DF        = "fin_raw_df"
_KEY_CLASSIFIED    = "fin_classified"
_KEY_SHEET         = "fin_sheet"
_KEY_FILE_ID       = "fin_file_id"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _stat_card(label: str, value: str) -> str:
    return (
        f'<div class="stat-card">'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-value">{value}</div>'
        f'</div>'
    )


def _section_tag(text: str) -> None:
    st.markdown(f'<span class="section-tag">{text}</span>', unsafe_allow_html=True)


STMT_TYPE_MAP: dict[str, StatementType | None] = {
    # Filled at runtime from translations, keyed by T[key]
}

# ─────────────────────────────────────────────────────────────────────────────
# Main render entry point
# ─────────────────────────────────────────────────────────────────────────────

def render_page() -> None:
    # ── Inject CSS ────────────────────────────────────────────────────────────
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Language selector (very top, persisted in session) ───────────────────
    lang_col, _ = st.columns([1, 5])
    with lang_col:
        lang = st.radio(
            "🌐",
            ["TR", "EN"],
            horizontal=True,
            label_visibility="collapsed",
            key=_KEY_LANG,
        )
    T = get_t(lang)

    # ── App header ────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="fin-header">'
        f'<p class="fin-title">📈 {T["app_title"]}</p>'
        f'<p class="fin-tagline">{T["app_tagline"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Control strip ─────────────────────────────────────────────────────────
    ctl_upload, ctl_table, ctl_period = st.columns([3, 3, 2])

    # ── File upload ───────────────────────────────────────────────────────────
    with ctl_upload:
        _section_tag(T["upload_header"])
        uploaded = st.file_uploader(
            T["upload_label"],
            type=["xlsx", "csv"],
            help=T["upload_help"],
            label_visibility="collapsed",
        )

    # ── Statement type selector ───────────────────────────────────────────────
    with ctl_table:
        _section_tag(T["table_header"])
        table_options = [
            T["table_all"],
            T["table_income"],
            T["table_balance"],
            T["table_cashflow"],
        ]
        selected_table_label = st.selectbox(
            T["table_header"],
            options=table_options,
            label_visibility="collapsed",
        )

    # ── Period selector ───────────────────────────────────────────────────────
    with ctl_period:
        _section_tag(T["period_header"])
        period_label = st.radio(
            T["period_header"],
            [T["period_annual"], T["period_quarterly"]],
            horizontal=False,
            label_visibility="collapsed",
        )

    period = (
        PeriodType.ANNUAL
        if period_label == T["period_annual"]
        else PeriodType.QUARTERLY
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── No file yet → empty state ─────────────────────────────────────────────
    if uploaded is None:
        st.markdown(
            f'<div class="empty-state">'
            f'<div class="empty-icon">📂</div>'
            f'<div class="empty-text">{T["no_file_msg"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        _render_footer(T)
        return

    # ── Load / cache file ─────────────────────────────────────────────────────
    file_id = (uploaded.name, uploaded.size)

    if st.session_state.get(_KEY_FILE_ID) != file_id:
        # New file — clear cache
        st.session_state[_KEY_FILE_ID]     = file_id
        st.session_state[_KEY_RAW_DF]      = None
        st.session_state[_KEY_CLASSIFIED]  = None
        st.session_state[_KEY_SHEET]       = None

    file_bytes = uploaded.read()
    sheet_names = get_sheet_names(file_bytes, uploaded.name)

    # Sheet picker (xlsx with multiple sheets)
    selected_sheet: str | None = None
    if sheet_names and len(sheet_names) > 1:
        selected_sheet = st.selectbox(
            T["upload_sheet_label"],
            options=sheet_names,
        )

    # Load (or use cached)
    cache_key = (file_id, selected_sheet)
    if st.session_state.get(_KEY_FILE_ID) != file_id or st.session_state.get(_KEY_SHEET) != selected_sheet:
        result: LoadResult = load_file(file_bytes, uploaded.name, selected_sheet)
        st.session_state[_KEY_FILE_ID]    = file_id
        st.session_state[_KEY_SHEET]      = selected_sheet
        st.session_state[_KEY_RAW_DF]     = result
        st.session_state[_KEY_CLASSIFIED] = None
    else:
        result = st.session_state[_KEY_RAW_DF]

    if not result.ok:
        if result.error == "empty":
            st.warning(T["err_empty"])
        else:
            st.error(f"{T['err_read']}: {result.error}")
        return

    raw_df: pd.DataFrame = result.df

    # ── Classification (cached per file) ──────────────────────────────────────
    if st.session_state.get(_KEY_CLASSIFIED) is None:
        classified = classify_dataframe(raw_df)
        st.session_state[_KEY_CLASSIFIED] = classified

    classified: dict[StatementType, pd.DataFrame] = st.session_state[_KEY_CLASSIFIED]

    # Show info banner if file was auto-split
    if has_mixed_statements(raw_df):
        st.info(T["info_classification"])

    # ── Resolve which sub-DataFrame to show ───────────────────────────────────
    label_to_type: dict[str, StatementType | None] = {
        T["table_all"]:      None,
        T["table_income"]:   StatementType.INCOME,
        T["table_balance"]:  StatementType.BALANCE,
        T["table_cashflow"]: StatementType.CASHFLOW,
    }
    selected_type = label_to_type.get(selected_table_label)

    if selected_type is None:
        # "All" — show entire raw_df
        view_df = raw_df.copy()
    else:
        view_df = classified.get(selected_type, pd.DataFrame())

    if view_df.empty:
        st.warning(T["no_rows_msg"])
        _render_footer(T)
        return

    # ── Period filter ─────────────────────────────────────────────────────────
    view_df = filter_columns(view_df, period)

    if view_df.empty:
        st.warning(T["no_cols_msg"])
        _render_footer(T)
        return

    # ── Stat cards ────────────────────────────────────────────────────────────
    num_numeric = sum(
        1 for c in view_df.columns
        if pd.api.types.is_numeric_dtype(view_df[c])
    )
    stmt_label = selected_table_label

    stats_html = (
        '<div class="stat-row">'
        + _stat_card(T["stat_total_rows"], str(len(view_df)))
        + _stat_card(T["stat_total_cols"], str(len(view_df.columns)))
        + _stat_card(T["stat_numeric"], str(num_numeric))
        + _stat_card(T["stat_table_type"], stmt_label)
        + "</div>"
    )
    st.markdown(stats_html, unsafe_allow_html=True)

    # ── Table display ─────────────────────────────────────────────────────────
    display_df = format_dataframe(view_df)

    row_height = min(600, 55 + len(display_df) * 35)
    st.dataframe(display_df, use_container_width=True, height=row_height)

    # ── Unclassified rows warning ─────────────────────────────────────────────
    other_df = classified.get(StatementType.OTHER, pd.DataFrame())
    if not other_df.empty and selected_type is None:
        st.caption(T["warn_unclassified"])

    # ── Future module hooks ───────────────────────────────────────────────────
    # TODO: Ratios tab — uncomment when ratios.py is ready:
    # from ratios import compute_ratios
    # ratios_df = compute_ratios(classified[INCOME], classified[BALANCE], classified[CASHFLOW])
    # st.dataframe(format_dataframe(ratios_df))

    # TODO: Charts section — uncomment when charts.py is ready:
    # from charts import render_revenue_chart
    # render_revenue_chart(classified[INCOME])

    # TODO: Margin analysis — uncomment when margins.py is ready:
    # from margins import compute_margins
    # st.dataframe(format_dataframe(compute_margins(classified[INCOME])))

    # TODO: Valuation panel — uncomment when valuation.py is ready:
    # from valuation import dcf_valuation
    # result = dcf_valuation(classified[CASHFLOW], wacc=0.10, terminal_growth=0.03)
    # st.metric("Intrinsic Value", result['intrinsic_value'])

    # TODO: Export button — uncomment when export.py is ready:
    # from export import export_to_excel
    # xlsx_bytes = export_to_excel(classified[INCOME], classified[BALANCE], classified[CASHFLOW])
    # st.download_button("Export .xlsx", xlsx_bytes, "analysis.xlsx")

    _render_footer(T)


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────

def _render_footer(T: dict) -> None:
    st.markdown(
        f'<div class="fin-footer">⬡ {T["footer"]}</div>',
        unsafe_allow_html=True,
    )
