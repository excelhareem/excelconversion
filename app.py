import streamlit as st
import pandas as pd
import math
from math import gcd

# ---------------- UI ----------------
st.set_page_config(page_title="Invoice Converter", layout="wide")
st.title("📑 Purchase → Sale Invoice Converter")

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

# -------------- Helpers --------------
def _num(x, default=0.0):
    """Safe numeric parser: strips commas, %, spaces. NaN/None -> default."""
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return default
        s = str(x).strip().replace(",", "")
        if s.endswith("%"):
            s = s[:-1].strip()
        return float(s) if s != "" else default
    except:
        return default

def _int_safe(x):
    """Round to nearest int; None/NaN -> 0."""
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return 0
        return int(round(float(x)))
    except:
        return 0

def _integer_tax_step(rate_percent_float: float) -> int:
    """
    Smallest integer 'step' so that (value * rate/100) is an integer.
    For rate r, step is 100 / gcd(100, r).
    """
    r_int = int(round(rate_percent_float))
    if r_int <= 0:
        return 1
    return 100 // gcd(100, r_int)

def _find_integer_tax_value(base_value: float, rate: float, min_pct: float, max_pct: float):
    """
    Increase base_value by a percentage within [min_pct, max_pct] so that:
    - adjusted value is an integer
    - and if rate>0, adjusted_value * rate / 100 is also an integer
    Returns (adjusted_value, ratio)
    """
    if base_value is None or base_value <= 0:
        return 0, 1.0

    step = _integer_tax_step(rate)
    lo = math.ceil(base_value * (1.0 + min_pct))
    hi = math.ceil(base_value * (1.0 + max_pct))

    for v in range(lo, hi + 1):
        if v % step == 0:
            return v, (v / base_value)

    # If nothing found in window, snap to next multiple of 'step'
    snapped = math.ceil(lo / step) * step
    return snapped, (snapped / base_value)

# -------------- Main --------------
if uploaded_file:
    try:
        # Read everything as string to preserve formatting (esp. HS Code)
        df = pd.read_excel(uploaded_file, dtype=str)

        # Normalize column names (trim & collapse spaces)
        df.columns = df.columns.str.strip().str.replace(r"\s+", " ", regex=True)

        # Required columns list (we'll keep only those that exist)
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

        # --- Generate/transform static invoice details ---
        n = len(df)
        df["Invoice Ref No."] = [f"17022025{str(i).zfill(3)}" for i in range(1, n + 1)]
        df["Invoice No."] = [f"zs333{str(i).zfill(3)}" for i in range(1, n + 1)]
        df["Invoice Type"] = "Sale Invoice"

        # Swap Buyer -> Seller, then replace Buyer with retail details
        if "Buyer Registration No." in df.columns:
            df["Seller Registration No."] = df["Buyer Registration No."]
        if "Buyer Name" in df.columns:
            df["Seller Name"] = df["Buyer Name"]

        base_buyer = 1122456437000
        df["Buyer Registration No."] = [str(base_buyer + i) for i in range(1, n + 1)]
        df["Buyer Name"] = "Retail Customers"
        df["Taxpayer Type"] = "Unregistered"

        # --- Preserve HS Code & Description EXACTLY as in file (already strings) ---
        # Do not coerce to numbers anywhere.

        # --- Adjust values row-by-row ---
        new_values = []
        new_extra = []
        new_further = []

        for _, row in df.iterrows():
            val = _num(row.get("Value of Sales Excluding Sales Tax"))  # base: value excl
            rate = _num(row.get("Rate"))                               # e.g., "18" or "18%"
            sale_type_raw = str(row.get("Sale Type", "")).strip()
            sale_type = sale_type_raw.lower()
            fixed_val = _num(row.get("Fixed / notified value or Retail Price / Toll Charges"))
            extra_tax = _num(row.get("Extra Tax"))
            further_tax = _num(row.get("Further Tax"))

            new_val = val
            ratio = 1.0

            # 1) Exempt/0% (no tax) -> 5% to 10% increase on Value Excl
            rate_str = str(row.get("Rate", "")).strip().lower()
            if rate_str in ["exempt", "0", "0.0", "0%"]:
                if val > 0:
                    new_val, ratio = _find_integer_tax_value(val, 0, 0.05, 0.10)

            # 2) Sale Type == "3rd Schedule Goods" (case/space-insensitive)
            elif sale_type.replace("  ", " ") == "3rd schedule goods":
                if val > 0 and rate > 0:
                    new_val, ratio = _find_integer_tax_value(val, rate, 0.005, 0.03)

            # 3) If Fixed/notified value exists -> apply on fixed (0.1% to 3.0%)
            elif fixed_val > 0:
                new_val, ratio = _find_integer_tax_value(fixed_val, rate if rate > 0 else 1, 0.001, 0.03)

            # 4) General taxable (0.1% to 3.0%)
            elif val > 0 and rate > 0:
                new_val, ratio = _find_integer_tax_value(val, rate, 0.001, 0.03)

            # Save adjusted integer values
            new_values.append(_int_safe(new_val))

            # Scale Extra/Further taxes (if present) by the same ratio; ensure integers
            new_extra.append(_int_safe(extra_tax * ratio) if extra_tax else 0)
            new_further.append(_int_safe(further_tax * ratio) if further_tax else 0)

        df["Value of Sales Excluding Sales Tax"] = new_values
        df["Extra Tax"] = new_extra
        df["Further Tax"] = new_further

        # --- Output table ---
        final_cols = [c for c in required_columns if c in df.columns]
        if not final_cols:
            st.warning("No expected columns found after upload. Showing full dataframe instead.")
            final_df = df
        else:
            final_df = df[final_cols]

        st.subheader("✅ Converted Sale Invoice")
        st.dataframe(final_df, use_container_width=True)

        # --- Download Excel ---
        out_path = "sale_invoice.xlsx"
        final_df.to_excel(out_path, index=False)
        with open(out_path, "rb") as f:
            st.download_button(
                label="📥 Download Sale Invoice Excel",
                data=f,
                file_name=out_path,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
