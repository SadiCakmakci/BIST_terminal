"""
BİST Finansal Analiz Uygulaması - MVP v1.0
Fintables benzeri, çok dilli (TR/EN) finansal tablo gösterimi
Veri Kaynağı: İş Yatırım Mali Tablo API
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
# SAYFA AYARLARI
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BİST Finansal Analiz",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# BIST30 HİSSE LİSTESİ
# ─────────────────────────────────────────────
BIST30 = [
    "AKBNK", "ARCLK", "ASELS", "BIMAS", "DOHOL",
    "EKGYO", "EREGL", "FROTO", "GARAN", "GUBRF",
    "HALKB", "ISCTR", "KCHOL", "KOZAA", "KOZAL",
    "KRDMD", "MGROS", "ODAS", "PETKM", "PGSUS",
    "SAHOL", "SASA", "SISE", "TAVHL", "TCELL",
    "THYAO", "TKFEN", "TOASO", "TTKOM", "VAKBN",
    "YKBNK",
]

# ─────────────────────────────────────────────
# ÇEVİRİ / ETİKETLER
# ─────────────────────────────────────────────
LABELS = {
    "TR": {
        "title": "BİST Finansal Analiz",
        "subtitle": "İş Yatırım verileriyle Fintables benzeri finansal tablo gösterimi",
        "sidebar_header": "Kontrol Paneli",
        "language": "Dil / Language",
        "ticker": "Hisse Senedi",
        "period_type": "Veri Periyodu",
        "quarterly": "Çeyreklik",
        "annual": "Yıllık",
        "fetch_btn": "Verileri Getir",
        "loading": "Veriler yükleniyor...",
        "error_fetch": "Veri çekme hatası",
        "error_empty": "Bu hisse için veri bulunamadı.",
        "error_parse": "Veri ayrıştırma hatası",
        "unit_note": "Birim: Bin TL (Thousand TRY)",
        "table1_title": "📋 Gelir Tablosu (Income Statement)",
        "table2_title": "🏦 Bilanço (Balance Sheet)",
        "table3_title": "💵 Nakit Akım Tablosu (Cash Flow Statement)",
        "rows_income": {
            "revenue": "Satış Gelirleri",
            "gross_profit": "Brüt Kar",
            "operating_income": "Faaliyet Karı",
            "ebitda": "FAVÖK (EBITDA)",
            "net_income": "Net Dönem Karı",
        },
        "rows_balance": {
            "current_assets": "Dönen Varlıklar",
            "non_current_assets": "Duran Varlıklar",
            "total_assets": "Toplam Varlıklar",
            "current_liabilities": "Kısa Vadeli Yükümlülükler",
            "non_current_liabilities": "Uzun Vadeli Yükümlülükler",
            "equity": "Ana Ortaklığa Ait Özkaynaklar",
            "net_debt": "Net Borç",
        },
        "rows_cashflow": {
            "operating_cf": "İşletme Faaliyetlerinden Nakit Akışları",
            "investing_cf": "Yatırım Faaliyetlerinden Nakit Akışları",
            "financing_cf": "Finansman Faaliyetlerinden Nakit Akışları",
        },
        "no_data": "-",
    },
    "EN": {
        "title": "BİST Financial Analysis",
        "subtitle": "Fintables-style financial table display powered by İş Yatırım data",
        "sidebar_header": "Control Panel",
        "language": "Dil / Language",
        "ticker": "Stock Ticker",
        "period_type": "Data Period",
        "quarterly": "Quarterly",
        "annual": "Annual",
        "fetch_btn": "Fetch Data",
        "loading": "Loading data...",
        "error_fetch": "Data fetch error",
        "error_empty": "No data found for this ticker.",
        "error_parse": "Data parsing error",
        "unit_note": "Unit: Thousand TRY (Bin TL)",
        "table1_title": "📋 Income Statement (Gelir Tablosu)",
        "table2_title": "🏦 Balance Sheet (Bilanço)",
        "table3_title": "💵 Cash Flow Statement (Nakit Akım Tablosu)",
        "rows_income": {
            "revenue": "Revenue",
            "gross_profit": "Gross Profit",
            "operating_income": "Operating Income",
            "ebitda": "EBITDA",
            "net_income": "Net Income",
        },
        "rows_balance": {
            "current_assets": "Current Assets",
            "non_current_assets": "Non-Current Assets",
            "total_assets": "Total Assets",
            "current_liabilities": "Current Liabilities",
            "non_current_liabilities": "Non-Current Liabilities",
            "equity": "Total Equity (Parent)",
            "net_debt": "Net Debt",
        },
        "rows_cashflow": {
            "operating_cf": "Operating Cash Flow",
            "investing_cf": "Investing Cash Flow",
            "financing_cf": "Financing Cash Flow",
        },
        "no_data": "-",
    },
}

# ─────────────────────────────────────────────
# İŞ YATIRIM İTEM EŞLEŞME HARİTASI
# itemDescTr / itemDescEng anahtar kelimeleri
# ─────────────────────────────────────────────
ITEM_MAP = {
    # Gelir Tablosu
    "revenue":           {"tr": ["Hasılat", "Net Satışlar", "Satış Gelirleri", "Hasılat,"],
                          "en": ["Revenue", "Net Sales", "Sales Revenue"]},
    "gross_profit":      {"tr": ["Brüt Kar", "Brüt Kâr"],
                          "en": ["Gross Profit"]},
    "operating_income":  {"tr": ["Esas Faaliyetlerden Kar", "Faaliyet Karı", "Esas Faaliyet Karı/Zararı"],
                          "en": ["Operating Profit", "Operating Income", "Profit from Operations"]},
    "depreciation":      {"tr": ["Amortisman", "Amortisman ve İtfa"],
                          "en": ["Depreciation", "Depreciation and Amortization"]},
    "net_income":        {"tr": ["Ana Ortaklık Payları", "Ana Ortaklığa Ait Net Dönem Karı", "Dönem Karı/Zararı"],
                          "en": ["Profit Attributable to Parent", "Net Income", "Net Profit"]},
    # Bilanço
    "current_assets":        {"tr": ["Dönen Varlıklar"],
                              "en": ["Current Assets"]},
    "non_current_assets":    {"tr": ["Duran Varlıklar"],
                              "en": ["Non-Current Assets", "Non Current Assets"]},
    "total_assets":          {"tr": ["Toplam Varlıklar", "TOPLAM VARLIKLAR"],
                              "en": ["Total Assets"]},
    "current_liabilities":   {"tr": ["Kısa Vadeli Yükümlülükler", "KISA VADELİ YÜKÜMLÜLÜKLER"],
                              "en": ["Current Liabilities"]},
    "non_current_liabilities":{"tr": ["Uzun Vadeli Yükümlülükler", "UZUN VADELİ YÜKÜMLÜLÜKLER"],
                               "en": ["Non-Current Liabilities", "Non Current Liabilities"]},
    "equity":                {"tr": ["Ana Ortaklığa Ait Özkaynaklar", "Özkaynaklar"],
                              "en": ["Equity Attributable to Parent", "Total Equity"]},
    "cash":                  {"tr": ["Nakit ve Nakit Benzerleri"],
                              "en": ["Cash and Cash Equivalents"]},
    "st_financial_debt":     {"tr": ["Kısa Vadeli Finansal Borçlar", "Kısa Vadeli Krediler ve Borçlanmalar"],
                              "en": ["Short-Term Borrowings", "Short Term Financial Liabilities"]},
    "lt_financial_debt":     {"tr": ["Uzun Vadeli Finansal Borçlar", "Uzun Vadeli Krediler ve Borçlanmalar"],
                              "en": ["Long-Term Borrowings", "Long Term Financial Liabilities"]},
    # Nakit Akım
    "operating_cf":   {"tr": ["İşletme Faaliyetlerinden", "İşletme Faaliyetlerinde Kullanılan Net Nakit"],
                       "en": ["Operating Activities", "Net Cash from Operating"]},
    "investing_cf":   {"tr": ["Yatırım Faaliyetlerinden", "Yatırım Faaliyetlerinde Kullanılan Net Nakit"],
                       "en": ["Investing Activities", "Net Cash from Investing"]},
    "financing_cf":   {"tr": ["Finansman Faaliyetlerinden", "Finansman Faaliyetlerinde Kullanılan Net Nakit"],
                       "en": ["Financing Activities", "Net Cash from Financing"]},
}

# ─────────────────────────────────────────────
# URL & DÖNEMLERİ OLUŞTURMA
# ─────────────────────────────────────────────
def build_periods(period_type: str):
    """
    Son 4 dönemi dinamik olarak üretir.
    Çeyreklik: 3, 6, 9, 12 (son 4 çeyrek)
    Yıllık   : 12, 12, 12, 12 (son 4 yıl aralıkları)
    """
    today = datetime.today()
    current_year = today.year
    current_month = today.month

    if period_type == "quarterly":
        # Mevcut çeyreği bul
        quarter_month = ((current_month - 1) // 3) * 3  # 3, 6 veya 9 → en son tamamlanan
        if quarter_month == 0:
            quarter_month = 12
            current_year -= 1

        periods = []
        y, m = current_year, quarter_month
        for _ in range(4):
            periods.append((y, m))
            m -= 3
            if m <= 0:
                m += 12
                y -= 1
        return periods  # [(yıl, dönem), ...]

    else:  # annual
        periods = []
        y = current_year - 1  # Son tamamlanan yıl
        for _ in range(4):
            periods.append((y, 12))
            y -= 1
        return periods


def build_url(ticker: str, periods: list) -> str:
    base = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo"
    params = f"companyCode={ticker}&exchange=TRY&financialGroup=XI_29"
    for i, (y, p) in enumerate(periods, start=1):
        params += f"&year{i}={y}&period{i}={p}"
    return f"{base}?{params}"


# ─────────────────────────────────────────────
# VERİ ÇEKME & PARSE
# ─────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def fetch_financial_data(ticker: str, period_type: str) -> pd.DataFrame | None:
    """
    İş Yatırım'dan mali tablo verisini çeker.
    Dönüş: Ham DataFrame (tüm kalemler) veya None
    """
    try:
        periods = build_periods(period_type)
        url = build_url(ticker, periods)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.isyatirim.com.tr/",
        }

        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        data = response.json()
        value = data.get("value", [])

        if not value:
            return None

        df = pd.DataFrame(value)
        return df, periods

    except requests.exceptions.RequestException as e:
        st.error(f"Bağlantı hatası: {e}")
        return None
    except (KeyError, ValueError) as e:
        st.error(f"JSON ayrıştırma hatası: {e}")
        return None


def find_item_value(df: pd.DataFrame, item_key: str, lang: str) -> dict:
    """
    DataFrame'den belirli bir kaleme ait değerleri anahtar kelimelerle bulur.
    """
    keywords = ITEM_MAP.get(item_key, {}).get(lang.lower(), [])
    fallback = ITEM_MAP.get(item_key, {}).get("tr" if lang == "en" else "en", [])

    desc_col = "itemDescTr" if lang == "TR" or lang == "tr" else "itemDescEng"
    fallback_col = "itemDescEng" if desc_col == "itemDescTr" else "itemDescTr"

    row = None
    for kw in keywords:
        mask = df[desc_col].str.contains(kw, case=False, na=False)
        if mask.any():
            row = df[mask].iloc[0]
            break

    # Bulunamazsa fallback dil sütununu dene
    if row is None:
        for kw in fallback:
            mask = df[fallback_col].str.contains(kw, case=False, na=False)
            if mask.any():
                row = df[mask].iloc[0]
                break

    if row is None:
        return {}

    # Değer sütunlarını topla (value1..value4)
    result = {}
    for i in range(1, 5):
        col = f"value{i}"
        if col in row.index:
            val = row[col]
            try:
                result[f"v{i}"] = float(val) / 1000 if val not in [None, "", "null"] else None
            except (ValueError, TypeError):
                result[f"v{i}"] = None
    return result


def format_number(val):
    """Sayıyı 1.000 ayraçlı tam sayı formatına çevirir."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "-"
    try:
        return f"{int(round(val)):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "-"


def build_column_headers(periods: list) -> list:
    """Dönem listesinden tablo başlıklarını üretir."""
    quarter_map = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4/FY"}
    headers = []
    for y, p in periods:
        if p == 12:
            headers.append(f"{y}")
        else:
            headers.append(f"{y} {quarter_map.get(p, str(p))}")
    return headers


def build_table(row_keys: list, row_labels: dict, df: pd.DataFrame, lang: str, computed: dict = None) -> pd.DataFrame:
    """
    Verilen satır anahtarlarından formatlanmış DataFrame tablosu oluşturur.
    computed: Hesaplanmış satırlar sözlüğü (key -> {v1..v4})
    """
    lang_key = "TR" if lang == "TR" else "EN"
    data = {}

    for key in row_keys:
        label = row_labels.get(key, key)
        if computed and key in computed:
            vals = computed[key]
        else:
            vals = find_item_value(df, key, lang_key)

        row_data = []
        for i in range(1, 5):
            v = vals.get(f"v{i}") if vals else None
            row_data.append(format_number(v))
        data[label] = row_data

    return pd.DataFrame(data).T


# ─────────────────────────────────────────────
# HESAPLAMALAR
# ─────────────────────────────────────────────
def compute_derived(df: pd.DataFrame, lang: str) -> dict:
    """
    FAVÖK ve Net Borç gibi hesaplanmış kalemleri döndürür.
    """
    computed = {}

    # FAVÖK = Faaliyet Karı + Amortisman
    op_vals = find_item_value(df, "operating_income", lang)
    dep_vals = find_item_value(df, "depreciation", lang)

    ebitda_vals = {}
    for i in range(1, 5):
        op = op_vals.get(f"v{i}") if op_vals else None
        dep = dep_vals.get(f"v{i}") if dep_vals else None
        if op is not None and dep is not None:
            ebitda_vals[f"v{i}"] = op + abs(dep)
        elif op is not None:
            ebitda_vals[f"v{i}"] = op  # Amortisman bulunamadıysa
        else:
            ebitda_vals[f"v{i}"] = None
    computed["ebitda"] = ebitda_vals

    # Net Borç = ST Finansal Borç + LT Finansal Borç - Nakit
    st_debt = find_item_value(df, "st_financial_debt", lang)
    lt_debt = find_item_value(df, "lt_financial_debt", lang)
    cash_vals = find_item_value(df, "cash", lang)

    net_debt_vals = {}
    for i in range(1, 5):
        st = st_debt.get(f"v{i}") if st_debt else None
        lt = lt_debt.get(f"v{i}") if lt_debt else None
        ca = cash_vals.get(f"v{i}") if cash_vals else None
        parts = [x for x in [st, lt, ca] if x is not None]
        if parts:
            st = st or 0
            lt = lt or 0
            ca = ca or 0
            net_debt_vals[f"v{i}"] = st + lt - ca
        else:
            net_debt_vals[f"v{i}"] = None
    computed["net_debt"] = net_debt_vals

    return computed


# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    :root {
        --bg: #0d1117;
        --surface: #161b22;
        --border: #30363d;
        --accent: #58a6ff;
        --accent2: #3fb950;
        --text: #e6edf3;
        --muted: #8b949e;
        --header-bg: #1c2128;
    }

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: var(--surface) !important;
        border-right: 1px solid var(--border);
    }

    /* Ana başlık */
    .main-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--accent);
        letter-spacing: -0.02em;
        margin-bottom: 0;
    }
    .main-subtitle {
        font-size: 0.82rem;
        color: var(--muted);
        margin-bottom: 1.5rem;
    }

    /* Tablo başlıkları */
    .section-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1rem;
        font-weight: 600;
        color: var(--accent);
        border-left: 3px solid var(--accent);
        padding-left: 0.6rem;
        margin: 1.5rem 0 0.5rem 0;
    }

    /* Birim notu */
    .unit-note {
        font-size: 0.72rem;
        color: var(--muted);
        font-family: 'IBM Plex Mono', monospace;
        margin-bottom: 0.4rem;
    }

    /* DataFrame tablosu */
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: 6px;
        overflow: hidden;
    }

    /* Divider */
    hr {
        border-color: var(--border) !important;
        margin: 1.2rem 0;
    }

    /* Ticker badge */
    .ticker-badge {
        display: inline-block;
        background: var(--accent);
        color: #0d1117;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 2px 10px;
        border-radius: 4px;
        margin-left: 8px;
    }

    /* Button */
    .stButton > button {
        background-color: var(--accent2) !important;
        color: #0d1117 !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.4rem 1.2rem !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
    }
    .stButton > button:hover {
        opacity: 0.85 !important;
    }

    /* Info/warning */
    .stAlert {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# UYGULAMA ANA FONKSİYONU
# ─────────────────────────────────────────────
def main():
    inject_css()

    # ── Sidebar ──────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Kontrol Paneli")
        st.divider()

        lang = st.selectbox(
            "🌐 Dil / Language",
            options=["TR", "EN"],
            index=0,
            key="lang_select",
        )
        L = LABELS[lang]

        st.divider()

        ticker = st.selectbox(
            L["ticker"],
            options=sorted(BIST30),
            index=sorted(BIST30).index("THYAO") if "THYAO" in BIST30 else 0,
        )

        period_label_map = {L["quarterly"]: "quarterly", L["annual"]: "annual"}
        period_choice = st.radio(
            L["period_type"],
            options=list(period_label_map.keys()),
        )
        period_type = period_label_map[period_choice]

        st.divider()
        fetch_clicked = st.button(L["fetch_btn"], use_container_width=True)

        st.markdown("""
        <br><small style='color:#8b949e'>
        📡 Kaynak: İş Yatırım<br>
        🔄 Cache: 10 dk
        </small>
        """, unsafe_allow_html=True)

    # ── Ana Ekran Başlığı ────────────────────
    col1, col2 = st.columns([7, 1])
    with col1:
        st.markdown(
            f'<div class="main-title">{L["title"]} '
            f'<span class="ticker-badge">{ticker}</span></div>'
            f'<div class="main-subtitle">{L["subtitle"]}</div>',
            unsafe_allow_html=True,
        )

    # ── Veri Çekme ───────────────────────────
    if not fetch_clicked and "last_df" not in st.session_state:
        st.info("← Soldaki panelden hisse ve periyot seçip 'Verileri Getir' butonuna tıklayın.")
        return

    if fetch_clicked:
        with st.spinner(L["loading"]):
            result = fetch_financial_data(ticker, period_type)
            if result is None:
                st.error(L["error_empty"])
                return
            df_raw, periods = result
            st.session_state["last_df"] = df_raw
            st.session_state["last_periods"] = periods
            st.session_state["last_ticker"] = ticker
    else:
        df_raw = st.session_state.get("last_df")
        periods = st.session_state.get("last_periods")
        if df_raw is None:
            st.error(L["error_empty"])
            return

    # ── Sütun başlıkları ────────────────────
    col_headers = build_column_headers(periods)

    # ── Hesaplamalar ─────────────────────────
    computed = compute_derived(df_raw, lang)

    # ─────────────────────────────────────────
    # TABLO 1: GELİR TABLOSU
    # ─────────────────────────────────────────
    st.markdown(f'<div class="section-title">{L["table1_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="unit-note">💡 {L["unit_note"]}</div>', unsafe_allow_html=True)

    income_keys = ["revenue", "gross_profit", "operating_income", "ebitda", "net_income"]
    try:
        df_income = build_table(
            row_keys=income_keys,
            row_labels=L["rows_income"],
            df=df_raw,
            lang=lang,
            computed=computed,
        )
        df_income.columns = col_headers
        st.dataframe(df_income, use_container_width=True)
    except Exception as e:
        st.error(f"{L['error_parse']}: {e}")

    st.divider()

    # ─────────────────────────────────────────
    # TABLO 2: BİLANÇO
    # ─────────────────────────────────────────
    st.markdown(f'<div class="section-title">{L["table2_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="unit-note">💡 {L["unit_note"]}</div>', unsafe_allow_html=True)

    balance_keys = [
        "current_assets", "non_current_assets", "total_assets",
        "current_liabilities", "non_current_liabilities", "equity", "net_debt"
    ]
    try:
        df_balance = build_table(
            row_keys=balance_keys,
            row_labels=L["rows_balance"],
            df=df_raw,
            lang=lang,
            computed=computed,
        )
        df_balance.columns = col_headers
        st.dataframe(df_balance, use_container_width=True)
    except Exception as e:
        st.error(f"{L['error_parse']}: {e}")

    st.divider()

    # ─────────────────────────────────────────
    # TABLO 3: NAKİT AKIM TABLOSU
    # ─────────────────────────────────────────
    st.markdown(f'<div class="section-title">{L["table3_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="unit-note">💡 {L["unit_note"]}</div>', unsafe_allow_html=True)

    cashflow_keys = ["operating_cf", "investing_cf", "financing_cf"]
    try:
        df_cf = build_table(
            row_keys=cashflow_keys,
            row_labels=L["rows_cashflow"],
            df=df_raw,
            lang=lang,
            computed={},
        )
        df_cf.columns = col_headers
        st.dataframe(df_cf, use_container_width=True)
    except Exception as e:
        st.error(f"{L['error_parse']}: {e}")

    # ── Footer ───────────────────────────────
    st.divider()
    st.markdown(
        '<small style="color:#8b949e">Veriler İş Yatırım halka açık API\'sinden alınmaktadır. '
        'Yatırım tavsiyesi değildir. / Data sourced from İş Yatırım public API. '
        'Not investment advice.</small>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
