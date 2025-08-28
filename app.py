import streamlit as st
import pandas as pd
import numpy as np
import math
from math import gcd

st.set_page_config(page_title="Invoice Converter", layout="wide")
st.title("📑 Purchase → Sale Invoice Converter")

# Hide Streamlit default UI elements
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stStatusWidget {display: none;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

# ---------- Helper Functions ----------
def _num(x, default=None):
    try:
        return float(str(x).replace(",", "").strip())
    except:
        return default

def _int_safe(x):
    return int(round(float(x))) if x is not None else 0

def _integer_tax_step(rate_percent_float: float) -> int:
    r_int = int(round(rate_percent_float))
    if r_int <= 0:
        return 1
    return 100 // gcd(100, r_int)

def _find_integer_tax_value(base_value: float, rate: float, min_pct: float, max_pct: float):
    """Find nearest integer-increased value that keeps tax integer."""
    if base_value is None or base_value <= 0:
        return base_value, 1.0

    step = _integer_tax_step(rate)
    lo = math.ceil(base_value * (1.0 + min_pct))
    hi = math.ceil(base_value * (1.0 + max_pct))

    for v in range(lo, hi + 1):
        if v % step == 0:
            return v, (v / base_value)

    snapped = math.ceil(lo / step) * step
    return snapped, (snapped / base_value)

# ---------- Main Processing ----------
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

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

        # Add Invoice numbers
        df["Invoice Ref No."] = [f"17022025{str(i).zfill(3)}" for i in range(1, len(df) + 1)]
        df["Invoice No."] = [f"zs333{str(i).zfill(3)}" for i in range(1, len(df) + 1)]
        df["Invoice Type"] = "Sale Invoice"

        # Swap Buyer <-> Seller
        df["Seller Registration No."] = df["Buyer Registration No."]
        df["Seller Name"] = df["Buyer Name"]
        base_buyer = 1122456437000
        df["Buyer Registration No."] = [str(base_buyer + i) for i in range(1, len(df) + 1)]
        df["Buyer Name"] = "Retail Customers"
        df["Taxpayer Type"] = "Unregistered"

        # Adjust values
        new_values = []
        new_extra = []
        new_further = []

        for _, row in df.iterrows():
            val = _num(row.get("Value of Sales Excluding Sales Tax"))
            rate = _num(row.get("Rate"))
            sale_type = str(row.get("Sale Type", "")).strip().lower()
            fixed_val = _num(row.get("Fixed / notified value or Retail Price / Toll Charges"))
            extra_tax = _num(row.get("Extra Tax"))
            further_tax = _num(row.get("Further Tax"))

            new_val = val
            ratio = 1.0

            # Case 1: Exempt or 0%
            if str(row.get("Rate")).strip().lower() in ["exempt", "0", "0.0", "0%"]:
                if val:
                    new_val, ratio = _find_integer_tax_value(val, 0, 0.05, 0.10)

            # Case 2: 3rd Schedule
            elif "3rd schedule" in sale_type:
                if val and rate:
                    new_val, ratio = _find_integer_tax_value(val, rate, 0.005, 0.03)

            # Case 3: Fixed Value exists
            elif fixed_val:
                new_val, ratio = _find_integer_tax_value(fixed_val, rate or 1, 0.001, 0.02)

            # Case 4: General taxable
            elif val and rate:
                new_val, ratio = _find_integer_tax_value(val, rate, 0.001, 0.02)

            new_values.append(_int_safe(new_val))

            # Apply same ratio to Extra & Further
            new_extra.append(_int_safe(extra_tax * ratio) if extra_tax else 0)
            new_further.append(_int_safe(further_tax * ratio) if further_tax else 0)

        df["Value of Sales Excluding Sales Tax"] = new_values
        df["Extra Tax"] = new_extra
        df["Further Tax"] = new_further

        # Keep required cols only
        final_df = df[[c for c in required_columns if c in df.columns]]

        st.subheader("Converted Sale Invoice")
        st.dataframe(final_df)

        final_file = "sale_invoice.xlsx"
        final_df.to_excel(final_file, index=False)

        with open(final_file, "rb") as f:
            st.download_button(
                label="📥 Download Sale Invoice Excel",
                data=f,
                file_name=final_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
