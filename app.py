import streamlit as st
import pandas as pd
import numpy as np
import math

st.title("📑 Purchase → Sale Invoice Converter")

uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

# Hide Streamlit branding / footer / menu
hide_footer_style = """
    <style>
    #MainMenu {visibility: hidden;}     
    footer {visibility: hidden;}        
    header {visibility: hidden;}        
    .stStatusWidget {display: none;}    
    </style>
"""
st.markdown(hide_footer_style, unsafe_allow_html=True)

if uploaded_file:
    # Read uploaded Excel
    df = pd.read_excel(uploaded_file, dtype=str)

    # Required columns in final output
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
        "Total Value of Sales.", "Type"
    ]

    # 1. Invoice Ref No.
    df["Invoice Ref No."] = [f"17022025{str(i).zfill(3)}" for i in range(1, len(df) + 1)]

    # 2. Invoice No.
    df["Invoice No."] = [f"zs333{str(i).zfill(3)}" for i in range(1, len(df) + 1)]

    # 3. Invoice Type
    df["Invoice Type"] = "Sale Invoice"

    # 4. Swap Buyer → Seller
    df["Seller Registration No."] = df["Buyer Registration No."]
    df["Seller Name"] = df["Buyer Name"]

    # 5. New Buyer
    base_buyer = 1122456437000
    df["Buyer Registration No."] = [str(base_buyer + i) for i in range(1, len(df) + 1)]
    df["Buyer Name"] = "Retail Customers"

    # 6. Taxpayer Type
    df["Taxpayer Type"] = "Unregistered"

    # 7. Preserve HS Code
    if "HS Code" in df.columns:
        df["HS Code"] = df["HS Code"].astype(str)

    # 8. Adjust Value of Sales Excluding Sales Tax
    def adjust_value(row):
        try:
            fixed = float(str(row["Value of Sales Excluding Sales Tax"]).replace(",", ""))
        except:
            return row["Value of Sales Excluding Sales Tax"]

        rate_str = str(row["Rate"]).strip().lower()

        # Case A: Exempt / 0%
        if rate_str in ["exempt", "0", "0.0", "0%"]:
            factor = 1 + np.random.uniform(0.05, 0.10)
            return int(round(fixed * factor, 0))

        # Try to parse tax rate
        try:
            rate = float(rate_str.replace("%", ""))
        except:
            return int(round(fixed, 0))

        # Case B: Taxable items (Normal + 3rd Schedule both)
        found_value = None
        for inc_percent in [x / 1000 for x in range(1, 21)]:  # 0.1% → 2.0%
            new_val = math.ceil(fixed * (1 + inc_percent))
            tax = new_val * rate / 100
            if tax.is_integer():
                found_value = new_val
                break

        # If still not found → force with +2%
        if not found_value:
            found_value = math.ceil(fixed * 1.02)

        return found_value

    if "Value of Sales Excluding Sales Tax" in df.columns:
        df["Value of Sales Excluding Sales Tax"] = df.apply(adjust_value, axis=1)

    # 9. Keep only required columns
    final_df = df[[col for col in required_columns if col in df.columns]]

    # Show preview
    st.subheader("Converted Sale Invoice")
    st.dataframe(final_df)

    # Download option
    final_file = "sale_invoice.xlsx"
    final_df.to_excel(final_file, index=False)

    with open(final_file, "rb") as f:
        st.download_button(
            label="📥 Download Sale Invoice Excel",
            data=f,
            file_name=final_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
