import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="BIST Financial & DCF Tool", layout="wide")

st.title("📊 BIST Financial Parser + DCF Valuation")

uploaded_file = st.file_uploader("Excel dosyası yükle", type=["xlsx"])

# --------------------------
# Helpers
# --------------------------

def clean_table(df):
    df = df.copy()
    df = df.rename(columns={df.columns[0]: "Kalem"})
    df = df.dropna(how="all")
    df["Kalem"] = df["Kalem"].astype(str)
    return df


def extract_period(df, period):
    if period not in df.columns:
        return None
    out = df[["Kalem", period]].copy()
    out = out.dropna(subset=[period])
    out = out.rename(columns={period: "Value"})
    return out


def find_value(df, keywords):
    for k in keywords:
        match = df[df["Kalem"].str.lower().str.contains(k)]
        if not match.empty:
            return float(match.iloc[0]["Value"])
    return None


def estimate_metrics(income_df, cash_df):
    revenue = find_value(income_df, ["hasılat", "satış"])
    ebitda = find_value(income_df, ["favök", "ebitda"])
    capex = find_value(cash_df, ["yatırım", "capex"])

    if revenue and ebitda:
        margin = ebitda / revenue
    else:
        margin = 0.2

    if revenue and capex:
        capex_ratio = capex / revenue
    else:
        capex_ratio = 0.05

    return margin, capex_ratio


def calculate_dcf(
    revenue,
    growth,
    margin,
    capex_ratio,
    tax_rate,
    wacc,
    terminal_growth,
    years=5
):

    projections = []

    rev = revenue

    for y in range(1, years + 1):

        rev = rev * (1 + growth)
        ebitda = rev * margin
        ebit = ebitda * 0.85
        tax = ebit * tax_rate
        nopat = ebit - tax
        capex = rev * capex_ratio
        fcf = nopat - capex

        discount = 1 / ((1 + wacc) ** y)
        pv = fcf * discount

        projections.append([y, rev, ebitda, fcf, pv])

    df = pd.DataFrame(
        projections,
        columns=["Year", "Revenue", "EBITDA", "FCF", "PV"]
    )

    terminal_value = (
        df.iloc[-1]["FCF"]
        * (1 + terminal_growth)
        / (wacc - terminal_growth)
    )

    terminal_pv = terminal_value / ((1 + wacc) ** years)

    enterprise_value = df["PV"].sum() + terminal_pv

    return df, enterprise_value


def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


# --------------------------
# App
# --------------------------

if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names

    st.success(f"Sheets: {sheets}")

    data = {}

    for sheet in sheets:
        df = pd.read_excel(uploaded_file, sheet_name=sheet)
        df = clean_table(df)
        data[sheet] = df

    sample_sheet = list(data.keys())[0]
    periods = [c for c in data[sample_sheet].columns if c != "Kalem"]

    period = st.selectbox("Dönem seç", periods)

    extracted = {}

    for name, df in data.items():
        table = extract_period(df, period)
        if table is not None:
            extracted[name] = table
            st.subheader(name)
            st.dataframe(table, use_container_width=True)

    # Try auto estimation
    income_df = None
    cash_df = None

    for name in extracted.keys():
        if "gelir" in name.lower():
            income_df = extracted[name]
        if "nakit" in name.lower():
            cash_df = extracted[name]

    if income_df is not None:

        revenue = find_value(income_df, ["hasılat", "satış"])

        if revenue:

            st.header("DCF Varsayımları")

            auto_margin = 0.2
            auto_capex = 0.05

            if cash_df is not None:
                auto_margin, auto_capex = estimate_metrics(income_df, cash_df)

            col1, col2, col3 = st.columns(3)

            growth = col1.number_input("Revenue Growth %", 0.0, 1.0, 0.10)
            margin = col2.number_input("EBITDA Margin", 0.0, 1.0, float(auto_margin))
            wacc = col3.number_input("WACC", 0.0, 1.0, 0.20)

            col4, col5, col6 = st.columns(3)

            capex_ratio = col4.number_input("CapEx Ratio", 0.0, 1.0, float(auto_capex))
            tax_rate = col5.number_input("Tax Rate", 0.0, 1.0, 0.25)
            terminal_growth = col6.number_input("Terminal Growth", 0.0, 1.0, 0.05)

            years = st.slider("Projection Years", 3, 10, 5)

            if st.button("Calculate DCF"):

                dcf_df, ev = calculate_dcf(
                    revenue,
                    growth,
                    margin,
                    capex_ratio,
                    tax_rate,
                    wacc,
                    terminal_growth,
                    years
                )

                st.subheader("DCF Projection")
                st.dataframe(dcf_df, use_container_width=True)

                st.metric("Enterprise Value", f"{ev:,.0f}")

                fig, ax = plt.subplots()
                ax.plot(dcf_df["Year"], dcf_df["Revenue"])
                ax.set_title("Revenue Projection")
                st.pyplot(fig)

                excel_bytes = to_excel(dcf_df)

                st.download_button(
                    "DCF Excel indir",
                    excel_bytes,
                    file_name="dcf_model.xlsx"
                )
