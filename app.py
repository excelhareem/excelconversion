import streamlit as st
import pandas as pd
import numpy as np
import math
from math import gcd

st.title("📑 Purchase → Sale Invoice Converter")

uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

# Hide Streamlit default UI elements
hide_footer_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stStatusWidget {display: none;}
    </style>
"""
st.markdown(hide_footer_style, unsafe_allow_html=True)

def _num(x, default=None):
    try:
        return float(str(x).replace(",", ""))
    except:
        return default

def _int_safe(x):
    return int(round(float(x))) if x is not None else 0

def _integer_tax_step(rate_percent_float: float) -> int:
    """
    For rate R%, tax = value * R / 100 is integer iff value is multiple of step = 100 / gcd(100, R_int).
    If R is non-integer we fall back to rounding R to nearest int for step logic.
    """
    r_int = int(round(rate_percent_float))
    if r_int <= 0:
        return 1
    return 100 // gcd(100, r_int)

def _find_integer_tax_value(base_value: float, rate: float, min_pct: float, max_pct: float):
    """
    Find smallest integer value >= ceil(base*(1+min_pct)) within max_pct (ceil(base*(1+max_pct)))
    that yields integer tax with given rate. If not found, snap to next required multiple.
    Returns (new_value_int, factor_float).
    """
    if base_value is None or base_value <= 0:
        return 0, 1.0

    step = _integer_tax_step(rate)  # e.g. 18% -> step 50
    lo = math.ceil(base_value * (1.0 + min_pct))
    hi = math.ceil(base_value * (1.0 + max_pct))

    # Search inside window
    for v in range(lo, hi + 1):
        if v % step == 0:
            return v, (v / base_value)

    # Snap to next multiple (may exceed max_pct slightly)
    snapped = math.ceil(lo / step) * step
    return snapped, (snapped / base_value)

if uploaded_file:
    # Read uploaded Excel file
    df = pd.read_excel(uploaded_file, dtype=str)

    # Columns required in final output
    required_columns = [
        "Invoice Ref No.", "Invoice No.", "Invoice Type", "Invoice Date",
        "Buyer Registration No.", "Buyer Name", "Taxpayer Type",
        "Seller Registration No.", "Seller Name", "Sale Type",
        "Sale Origination Province of Supplier", "Quantity",
        "Product Description", "HS Code", "HSCode Description", "Rate", "UoM",
        "Value of Sales Excluding Sales Tax", "Reason", "Reason Remarks",
        "Sales Tax/ FED in ST Mode", "Extra Tax", "ST Withheld at Source",
        "SRO No. / Schedule No.", "Item Sr. No.", "Further Tax",
        "Fixed / notified value or Retail Price / Toll Charges",
        "Total Value of Sales."
    ]

    # 1. Invoice Ref No.
    df["Invoice Ref No."] = [f"17022025{str(i).zfill(3)}" for i in range(1, len(df) + 1)]
    # 2. Invoice No.
    df["Invoice No."] = [f"zs333{str(i).zfill(3)}" for i in range(1, len(df) + 1)]
    # 3. Invoice Type
    df["Invoice Type"] = "Sale Invoice"
    # 4. Swap Buyer → Seller
    if "Buyer Registration No." in df and "Buyer Name" in df:
        df["Seller Registration No."] = df["Buyer Registration No."]
        df["Seller Name"] = df["Buyer Name"]
    # 5. New Buyer values
    base_buyer = 1122456437000
    df["Buyer Registration No."] = [str(base_buyer + i) for i in range(1, len(df) + 1)]
    df["Buyer Name"] = "Retail Customers"
    # 6. Taxpayer Type
    df["Taxpayer Type"] = "Unregistered"
    # 7. Preserve HS Code
    if "HS Code" in df.columns:
        df["HS Code"] = df["HS Code"].astype(str)

    def adjust_row(row):
        # read inputs
        rate_str = str(row.get("Rate", "")).strip().lower()
        sale_type = str(row.get("Sale Type", "")).strip().lower()
        val_excl = _num(row.get("Value of Sales Excluding Sales Tax", ""), 0.0)
        fixed_col = "Fixed / notified value or Retail Price / Toll Charges"
        fixed_val = _num(row.get(fixed_col, ""), None)

        # parse rate
        has_rate = False
        try:
            rate = float(rate_str.replace("%", ""))
            has_rate = rate > 0
        except:
            rate = 0.0

        # CASE 1: Exempt / 0% (sale type irrelevant)
        if rate_str in ["exempt", "0", "0.0", "0%"] or not has_rate:
            factor = 1.0 + np.random.uniform(0.05, 0.10)  # 5–10%
            new_excl = _int_safe(val_excl * factor)
            # taxes
            sales_tax = 0
            # scale Extra/Further only if p
