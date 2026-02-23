import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="BIST Financial Parser", layout="wide")

st.title("📊 BIST Financial Statement Parser")

uploaded_file = st.file_uploader("Excel dosyası yükle", type=["xlsx"])

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


def to_excel_output(tables):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name, index=False)
    return output.getvalue()


if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names

    st.success(f"Bulunan sheetler: {sheets}")

    data = {}

    for sheet in sheets:
        df = pd.read_excel(uploaded_file, sheet_name=sheet)
        df = clean_table(df)
        data[sheet] = df

    # Period list
    sample_sheet = list(data.keys())[0]
    periods = [c for c in data[sample_sheet].columns if c != "Kalem"]

    selected_period = st.selectbox("Dönem seç", periods)

    results = {}

    for name, df in data.items():

        table = extract_period(df, selected_period)

        if table is not None:
            st.subheader(name)
            st.dataframe(table, use_container_width=True)
            results[name] = table

    if results:

        excel_bytes = to_excel_output(results)

        st.download_button(
            label="📥 Excel indir",
            data=excel_bytes,
            file_name=f"financials_{selected_period}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
