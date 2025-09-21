# utils.py
"""
Utility functions for NFA/DFA project.
"""
import pandas as pd
from io import BytesIO

def parse_list(raw: str):
    return [x.strip() for x in raw.split(",") if x.strip()]

def df_to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()
