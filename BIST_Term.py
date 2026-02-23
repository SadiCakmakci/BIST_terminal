"""
BİST Finansal Analiz Uygulaması - MVP (Aşama 1)
Gereksinimler: pip install streamlit yfinance pandas
Çalıştırma   : streamlit run bist_analiz.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd

# ─────────────────────────────────────────────
# SAYFA AYARLARI
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BİST Finansal Analiz",
    page_icon="📊",
    layout="wide",
)

# ─────────────────────────────────────────────
# ÖZEL CSS
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans', sans-serif;
        }

        /* Genel arka plan */
        .stApp {
            background-color: #0d1117;
            color: #c9d1d9;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }
        section[data-testid="stSidebar"] * {
            color: #c9d1d9 !important;
        }

        /* Başlık */
        h1, h2, h3 {
            font-family: 'IBM Plex Mono', monospace !important;
            color: #58a6ff !important;
            letter-spacing: -0.5px;
        }

        /* Tablo */
        .dataframe {
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
            overflow: hidden;
            font-family: 'IBM Plex Mono', monospace !important;
            font-size: 0.82rem !important;
        }
        .dataframe thead tr th {
            background-color: #1f2937 !important;
            color: #58a6ff !important;
            font-weight: 600 !important;
            border-bottom: 2px solid #388bfd !important;
        }
        .dataframe tbody tr:nth-child(even) td {
            background-color: #161b22 !important;
        }
        .dataframe tbody tr:hover td {
            background-color: #1f2937 !important;
        }
        .dataframe td, .dataframe th {
            border-color: #30363d !important;
            padding: 8px 14px !important;
        }

        /* Etiket/rozet */
        .badge {
            display: inline-block;
            background: #388bfd22;
            border: 1px solid #388bfd;
            color: #58a6ff;
            border-radius: 20px;
            padding: 2px 12px;
            font-size: 0.75rem;
            font-family: 'IBM Plex Mono', monospace;
            margin-bottom: 6px;
        }

        /* Hata mesajı */
        .err-box {
            background: #2d1b1b;
            border: 1px solid #f85149;
            border-radius: 8px;
            padding: 16px;
            color: #f85149;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.85rem;
        }

        /* Bilgi kutusu */
        .info-box {
            background: #1c2a3a;
            border: 1px solid #388bfd;
            border-radius: 8px;
            padding: 14px 18px;
            color: #c9d1d9;
            font-size: 0.85rem;
        }

        /* Stok fiyat kartı */
        .price-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 18px 24px;
            margin-bottom: 8px;
        }
        .price-card .ticker {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.4rem;
            font-weight: 600;
            color: #58a6ff;
        }
        .price-card .company {
            font-size: 0.85rem;
            color: #8b949e;
            margin-top: 2px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# VERİ ÇEKME FONKSİYONLARI
# ─────────────────────────────────────────────
POPULER_HISSELER = [
    "THYAO.IS", "TUPRS.IS", "SASA.IS", "ASELS.IS", "EREGL.IS",
    "BIMAS.IS", "AKBNK.IS", "GARAN.IS", "ISCTR.IS", "KCHOL.IS",
    "KOZAL.IS", "SISE.IS", "TOASO.IS", "FROTO.IS", "PGSUS.IS",
]


@st.cache_data(ttl=3600, show_spinner=False)
def hisse_bilgisi_getir(ticker_kodu: str) -> dict:
    """Hisse özet bilgisini yfinance'den çeker."""
    try:
        ticker = yf.Ticker(ticker_kodu)
        info = ticker.info or {}
        return {
            "sirket_adi": info.get("longName", ticker_kodu),
            "sektor": info.get("sector", "—"),
            "para_birimi": info.get("currency", "TRY"),
        }
    except Exception:
        return {"sirket_adi": ticker_kodu, "sektor": "—", "para_birimi": "TRY"}


@st.cache_data(ttl=3600, show_spinner=False)
def finansal_veri_getir(ticker_kodu: str, donem: str) -> dict[str, pd.DataFrame | None]:
    """
    Gelir Tablosu ve Bilanço verilerini çeker.
    donem: "Çeyreklik" | "Yıllık"
    """
    try:
        ticker = yf.Ticker(ticker_kodu)

        if donem == "Çeyreklik":
            gelir = ticker.quarterly_financials
            bilanco = ticker.quarterly_balance_sheet
        else:
            gelir = ticker.financials
            bilanco = ticker.balance_sheet

        return {"gelir_tablosu": gelir, "bilanco": bilanco}

    except Exception as e:
        return {"hata": str(e), "gelir_tablosu": None, "bilanco": None}


def df_formatla(df: pd.DataFrame, para_birimi: str = "TRY") -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df = df.copy()

    # Tarih sütunlarını güvenli stringe çevir
    yeni_kolonlar = []
    for col in df.columns:
        try:
            if hasattr(col, "year"):
                yeni_kolonlar.append(f"{col.year}-{col.month:02d}")
            else:
                yeni_kolonlar.append(str(col))
        except:
            yeni_kolonlar.append(str(col))

    # Duplicate kolonları kaldır
    df.columns = pd.Index(yeni_kolonlar)
    df = df.loc[:, ~df.columns.duplicated()]

    # Sayı formatlama
    def sayi_formatla(x):
        try:
            val = float(x)
            if abs(val) >= 1e9:
                return f"{val/1e9:,.2f} Mr"
            elif abs(val) >= 1e6:
                return f"{val/1e6:,.2f} Mn"
            else:
                return f"{val:,.0f}"
        except:
            return x

    return df.applymap(sayi_formatla)


def ozet_satirlar_sec(df: pd.DataFrame, anahtar_satirlar: list[str]) -> pd.DataFrame:
    """İstenen özet satırları filtreler (büyük/küçük harf duyarsız kısmi eşleşme)."""
    if df is None or df.empty:
        return df
    bulunan = []
    for satir in anahtar_satirlar:
        eslesme = [idx for idx in df.index if satir.lower() in str(idx).lower()]
        bulunan.extend(eslesme)
    # Tekrarları kaldır, sırası koru
    seen = set()
    bulunan = [x for x in bulunan if not (x in seen or seen.add(x))]
    return df.loc[bulunan] if bulunan else df


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 BİST Analiz")
    st.markdown("---")

    secim_tipi = st.radio(
        "Hisse Giriş Yöntemi",
        ["Listeden Seç", "Manuel Gir"],
        horizontal=True,
    )

    if secim_tipi == "Listeden Seç":
        ticker_kodu = st.selectbox(
            "Hisse Senedi",
            options=POPULER_HISSELER,
            index=0,
        )
    else:
        ticker_kodu = st.text_input(
            "Hisse Kodu (örn: THYAO.IS)",
            value="THYAO.IS",
            max_chars=20,
        ).upper().strip()

    st.markdown("---")

    donem = st.radio(
        "Dönem Seçimi",
        ["Çeyreklik", "Yıllık"],
        index=0,
    )

    st.markdown("---")
    veri_cek = st.button("🔄 Verileri Getir", use_container_width=True, type="primary")

    st.markdown(
        """
        <div style='margin-top:24px;font-size:0.72rem;color:#484f58;line-height:1.6'>
        Veri Kaynağı: <b>yfinance</b><br>
        Güncelleme: ~60 dk. önbellek<br>
        Birim: Milyar (Mr) / Milyon (Mn)
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
# ANA EKRAN
# ─────────────────────────────────────────────
st.markdown("# BİST Finansal Analiz Platformu")
st.markdown(
    f'<span class="badge">MVP — Aşama 1</span> '
    f'<span class="badge">{donem} Veri</span>',
    unsafe_allow_html=True,
)
st.markdown("---")

# Başlangıç durumu: hiç ticker seçilmemişse yönlendirme
if not ticker_kodu:
    st.markdown(
        '<div class="info-box">👈 Sol menüden bir hisse senedi seçerek başlayın.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Hisse Özet Kartı ──────────────────────────
info = hisse_bilgisi_getir(ticker_kodu)
st.markdown(
    f"""
    <div class="price-card">
        <div class="ticker">{ticker_kodu}</div>
        <div class="company">{info['sirket_adi']} &nbsp;·&nbsp; {info['sektor']} &nbsp;·&nbsp; {info['para_birimi']}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Veri Yükleme ─────────────────────────────
with st.spinner(f"{ticker_kodu} için {donem.lower()} veriler yükleniyor…"):
    veriler = finansal_veri_getir(ticker_kodu, donem)

if "hata" in veriler:
    st.markdown(
        f'<div class="err-box">⚠️ Veri çekilirken hata oluştu:<br><code>{veriler["hata"]}</code></div>',
        unsafe_allow_html=True,
    )
    st.stop()

gelir_df_ham = veriler.get("gelir_tablosu")
bilanco_df_ham = veriler.get("bilanco")

# ─────────────────────────────────────────────
# GELİR TABLOSU
# ─────────────────────────────────────────────
st.markdown("## 📋 Özet Gelir Tablosu")

GELIR_SATIRLARI = [
    "Total Revenue",
    "Gross Profit",
    "Operating Income",
    "EBITDA",
    "Net Income",
    "Basic EPS",
]

if gelir_df_ham is not None and not gelir_df_ham.empty:
    gelir_ozet = ozet_satirlar_sec(gelir_df_ham, GELIR_SATIRLARI)
    gelir_formatli = df_formatla(gelir_ozet, info["para_birimi"])

    # Satır isimlerini Türkçeleştir
    GELIR_TR = {
        "Total Revenue": "Toplam Gelir",
        "Gross Profit": "Brüt Kâr",
        "Operating Income": "Faaliyet Kârı",
        "EBITDA": "FAVÖK",
        "Net Income": "Net Kâr/Zarar",
        "Basic EPS": "Hisse Başına Kâr",
    }
    gelir_formatli.index = [
        GELIR_TR.get(idx, idx) for idx in gelir_formatli.index
    ]
    gelir_formatli.index.name = f"Kalem ({info['para_birimi']})"

    st.dataframe(gelir_formatli, use_container_width=True)
else:
    st.markdown(
        '<div class="info-box">ℹ️ Gelir tablosu verisi bulunamadı.</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# BİLANÇO
# ─────────────────────────────────────────────
st.markdown("## 🏦 Özet Bilanço")

BILANCO_SATIRLARI = [
    "Total Assets",
    "Current Assets",
    "Cash",
    "Total Liabilities",
    "Current Liabilities",
    "Long Term Debt",
    "Stockholders Equity",
    "Retained Earnings",
]

if bilanco_df_ham is not None and not bilanco_df_ham.empty:
    bilanco_ozet = ozet_satirlar_sec(bilanco_df_ham, BILANCO_SATIRLARI)
    bilanco_formatli = df_formatla(bilanco_ozet, info["para_birimi"])

    BILANCO_TR = {
        "Total Assets": "Toplam Varlıklar",
        "Current Assets": "Dönen Varlıklar",
        "Cash": "Nakit & Nakit Benzerleri",
        "Total Liabilities": "Toplam Yükümlülükler",
        "Current Liabilities": "Kısa Vadeli Yükümlülükler",
        "Long Term Debt": "Uzun Vadeli Borç",
        "Stockholders Equity": "Özsermaye",
        "Retained Earnings": "Birikmiş Kârlar",
    }
    bilanco_formatli.index = [
        BILANCO_TR.get(idx, idx) for idx in bilanco_formatli.index
    ]
    bilanco_formatli.index.name = f"Kalem ({info['para_birimi']})"

    st.dataframe(bilanco_formatli, use_container_width=True)
else:
    st.markdown(
        '<div class="info-box">ℹ️ Bilanço verisi bulunamadı.</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center;font-size:0.72rem;color:#484f58;padding:8px 0'>
    BİST Finansal Analiz Platformu · MVP Aşama 1 · Veri: yfinance · Yatırım tavsiyesi değildir.
    </div>
    """,
    unsafe_allow_html=True,
)
