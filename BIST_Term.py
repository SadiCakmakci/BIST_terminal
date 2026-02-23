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
        .stApp {
            background-color: #0d1117;
            color: #c9d1d9;
        }
        section[data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }
        section[data-testid="stSidebar"] * {
            color: #c9d1d9 !important;
        }
        h1, h2, h3 {
            font-family: 'IBM Plex Mono', monospace !important;
            color: #58a6ff !important;
            letter-spacing: -0.5px;
        }
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
        .err-box {
            background: #2d1b1b;
            border: 1px solid #f85149;
            border-radius: 8px;
            padding: 16px;
            color: #f85149;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.85rem;
        }
        .info-box {
            background: #1c2a3a;
            border: 1px solid #388bfd;
            border-radius: 8px;
            padding: 14px 18px;
            color: #c9d1d9;
            font-size: 0.85rem;
        }
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
# SABİTLER
# ─────────────────────────────────────────────
POPULER_HISSELER = [
    "THYAO.IS", "TUPRS.IS", "SASA.IS", "ASELS.IS", "EREGL.IS",
    "BIMAS.IS", "AKBNK.IS", "GARAN.IS", "ISCTR.IS", "KCHOL.IS",
    "KOZAL.IS", "SISE.IS", "TOASO.IS", "FROTO.IS", "PGSUS.IS",
]

# yfinance eski snake_case ve yeni camelCase satır adlarını birlikte kapsıyoruz.
# Anahtar: yfinance satır adı küçük+strip hali | Değer: Türkçe gösterim
GELIR_ESLESTIRME = {
    # ── Eski snake_case (yfinance < 0.2) ─────────────────────────────────────
    "total revenue":                                "Toplam Gelir",
    "gross profit":                                 "Brüt Kâr",
    "operating income":                             "Faaliyet Kârı",
    "ebit":                                         "FAVÖK (EBIT)",
    "ebitda":                                       "FAVÖK (EBITDA)",
    "net income":                                   "Net Kâr/Zarar",
    "net income common stockholders":               "Net Kâr/Zarar",
    "basic eps":                                    "Hisse Başına Kâr",
    "diluted eps":                                  "Seyreltilmiş HBK",
    # ── Yeni PascalCase (yfinance >= 0.2.18) ──────────────────────────────────
    "totalrevenue":                                 "Toplam Gelir",
    "grossprofit":                                  "Brüt Kâr",
    "operatingincome":                              "Faaliyet Kârı",
    "operatingrevenue":                             "Faaliyet Geliri",
    "normalizedebitda":                             "FAVÖK (EBITDA)",
    "netincome":                                    "Net Kâr/Zarar",
    "netincomefromcontinuingoperations":            "Net Kâr/Zarar",
    "netincomecommonstock":                         "Net Kâr/Zarar",
    "basiceps":                                     "Hisse Başına Kâr",
    "dilutedeps":                                   "Seyreltilmiş HBK",
    "costofrevenue":                                "Satışların Maliyeti",
    "cost of revenue":                              "Satışların Maliyeti",
    "researchanddevelopment":                       "Ar-Ge Giderleri",
    "research and development":                     "Ar-Ge Giderleri",
    "sellinggeneralandadministration":              "SG&A Giderleri",
    "selling general and administrative":           "SG&A Giderleri",
    "interestexpense":                              "Faiz Gideri",
    "interest expense":                             "Faiz Gideri",
    "interestincome":                               "Faiz Geliri",
    "interest income":                              "Faiz Geliri",
    "taxprovision":                                 "Vergi Karşılığı",
    "tax provision":                                "Vergi Karşılığı",
}

BILANCO_ESLESTIRME = {
    # ── Eski snake_case ───────────────────────────────────────────────────────
    "total assets":                                 "Toplam Varlıklar",
    "current assets":                               "Dönen Varlıklar",
    "cash and cash equivalents":                    "Nakit & Benzerleri",
    "cash cash equivalents and short term investments": "Nakit & Benzerleri",
    "total liabilities net minority interest":      "Toplam Yükümlülükler",
    "total liabilities":                            "Toplam Yükümlülükler",
    "current liabilities":                          "Kısa Vadeli Yükümlülükler",
    "long term debt":                               "Uzun Vadeli Borç",
    "stockholders equity":                          "Özsermaye",
    "common stock equity":                          "Özsermaye",
    "retained earnings":                            "Birikmiş Kârlar",
    # ── Yeni PascalCase ───────────────────────────────────────────────────────
    "totalassets":                                  "Toplam Varlıklar",
    "currentassets":                                "Dönen Varlıklar",
    "cashandcashequivalents":                       "Nakit & Benzerleri",
    "cashcashequivalentsandshortterminvestments":   "Nakit & Benzerleri",
    "totalliabilitiesnetsminorityinterest":         "Toplam Yükümlülükler",
    "totalliabilitiesnetminorityinterest":          "Toplam Yükümlülükler",
    "currentliabilities":                           "Kısa Vadeli Yükümlülükler",
    "longtermdebt":                                 "Uzun Vadeli Borç",
    "longtermdebtnoncurrent":                       "Uzun Vadeli Borç",
    "stockholdersequity":                           "Özsermaye",
    "commonstockequity":                            "Özsermaye",
    "retainedearnings":                             "Birikmiş Kârlar",
    "noncurrentliabilities":                        "Uzun Vadeli Yükümlülükler",
    "noncurrentassets":                             "Duran Varlıklar",
    "netppe":                                       "Maddi Duran Varlıklar (Net)",
    "net ppe":                                      "Maddi Duran Varlıklar (Net)",
    "inventory":                                    "Stoklar",
    "accountsreceivable":                           "Ticari Alacaklar",
    "accounts receivable":                          "Ticari Alacaklar",
    "workingcapital":                               "Net Çalışma Sermayesi",
}


# ─────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def hisse_bilgisi_getir(ticker_kodu: str) -> dict:
    """Hisse özet bilgisini yfinance'den çeker."""
    try:
        ticker = yf.Ticker(ticker_kodu)
        info = ticker.info or {}
        return {
            "sirket_adi": info.get("longName", ticker_kodu),
            "sektor":     info.get("sector", "—"),
            "para_birimi": info.get("currency", "TRY"),
        }
    except Exception:
        return {"sirket_adi": ticker_kodu, "sektor": "—", "para_birimi": "TRY"}


@st.cache_data(ttl=3600, show_spinner=False)
def finansal_veri_getir(ticker_kodu: str, donem: str) -> dict:
    """
    Gelir Tablosu ve Bilanço verilerini çeker.
    donem: "Çeyreklik" | "Yıllık"

    yfinance bazı hisselerde DataFrame'i TRANSPOSED döndürebilir
    (dönemler satırda, kalemler sütunda). _normalize_df() bunu düzeltir.
    """
    try:
        ticker = yf.Ticker(ticker_kodu)

        ceyreklik = (donem == "Çeyreklik")

        # Yeni API adları (yfinance >= 0.2.18)
        gelir   = ticker.quarterly_income_stmt   if ceyreklik else ticker.income_stmt
        bilanco = ticker.quarterly_balance_sheet if ceyreklik else ticker.balance_sheet

        # Eski API fallback
        if gelir is None or (hasattr(gelir, "empty") and gelir.empty):
            gelir = ticker.quarterly_financials if ceyreklik else ticker.financials

        return {
            "gelir_tablosu": _normalize_df(gelir),
            "bilanco":        _normalize_df(bilanco),
        }

    except Exception as e:
        return {"hata": str(e), "gelir_tablosu": None, "bilanco": None}


def _normalize_df(df) -> pd.DataFrame | None:
    """
    Satırlar=kalemler, sütunlar=dönemler olacak şekilde normalize eder.
    yfinance bazı durumlarda transpozunu döndürür; index'e bakarak anlarız.
    """
    if df is None:
        return None
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    # İlk index değeri Timestamp ise → transpozlanmış
    if isinstance(df.index[0], pd.Timestamp):
        df = df.T
    return df


def _kolon_formatla(col) -> str:
    """Timestamp veya string sütun adını YYYY-AA formatına çevirir."""
    try:
        if hasattr(col, "strftime"):
            return col.strftime("%Y-%m")
        return str(col)[:10]
    except Exception:
        return str(col)


def _sayi_formatla(x) -> str:
    """
    Sayıyı USD cinsinden okunabilir biçimde gösterir.
    yfinance verileri zaten USD olarak döner.

    ≥ 1B  → $1.23B
    ≥ 1M  → $1.23M
    ≥ 1K  → $1.23K
    diğer → $1.23
    """
    try:
        val = float(x)
        if pd.isna(val):
            return "—"
        sign = "-" if val < 0 else ""
        abs_val = abs(val)
        if abs_val >= 1e9:
            return f"{sign}${abs_val / 1e9:,.2f}B"
        elif abs_val >= 1e6:
            return f"{sign}${abs_val / 1e6:,.2f}M"
        elif abs_val >= 1e3:
            return f"{sign}${abs_val / 1e3:,.2f}K"
        else:
            return f"{sign}${abs_val:,.2f}"
    except (TypeError, ValueError):
        return str(x) if x is not None else "—"


def df_hazirla(df: pd.DataFrame, eslestirme: dict, para_birimi: str) -> pd.DataFrame | None:
    """
    Ham DataFrame'i alır:
      1. Eşleştirme tablosuna göre istenen satırları seçer ve Türkçeleştirir.
      2. Sütun adlarını tarihe çevirir.
      3. Sayıları biçimlendirir (Pandas 2.x uyumlu: applymap → map).
    """
    if df is None or df.empty:
        return None

    df = df.copy()

    # ── 1. Satır seçimi & Türkçeleştirme ────────────────────────────────────
    secilen = {}   # {orijinal_index: türkçe_ad}
    for orig_idx in df.index:
        anahtar = str(orig_idx).lower().strip()
        # Birebir eşleşme
        if anahtar in eslestirme:
            secilen[orig_idx] = eslestirme[anahtar]
            continue
        # Kısmi eşleşme (camelCase / boşluk farkı)
        for pattern, tr_ad in eslestirme.items():
            if pattern in anahtar or anahtar in pattern:
                if orig_idx not in secilen:
                    secilen[orig_idx] = tr_ad
                break

    if not secilen:
        # Eşleşme yoksa tüm satırları ham haliyle göster
        secili_idx = list(df.index)
        tr_adlar   = [str(i) for i in secili_idx]
    else:
        # Aynı Türkçe ada karşılık gelen ilk satırı al (duplicate önleme)
        gorulmus = set()
        secili_idx, tr_adlar = [], []
        for orig, tr in secilen.items():
            if tr not in gorulmus:
                secili_idx.append(orig)
                tr_adlar.append(tr)
                gorulmus.add(tr)

    sonuc = df.loc[secili_idx].copy()
    sonuc.index = pd.Index(tr_adlar, name="Kalem (USD)")

    # ── 2. Sütun adları ──────────────────────────────────────────────────────
    sonuc.columns = pd.Index([_kolon_formatla(c) for c in sonuc.columns])
    # Duplicate sütunları kaldır
    sonuc = sonuc.loc[:, ~sonuc.columns.duplicated()]

    # ── 3. Sayı formatlama (Pandas 2.x: applymap() kaldırıldı → map() kullan)
    sonuc = sonuc.apply(lambda col: col.map(_sayi_formatla))

    return sonuc


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
    st.markdown(
        """
        <div style='font-size:0.72rem;color:#484f58;line-height:1.8'>
        Veri Kaynağı: <b>yfinance</b><br>
        Güncelleme: ~60 dk. önbellek<br>
        Birim: USD · $1.23B / $1.23M / $1.23K
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

if not ticker_kodu:
    st.markdown(
        '<div class="info-box">👈 Sol menüden bir hisse senedi seçerek başlayın.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Hisse Özet Kartı ─────────────────────────────────────────────────────────
info = hisse_bilgisi_getir(ticker_kodu)

st.markdown(
    f"""
    <div class="price-card">
        <div class="ticker">{ticker_kodu}</div>
        <div class="company">
            {info['sirket_adi']} &nbsp;·&nbsp; {info['sektor']} &nbsp;·&nbsp; USD
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Veri Yükleme ─────────────────────────────────────────────────────────────
with st.spinner(f"{ticker_kodu} için {donem.lower()} veriler yükleniyor…"):
    veriler = finansal_veri_getir(ticker_kodu, donem)

if "hata" in veriler:
    st.markdown(
        f'<div class="err-box">⚠️ Veri çekilirken hata oluştu:<br>'
        f'<code>{veriler["hata"]}</code></div>',
        unsafe_allow_html=True,
    )
    st.stop()

gelir_df_ham   = veriler.get("gelir_tablosu")
bilanco_df_ham = veriler.get("bilanco")

# ─────────────────────────────────────────────
# GELİR TABLOSU
# ─────────────────────────────────────────────
st.markdown("## 📋 Özet Gelir Tablosu")

if gelir_df_ham is not None and not gelir_df_ham.empty:
    gelir_df = df_hazirla(gelir_df_ham, GELIR_ESLESTIRME, info["para_birimi"])
    if gelir_df is not None and not gelir_df.empty:
        st.dataframe(gelir_df, use_container_width=True)
    else:
        st.markdown(
            '<div class="info-box">ℹ️ Gelir tablosu için eşleşen kalem bulunamadı.</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        '<div class="info-box">ℹ️ Gelir tablosu verisi bulunamadı. '
        'Bu hisse için yfinance veri sağlamıyor olabilir.</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# BİLANÇO
# ─────────────────────────────────────────────
st.markdown("## 🏦 Özet Bilanço")

if bilanco_df_ham is not None and not bilanco_df_ham.empty:
    bilanco_df = df_hazirla(bilanco_df_ham, BILANCO_ESLESTIRME, info["para_birimi"])
    if bilanco_df is not None and not bilanco_df.empty:
        st.dataframe(bilanco_df, use_container_width=True)
    else:
        st.markdown(
            '<div class="info-box">ℹ️ Bilanço için eşleşen kalem bulunamadı.</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        '<div class="info-box">ℹ️ Bilanço verisi bulunamadı. '
        'Bu hisse için yfinance veri sağlamıyor olabilir.</div>',
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
