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
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

# ---------- Helper Functions ----------
def _num(x, default=None):
    try:
        return float(str(x).replace(",", ""))
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
    if base_value is None or base_value <= 0:
        return 0, 1.0

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
        df = pd.read_excel(uploaded_file)   # don't force dtype=str

        # required columns list
        required_columns = [
            "Invoice Ref No.", "Invoice No.", "Invoice Type", "Invoice Date",
            "Buyer Registration No.", "Buyer Name", "Taxpayer Type",
            "Seller Registration No.", "Seller Name", "Sale Type",
            "Sale Origination Province of Supplier", "Quantity",
            "Product Description", "HS Code", "HSCode Description", "Rate", "UoM",
            "Value of Sales Exc
