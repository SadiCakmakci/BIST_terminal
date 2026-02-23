import streamlit as st
import pandas as pd
import io

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Financial Table Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── TRANSLATIONS ─────────────────────────────────────────────────────────────
LANG = {
    "TR": {
        "app_title": "📊 Finansal Tablo Görüntüleyici",
        "app_subtitle": "Excel veya CSV dosyanızı yükleyerek finansal tablonuzu şık bir şekilde görüntüleyin.",
        "sidebar_header": "⚙️ Ayarlar",
        "lang_label": "🌐 Dil / Language",
        "upload_label": "📂 Dosya Yükle (.xlsx veya .csv)",
        "upload_help": "Yalnızca .xlsx ve .csv formatları desteklenmektedir.",
        "no_file": "⬅️ Başlamak için sol menüden bir dosya yükleyin.",
        "preview_title": "📋 Tablo Önizlemesi",
        "rows_label": "Satır",
        "cols_label": "Sütun",
        "numeric_cols": "Sayısal Sütunlar",
        "sheet_label": "📄 Sayfa Seç",
        "success": "✅ Dosya başarıyla yüklendi.",
        "error_read": "❌ Dosya okunurken bir hata oluştu:",
        "error_empty": "⚠️ Yüklenen dosya boş görünüyor.",
        "stats_title": "📐 Genel Bilgiler",
        "footer": "Veri API'ye gönderilmez · Tüm veriler yerel olarak işlenir",
    },
    "EN": {
        "app_title": "📊 Financial Table Viewer",
        "app_subtitle": "Upload your Excel or CSV file to display your financial statements elegantly.",
        "sidebar_header": "⚙️ Settings",
        "lang_label": "🌐 Language / Dil",
        "upload_label": "📂 Upload File (.xlsx or .csv)",
        "upload_help": "Only .xlsx and .csv formats are supported.",
        "no_file": "⬅️ Upload a file from the sidebar to get started.",
        "preview_title": "📋 Table Preview",
        "rows_label": "Rows",
        "cols_label": "Columns",
        "numeric_cols": "Numeric Columns",
        "sheet_label": "📄 Select Sheet",
        "success": "✅ File loaded successfully.",
        "error_read": "❌ An error occurred while reading the file:",
        "error_empty": "⚠️ The uploaded file appears to be empty.",
        "stats_title": "📐 Summary",
        "footer": "Data is not sent to any API · All processing is local",
    },
}

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 50%, #0f1117 100%);
        color: #e8eaf0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141621 0%, #1e2235 100%);
        border-right: 1px solid #2d3354;
    }

    [data-testid="stSidebar"] * {
        color: #c8cce0 !important;
    }

    /* Title */
    .main-title {
        font-family: 'DM Serif Display', serif;
        font-size: 2.4rem;
        color: #a8b4ff;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }

    .main-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 2rem;
        font-weight: 300;
    }

    /* Stat cards */
    .stat-card {
        background: linear-gradient(135deg, #1e2235, #252a40);
        border: 1px solid #2d3354;
        border-radius: 12px;
        padding: 1rem 1.4rem;
        text-align: center;
    }

    .stat-label {
        font-size: 0.72rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    .stat-value {
        font-family: 'DM Mono', monospace;
        font-size: 1.6rem;
        color: #a8b4ff;
        font-weight: 500;
        margin-top: 0.2rem;
    }

    /* Dataframe overrides */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #2d3354;
    }

    /* Success / error */
    .stAlert {
        border-radius: 10px;
    }

    /* Footer */
    .footer-text {
        font-size: 0.72rem;
        color: #374151;
        text-align: center;
        margin-top: 3rem;
        font-family: 'DM Mono', monospace;
        letter-spacing: 0.5px;
    }

    /* Divider */
    hr {
        border-color: #2d3354;
        margin: 1.5rem 0;
    }

    /* Section heading */
    .section-heading {
        font-family: 'DM Serif Display', serif;
        font-size: 1.15rem;
        color: #8892c8;
        margin-bottom: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")

    # Language selector (always first)
    lang_choice = st.radio(
        "🌐 Dil / Language",
        options=["TR", "EN"],
        horizontal=True,
        label_visibility="collapsed",
    )
    T = LANG[lang_choice]

    st.markdown(f"### {T['sidebar_header']}")
    st.markdown("---")

    # File uploader
    uploaded_file = st.file_uploader(
        T["upload_label"],
        type=["xlsx", "csv"],
        help=T["upload_help"],
    )

    st.markdown("---")
    st.markdown(f"<p style='font-size:0.7rem;color:#4b5563;text-align:center'>{T['footer']}</p>", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def format_number(val):
    """Format numeric values with thousands separator."""
    try:
        if pd.isna(val):
            return "-"
        if isinstance(val, (int, float)):
            if val == int(val):
                return f"{int(val):,}".replace(",", ".")
            return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return val
    except Exception:
        return val


def load_file(file) -> tuple[pd.DataFrame | None, str | None, list[str]]:
    """Load xlsx or csv; return (df, error_msg, sheet_names)."""
    name = file.name.lower()
    sheets = []
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(file, thousands=None)
            return df, None, []
        else:
            xf = pd.ExcelFile(file)
            sheets = xf.sheet_names
            return None, None, sheets  # caller will pick sheet
    except Exception as e:
        return None, str(e), []


def read_sheet(file, sheet_name: str) -> tuple[pd.DataFrame | None, str | None]:
    try:
        df = pd.read_excel(file, sheet_name=sheet_name)
        return df, None
    except Exception as e:
        return None, str(e)


# ── MAIN ──────────────────────────────────────────────────────────────────────
st.markdown(f"<p class='main-title'>{T['app_title']}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='main-subtitle'>{T['app_subtitle']}</p>", unsafe_allow_html=True)

if uploaded_file is None:
    st.info(T["no_file"])
    st.stop()

# ── FILE LOADING ──────────────────────────────────────────────────────────────
file_name = uploaded_file.name.lower()

if file_name.endswith(".csv"):
    df, err = None, None
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        err = str(e)

    if err:
        st.error(f"{T['error_read']} {err}")
        st.stop()
    if df is None or df.empty:
        st.warning(T["error_empty"])
        st.stop()

else:  # xlsx
    try:
        xf = pd.ExcelFile(uploaded_file)
        sheet_names = xf.sheet_names
    except Exception as e:
        st.error(f"{T['error_read']} {e}")
        st.stop()

    if len(sheet_names) > 1:
        selected_sheet = st.selectbox(T["sheet_label"], options=sheet_names)
    else:
        selected_sheet = sheet_names[0]

    try:
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
    except Exception as e:
        st.error(f"{T['error_read']} {e}")
        st.stop()

    if df is None or df.empty:
        st.warning(T["error_empty"])
        st.stop()

# ── FILL NaN ──────────────────────────────────────────────────────────────────
# Keep a copy with original dtypes for display formatting
df_display = df.copy()

# Identify numeric columns BEFORE filling
numeric_cols = df_display.select_dtypes(include="number").columns.tolist()

# Fill NaN with "-"
df_display = df_display.fillna("-")

# ── FORMAT NUMERIC COLUMNS ────────────────────────────────────────────────────
for col in numeric_cols:
    df_display[col] = df_display[col].apply(
        lambda v: format_number(v) if v != "-" else "-"
    )

# ── STATS ROW ─────────────────────────────────────────────────────────────────
st.success(T["success"])
st.markdown(f"<p class='section-heading'>{T['stats_title']}</p>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f"""<div class="stat-card">
            <div class="stat-label">{T['rows_label']}</div>
            <div class="stat-value">{str(len(df)).replace(",", ".")}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""<div class="stat-card">
            <div class="stat-label">{T['cols_label']}</div>
            <div class="stat-value">{len(df.columns)}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""<div class="stat-card">
            <div class="stat-label">{T['numeric_cols']}</div>
            <div class="stat-value">{len(numeric_cols)}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── TABLE ─────────────────────────────────────────────────────────────────────
st.markdown(f"<p class='section-heading'>{T['preview_title']}</p>", unsafe_allow_html=True)

st.dataframe(
    df_display,
    use_container_width=True,
    height=min(600, 60 + len(df_display) * 35),
)

st.markdown(
    f"<p class='footer-text'>{T['footer']}</p>",
    unsafe_allow_html=True,
)
