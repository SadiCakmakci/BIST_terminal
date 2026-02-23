import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import re

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Financial Analysis Terminal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# TRANSLATIONS MODULE
# ============================================================

TRANSLATIONS = {
    "EN": {
        "upload": "Upload Financial File",
        "statement": "Statement Type",
        "period": "Period Type",
        "scale": "Scale",
        "income": "Income Statement",
        "balance": "Balance Sheet",
        "cashflow": "Cash Flow",
        "other": "Other",
        "annual": "Annual",
        "quarterly": "Quarterly",
        "rows": "Rows",
        "columns": "Columns",
        "numeric_cols": "Numeric Columns",
        "statement_detected": "Detected Statement",
        "no_file": "Please upload a file.",
        "error": "File processing error.",
        "footer": "Financial Analysis System MVP",
    },
    "TR": {
        "upload": "Finansal Dosya Yükle",
        "statement": "Finansal Tablo",
        "period": "Dönem Tipi",
        "scale": "Ölçek",
        "income": "Gelir Tablosu",
        "balance": "Bilanço",
        "cashflow": "Nakit Akış",
        "other": "Diğer",
        "annual": "Yıllık",
        "quarterly": "Çeyreklik",
        "rows": "Satır",
        "columns": "Kolon",
        "numeric_cols": "Sayısal Kolon",
        "statement_detected": "Tespit Edilen Tablo",
        "no_file": "Lütfen dosya yükleyin.",
        "error": "Dosya işleme hatası.",
        "footer": "Finansal Analiz Sistemi MVP",
    }
}

# ============================================================
# KEYWORD ENGINE
# ============================================================

INCOME_KEYWORDS = [
    "revenue", "sales", "net income", "gross profit",
    "operating profit", "hasılat", "satış", "net kar", "brüt kar"
]

BALANCE_KEYWORDS = [
    "assets", "liabilities", "equity",
    "varlık", "yükümlülük", "özkaynak"
]

CASHFLOW_KEYWORDS = [
    "cash flow", "operating cash",
    "nakit akışı", "faaliyetlerden nakit"
]

# ============================================================
# DATA LOADER
# ============================================================

@st.cache_data
def load_file(file) -> Dict[str, pd.DataFrame]:
    dataframes = {}

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        dataframes["CSV"] = df
        return dataframes

    excel = pd.ExcelFile(file)

    for sheet in excel.sheet_names:
        try:
            df = excel.parse(sheet)
            dataframes[sheet] = df
        except Exception:
            continue

    return dataframes

# ============================================================
# CLASSIFIER
# ============================================================

def score_text(text: str, keywords: List[str]) -> int:
    text = str(text).lower()
    return sum(1 for k in keywords if k in text)

def classify_dataframe(df: pd.DataFrame) -> str:

    score_income = 0
    score_balance = 0
    score_cash = 0

    for col in df.columns:
        score_income += score_text(col, INCOME_KEYWORDS)
        score_balance += score_text(col, BALANCE_KEYWORDS)
        score_cash += score_text(col, CASHFLOW_KEYWORDS)

    for _, row in df.iterrows():
        row_text = " ".join(map(str, row.values))
        score_income += score_text(row_text, INCOME_KEYWORDS)
        score_balance += score_text(row_text, BALANCE_KEYWORDS)
        score_cash += score_text(row_text, CASHFLOW_KEYWORDS)

    scores = {
        "INCOME": score_income,
        "BALANCE": score_balance,
        "CASHFLOW": score_cash
    }

    best = max(scores, key=scores.get)

    if scores[best] == 0:
        return "OTHER"

    return best

def classify_all(dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:

    classified = {
        "INCOME": None,
        "BALANCE": None,
        "CASHFLOW": None,
        "OTHER": None
    }

    for name, df in dataframes.items():
        category = classify_dataframe(df)
        classified[category] = df

    return classified

# ============================================================
# PERIOD DETECTION
# ============================================================

def detect_period(columns: List[str]) -> Tuple[List[str], List[str]]:

    annual_cols = []
    quarterly_cols = []

    for col in columns:
        col_str = str(col).lower()

        if re.search(r"(q[1-4]|[1-4]ç)", col_str):
            quarterly_cols.append(col)
        elif re.search(r"(20\d{2})", col_str):
            annual_cols.append(col)

    return annual_cols, quarterly_cols

# ============================================================
# FORMATTERS
# ============================================================

def detect_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")
    return df

def scale_dataframe(df: pd.DataFrame, scale: str) -> pd.DataFrame:

    factor = 1

    if scale == "Thousands":
        factor = 1_000
    elif scale == "Millions":
        factor = 1_000_000

    numeric_cols = df.select_dtypes(include=np.number).columns
    df[numeric_cols] = df[numeric_cols] / factor

    return df

# ============================================================
# UI HELPERS
# ============================================================

def metric_card(label: str, value):
    st.metric(label, value)

def apply_dark_theme():
    st.markdown("""
        <style>
        body { background-color: #0e1117; color: white; }
        </style>
    """, unsafe_allow_html=True)

# ============================================================
# MAIN APP
# ============================================================

def main():

    apply_dark_theme()

    # Language
    lang = st.selectbox("Language", ["EN", "TR"])
    T = TRANSLATIONS[lang]

    st.title("📊 Financial Analysis Terminal")

    uploaded = st.file_uploader(T["upload"], type=["xlsx", "xls", "csv"])

    if not uploaded:
        st.info(T["no_file"])
        return

    try:
        data = load_file(uploaded)
        classified = classify_all(data)
    except Exception as e:
        st.error(T["error"])
        st.exception(e)
        return

    statement_options = {
        T["income"]: "INCOME",
        T["balance"]: "BALANCE",
        T["cashflow"]: "CASHFLOW",
        T["other"]: "OTHER"
    }

    statement_choice = st.selectbox(
        T["statement"],
        list(statement_options.keys())
    )

    df = classified.get(statement_options[statement_choice])

    if df is None:
        st.warning("No data detected.")
        return

    df = detect_numeric(df)

    annual_cols, quarterly_cols = detect_period(df.columns)

    period_choice = st.selectbox(
        T["period"],
        [T["annual"], T["quarterly"]]
    )

    if period_choice == T["annual"] and annual_cols:
        display_cols = annual_cols
    elif period_choice == T["quarterly"] and quarterly_cols:
        display_cols = quarterly_cols
    else:
        display_cols = df.columns

    scale = st.selectbox(
        T["scale"],
        ["Full", "Thousands", "Millions"]
    )

    df_scaled = scale_dataframe(df.copy(), scale)

    display_df = df_scaled[display_cols]

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(T["rows"], display_df.shape[0])
    col2.metric(T["columns"], display_df.shape[1])
    col3.metric(T["numeric_cols"], len(display_df.select_dtypes(include=np.number).columns))
    col4.metric(T["statement_detected"], statement_options[statement_choice])

    st.dataframe(display_df, use_container_width=True)

    # TODO FUTURE MODULES
    # ---------------------
    # Financial Ratios
    # Charts
    # Margin Analysis
    # DCF Valuation
    # AI Commentary
    # Export to Excel

    st.markdown("---")
    st.caption(T["footer"])


if __name__ == "__main__":
    main()
