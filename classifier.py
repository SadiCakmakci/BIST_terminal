import pandas as pd


def classify_table(df: pd.DataFrame) -> str:
    """
    DataFrame içeriğine bakarak finansal tablo tipini tahmin eder.
    """
    if df is None or df.empty:
        return "unknown"

    text = " ".join(df.astype(str).values.flatten()).lower()

    if any(x in text for x in ["revenue", "sales", "net income", "gross profit"]):
        return "income_statement"

    if any(x in text for x in ["assets", "liabilities", "equity"]):
        return "balance_sheet"

    if any(x in text for x in ["cash flow", "operating cash"]):
        return "cash_flow"

    return "unknown"


def detect_period(columns) -> str:
    """
    Kolonlara bakarak yıllık mı çeyreklik mi anlamaya çalışır.
    """
    cols = " ".join([str(c).lower() for c in columns])

    if any(x in cols for x in ["q1", "q2", "q3", "q4", "ç1", "ç2", "ç3", "ç4"]):
        return "quarterly"

    return "annual"
