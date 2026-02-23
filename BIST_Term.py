# BIST_Term.py
# Streamlit Financial Statement Analyzer — Single File Version

from __future__ import annotations
import streamlit as st
import pandas as pd
import io
from enum import Enum


# =============================
# TRANSLATIONS
# =============================

def get_t(lang: str):
    TR = {
        "app_title": "Finansal Tablo Analiz",
        "app_tagline": "Dosya yükle • Otomatik sınıflandır • Analiz et",
        "upload_header": "Dosya",
        "upload_label": "Excel / CSV yükle",
        "upload_help": "Finansal tablo içeren dosya",
        "upload_sheet_label": "Sheet seç",
        "table_header": "Tablo Türü",
        "table_all": "Hepsi",
        "table_income": "Gelir Tablosu",
        "table_balance": "Bilanço",
        "table_cashflow": "Nakit Akışı",
        "period_header": "Dönem",
        "period_annual": "Yıllık",
        "period_quarterly": "Çeyreklik",
        "no_file_msg": "Dosya yükleyerek başlayın",
        "err_empty": "Dosya boş",
        "err_read": "Dosya okunamadı",
        "info_classification": "Tablo otomatik sınıflandırıldı",
        "no_rows_msg": "Gösterilecek satır yok",
        "no_cols_msg": "Gösterilecek kolon yok",
        "stat_total_rows": "Satır",
        "stat_total_cols": "Kolon",
        "stat_numeric": "Numerik",
        "stat_table_type": "Tablo",
        "warn_unclassified": "Bazı satırlar sınıflandırılamadı",
        "footer": "Financial Analyzer MVP",
    }

    EN = {
        "app_title": "Financial Analyzer",
        "app_tagline": "Upload • Classify • Analyze",
    }

    return TR if lang == "TR" else EN


# =============================
# ENUMS
# =============================

class StatementType(Enum):
    INCOME = "income"
    BALANCE = "balance"
    CASHFLOW = "cashflow"
    OTHER = "other"


class PeriodType(Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"


# =============================
# DATA LOADER
# =============================

class LoadResult:
    def __init__(self, ok: bool, df=None, error=None):
        self.ok = ok
        self.df = df
        self.error = error


def get_sheet_names(file_bytes, filename):
    if filename.endswith(".xlsx"):
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        return xls.sheet_names
    return []


def load_file(file_bytes, filename, sheet=None):
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet)

        if df.empty:
            return LoadResult(False, error="empty")

        return LoadResult(True, df=df)

    except Exception as e:
        return LoadResult(False, error=str(e))


# =============================
# CLASSIFIER
# =============================

def classify_dataframe(df: pd.DataFrame):

    classified = {
        StatementType.INCOME: pd.DataFrame(),
        StatementType.BALANCE: pd.DataFrame(),
        StatementType.CASHFLOW: pd.DataFrame(),
        StatementType.OTHER: pd.DataFrame(),
    }

    for idx, row in df.iterrows():
        text = " ".join(map(str, row.values)).lower()

        if any(x in text for x in ["revenue", "sales", "income", "profit"]):
            classified[StatementType.INCOME] = pd.concat(
                [classified[StatementType.INCOME], row.to_frame().T]
            )

        elif any(x in text for x in ["asset", "liability", "equity"]):
            classified[StatementType.BALANCE] = pd.concat(
                [classified[StatementType.BALANCE], row.to_frame().T]
            )

        elif any(x in text for x in ["cash"]):
            classified[StatementType.CASHFLOW] = pd.concat(
                [classified[StatementType.CASHFLOW], row.to_frame().T]
            )

        else:
            classified[StatementType.OTHER] = pd.concat(
                [classified[StatementType.OTHER], row.to_frame().T]
            )

    return classified


def has_mixed_statements(df):
    return True


# =============================
# PERIOD FILTER
# =============================

def filter_columns(df: pd.DataFrame, period: PeriodType):

    cols = []

    for c in df.columns:
        text = str(c).lower()

        if period == PeriodType.QUARTERLY:
            if any(x in text for x in ["q", "ç"]):
                cols.append(c)

        else:
            cols.append(c)

    if cols:
        return df[cols]

    return df


# =============================
# FORMATTERS
# =============================

def format_dataframe(df: pd.DataFrame):
    return df


# =============================
# UI
# =============================

def render_page():

    st.set_page_config(layout="wide")

    lang = st.radio("🌐", ["TR", "EN"], horizontal=True)
    T = get_t(lang)

    st.title(T["app_title"])

    uploaded = st.file_uploader("Dosya yükle", type=["xlsx", "csv"])

    if uploaded is None:
        st.info("Dosya yükleyin")
        return

    file_bytes = uploaded.read()
    sheet_names = get_sheet_names(file_bytes, uploaded.name)

    sheet = None
    if len(sheet_names) > 1:
        sheet = st.selectbox("Sheet", sheet_names)

    result = load_file(file_bytes, uploaded.name, sheet)

    if not result.ok:
        st.error("Dosya okunamadı")
        return

    df = result.df

    classified = classify_dataframe(df)

    table_type = st.selectbox(
        "Tablo",
        ["Hepsi", "Gelir", "Bilanço", "Nakit"]
    )

    period = st.radio(
        "Dönem",
        ["Yıllık", "Çeyreklik"]
    )

    if table_type == "Gelir":
        view_df = classified[StatementType.INCOME]

    elif table_type == "Bilanço":
        view_df = classified[StatementType.BALANCE]

    elif table_type == "Nakit":
        view_df = classified[StatementType.CASHFLOW]

    else:
        view_df = df

    if period == "Çeyreklik":
        view_df = filter_columns(view_df, PeriodType.QUARTERLY)

    st.dataframe(view_df, use_container_width=True)


# =============================
# RUN
# =============================

if __name__ == "__main__":
    render_page()
