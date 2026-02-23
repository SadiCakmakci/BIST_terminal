"""
BİST Finansal Analiz Uygulaması - MVP v1.0
Fintables standartlarına uygun, çok dilli (TR/EN) finansal analiz aracı.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────
# 1. SAYFA AYARLARI
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BİST Finansal Analiz",
    page_icon="📊",
    layout="wide",
)

# ─────────────────────────────────────────────
# 2. DİL SÖZLÜĞÜ
# ─────────────────────────────────────────────
LABELS = {
    "TR": {
        # Sidebar
        "app_title": "📊 BİST Finansal Analiz",
        "lang_label": "Dil / Language",
        "ticker_label": "Hisse Kodu",
        "ticker_placeholder": "Örn: THYAO.IS",
        "period_label": "Veri Periyodu",
        "period_quarterly": "Çeyreklik",
        "period_annual": "Yıllık",
        "fetch_button": "Verileri Getir",
        # Uyarılar
        "warn_empty_ticker": "⚠️ Lütfen bir hisse kodu girin.",
        "warn_no_data": "⚠️ Veri çekilemedi. Hisse kodunu kontrol edin (örn: THYAO.IS).",
        "warn_partial": "ℹ️ Bazı satırlar için veri bulunamadı; '-' ile gösterildi.",
        "loading": "Veriler yükleniyor...",
        "unit_note": "Tüm rakamlar Bin TL (Thousand TRY) cinsindendir.",
        # Tablo başlıkları
        "income_title": "📋 Özet Gelir Tablosu",
        "balance_title": "🏦 Özet Bilanço",
        "cashflow_title": "💵 Özet Nakit Akım Tablosu",
        # Gelir tablosu satırları
        "revenue": "Satış Gelirleri",
        "gross_profit": "Brüt Kar",
        "operating_income": "Faaliyet Karı",
        "ebitda": "FAVÖK / EBITDA",
        "net_income": "Net Dönem Karı",
        # Bilanço satırları
        "current_assets": "Dönen Varlıklar",
        "non_current_assets": "Duran Varlıklar",
        "total_assets": "Toplam Varlıklar",
        "current_liabilities": "Kısa Vadeli Yükümlülükler",
        "non_current_liabilities": "Uzun Vadeli Yükümlülükler",
        "equity": "Ana Ortaklığa Ait Özkaynaklar",
        "net_debt": "Net Borç",
        # Nakit akım satırları
        "operating_cf": "İşletme Faaliyetlerinden Nakit Akışları",
        "investing_cf": "Yatırım Faaliyetlerinden Nakit Akışları",
        "financing_cf": "Finansman Faaliyetlerinden Nakit Akışları",
    },
    "EN": {
        "app_title": "📊 BIST Financial Analysis",
        "lang_label": "Language / Dil",
        "ticker_label": "Ticker Symbol",
        "ticker_placeholder": "e.g.: THYAO.IS",
        "period_label": "Data Period",
        "period_quarterly": "Quarterly",
        "period_annual": "Annual",
        "fetch_button": "Fetch Data",
        "warn_empty_ticker": "⚠️ Please enter a ticker symbol.",
        "warn_no_data": "⚠️ Could not retrieve data. Check the ticker (e.g.: THYAO.IS).",
        "warn_partial": "ℹ️ Some rows had no data available; shown as '-'.",
        "loading": "Loading data...",
        "unit_note": "All figures are in Thousand TRY (Bin TL).",
        "income_title": "📋 Income Statement",
        "balance_title": "🏦 Balance Sheet",
        "cashflow_title": "💵 Cash Flow Statement",
        "revenue": "Revenue",
        "gross_profit": "Gross Profit",
        "operating_income": "Operating Income",
        "ebitda": "EBITDA",
        "net_income": "Net Income",
        "current_assets": "Total Current Assets",
        "non_current_assets": "Total Non-Current Assets",
        "total_assets": "Total Assets",
        "current_liabilities": "Total Current Liabilities",
        "non_current_liabilities": "Total Non-Current Liabilities",
        "equity": "Stockholders' Equity",
        "net_debt": "Net Debt",
        "operating_cf": "Operating Cash Flow",
        "investing_cf": "Investing Cash Flow",
        "financing_cf": "Financing Cash Flow",
    },
}

# ─────────────────────────────────────────────
# 3. YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def safe_get(df: pd.DataFrame, keys: list, divisor: float = 1_000) -> pd.Series:
    """
    DataFrame'den birden fazla olası anahtar adıyla satır çekmeye çalışır.
    Bulunan ilk eşleşmeyi 1.000'e bölerek (Bin TL) döndürür.
    Hiçbir anahtar bulunamazsa NaN serisi döndürür.
    """
    if df is None or df.empty:
        return pd.Series(dtype=float)
    for key in keys:
        if key in df.index:
            return df.loc[key] / divisor
    return pd.Series(dtype=float)


def format_number(val) -> str:
    """Sayısal değeri Türk/Avrupa binlik ayraçlı tam sayı formatına çevirir."""
    try:
        if pd.isna(val):
            return "-"
        int_val = int(round(float(val)))
        # Noktayı binlik ayraç olarak kullan
        return f"{int_val:,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "-"


def format_df(df: pd.DataFrame) -> pd.DataFrame:
    """Tüm DataFrame'i string formatına çevirir."""
    return df.applymap(format_number)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_financials(ticker_symbol: str, quarterly: bool):
    """
    yfinance üzerinden finansal tabloları çeker.
    TTL=300 sn cache ile gereksiz API çağrılarını önler.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        if quarterly:
            income = ticker.quarterly_financials
            balance = ticker.quarterly_balance_sheet
            cashflow = ticker.quarterly_cashflow
        else:
            income = ticker.financials
            balance = ticker.balance_sheet
            cashflow = ticker.cashflow
        return income, balance, cashflow, None
    except Exception as e:
        return None, None, None, str(e)


def build_income_statement(income: pd.DataFrame, lang: str) -> pd.DataFrame:
    """Gelir tablosunu Fintables formatında oluşturur."""
    L = LABELS[lang]

    revenue        = safe_get(income, ["Total Revenue", "Revenue"])
    gross_profit   = safe_get(income, ["Gross Profit"])
    op_income      = safe_get(income, ["Operating Income", "Ebit"])
    depreciation   = safe_get(income, ["Reconciled Depreciation", "Depreciation And Amortization In Income Statement", "Depreciation"])
    net_income     = safe_get(income, ["Net Income", "Net Income Common Stockholders"])

    # EBITDA = Faaliyet Karı + Amortisman
    ebitda = op_income.add(depreciation, fill_value=0) if not op_income.empty else depreciation

    rows = {
        L["revenue"]:         revenue,
        L["gross_profit"]:    gross_profit,
        L["operating_income"]: op_income,
        L["ebitda"]:          ebitda,
        L["net_income"]:      net_income,
    }

    df = pd.DataFrame(rows).T
    df.columns = [str(c.date()) if hasattr(c, "date") else str(c) for c in df.columns]
    return df


def build_balance_sheet(balance: pd.DataFrame, lang: str) -> pd.DataFrame:
    """Bilançoyu Fintables formatında oluşturur."""
    L = LABELS[lang]

    current_assets      = safe_get(balance, ["Current Assets", "Total Current Assets"])
    total_assets        = safe_get(balance, ["Total Assets"])
    non_current_assets  = total_assets.subtract(current_assets, fill_value=0) if not total_assets.empty else pd.Series(dtype=float)

    current_liab        = safe_get(balance, ["Current Liabilities", "Total Current Liabilities"])
    total_liab          = safe_get(balance, ["Total Liabilities Net Minority Interest", "Total Liabilities"])
    non_current_liab    = total_liab.subtract(current_liab, fill_value=0) if not total_liab.empty else pd.Series(dtype=float)

    equity              = safe_get(balance, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])

    # Net Borç = Kısa + Uzun vadeli finansal borçlar - Nakit
    total_debt          = safe_get(balance, ["Total Debt", "Long Term Debt And Capital Lease Obligation"])
    cash                = safe_get(balance, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"])
    net_debt            = total_debt.subtract(cash, fill_value=0) if not total_debt.empty else pd.Series(dtype=float)

    rows = {
        L["current_assets"]:       current_assets,
        L["non_current_assets"]:   non_current_assets,
        L["total_assets"]:         total_assets,
        L["current_liabilities"]:  current_liab,
        L["non_current_liabilities"]: non_current_liab,
        L["equity"]:               equity,
        L["net_debt"]:             net_debt,
    }

    df = pd.DataFrame(rows).T
    df.columns = [str(c.date()) if hasattr(c, "date") else str(c) for c in df.columns]
    return df


def build_cashflow(cashflow: pd.DataFrame, lang: str) -> pd.DataFrame:
    """Nakit akım tablosunu Fintables formatında oluşturur."""
    L = LABELS[lang]

    op_cf  = safe_get(cashflow, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
    inv_cf = safe_get(cashflow, ["Investing Cash Flow", "Cash Flow From Continuing Investing Activities"])
    fin_cf = safe_get(cashflow, ["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"])

    rows = {
        L["operating_cf"]:  op_cf,
        L["investing_cf"]:  inv_cf,
        L["financing_cf"]:  fin_cf,
    }

    df = pd.DataFrame(rows).T
    df.columns = [str(c.date()) if hasattr(c, "date") else str(c) for c in df.columns]
    return df


def display_table(title: str, df: pd.DataFrame):
    """Tabloyu başlığıyla birlikte şık biçimde gösterir."""
    st.markdown(f"### {title}")
    if df.empty:
        st.warning("Tablo verisi bulunamadı." if st.session_state.get("lang") == "TR" else "No data available for this table.")
        return

    formatted = format_df(df)

    st.dataframe(
        formatted,
        use_container_width=True,
        height=min(50 + len(formatted) * 38, 400),
    )


# ─────────────────────────────────────────────
# 4. SESSION STATE BAŞLANGICI
# ─────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state["lang"] = "TR"
if "ticker" not in st.session_state:
    st.session_state["ticker"] = "THYAO.IS"
if "quarterly" not in st.session_state:
    st.session_state["quarterly"] = False

# ─────────────────────────────────────────────
# 5. SIDEBAR (KONTROL PANELİ)
# ─────────────────────────────────────────────
with st.sidebar:
    # --- Dil Seçimi ---
    lang_choice = st.selectbox(
        "🌐 Dil / Language",
        options=["TR", "EN"],
        index=0 if st.session_state["lang"] == "TR" else 1,
        key="lang_selectbox",
    )
    st.session_state["lang"] = lang_choice
    lang = st.session_state["lang"]
    L = LABELS[lang]

    st.markdown("---")
    st.markdown(f"## {L['app_title']}")
    st.markdown("---")

    # --- Hisse Kodu ---
    ticker_input = st.text_input(
        L["ticker_label"],
        value=st.session_state["ticker"],
        placeholder=L["ticker_placeholder"],
    ).strip().upper()

    # --- Periyot Seçimi ---
    period_choice = st.radio(
        L["period_label"],
        options=[L["period_quarterly"], L["period_annual"]],
        index=0 if st.session_state["quarterly"] else 1,
        horizontal=True,
    )
    is_quarterly = period_choice == L["period_quarterly"]

    st.markdown("---")

    # --- Veri Getir Butonu ---
    fetch_clicked = st.button(L["fetch_button"], type="primary", use_container_width=True)

    if fetch_clicked:
        st.session_state["ticker"] = ticker_input
        st.session_state["quarterly"] = is_quarterly

    st.markdown("---")
    st.caption("MVP v1.0 | yfinance → Fintables Mapping")

# ─────────────────────────────────────────────
# 6. ANA EKRAN
# ─────────────────────────────────────────────
lang = st.session_state["lang"]
L = LABELS[lang]

st.title(L["app_title"])

current_ticker = st.session_state.get("ticker", "")
quarterly_mode = st.session_state.get("quarterly", False)

period_label = L["period_quarterly"] if quarterly_mode else L["period_annual"]
st.caption(f"**{current_ticker}** | {period_label} | {L['unit_note']}")
st.markdown("---")

if not current_ticker:
    st.info(L["warn_empty_ticker"])
    st.stop()

# Veri çekme
with st.spinner(L["loading"]):
    income_raw, balance_raw, cashflow_raw, err = fetch_financials(current_ticker, quarterly_mode)

if err or (income_raw is None and balance_raw is None and cashflow_raw is None):
    st.error(L["warn_no_data"])
    if err:
        st.exception(err)
    st.stop()

# Tabloları oluştur
try:
    income_df   = build_income_statement(income_raw, lang)
    balance_df  = build_balance_sheet(balance_raw, lang)
    cashflow_df = build_cashflow(cashflow_raw, lang)
except Exception as e:
    st.error(L["warn_no_data"])
    st.exception(e)
    st.stop()

# Eksik veri uyarısı
has_missing = (
    income_df.isnull().any().any()
    or balance_df.isnull().any().any()
    or cashflow_df.isnull().any().any()
)
if has_missing:
    st.info(L["warn_partial"])

# Tabloları göster
display_table(L["income_title"], income_df)
st.markdown("")
display_table(L["balance_title"], balance_df)
st.markdown("")
display_table(L["cashflow_title"], cashflow_df)
