import streamlit as st
import pandas as pd
import numpy as np
import io

st.title("📑 Purchase → Sale Invoice Converter")

uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    # Read Excel with HS Code as string to preserve formatting
    df = pd.read_excel(uploaded_file, dtype={"HS Code": str})

    # Columns required in final output
    required_columns = [
        "Invoice Ref No.", "Invoice No.", "Invoice Type", "Invoice Date",
        "Buyer Registration No.", "Buyer Name", "Taxpayer Type",
        "Seller Registration No.", "Seller Name", "Sale Type",
        "Sale Origination Province of Supplier", "Quantity",
        "Product Description", "HS Code", "HSCode Description",
        "Rate", "UoM", "Value of Sales Excluding Sales Tax",
        "Reason", "Reason Remarks", "Sales Tax/ FED in ST Mode",
        "Extra Tax", "ST Withheld at Source", "SRO No. / Schedule No.",
        "Item Sr. No.", "Further Tax",
        "Fixed / notified value or Retail Price / Toll Charges",
        "Total Value of Sales."
    ]

    # Keep only required columns, add missing as blank
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""

    df = df[required_columns]

    # Buyer → Seller swap
    if "Buyer Registration No." in df.columns:
        df["Seller Registration No."] = df["Buyer Registration No."].astype(str)
    if "Buyer Name" in df.columns:
        df["Seller Name"] = df["Buyer Name"]

    # Buyer details → fixed
    df["Buyer Registration No."] = [
        "1122456437" + str(100 + i) for i in range(len(df))
    ]
    df["Buyer Name"] = "Retail Customers"

    # Seller details → fixed
    df["Seller Registration No."] = [
        "1212341232" + str(100 + i) for i in range(len(df))
    ]
    df["Seller Name"] = "Retail Customers"

    # Invoice Type → Sale Invoice
    df["Invoice Type"] = "Sale Invoice"

    # Taxpayer Type → Unregistered
    df["Taxpayer Type"] = "Unregistered"

    # Invoice Ref No. → like 17022025xxx
    base_ref = 17022025
    df["Invoice Ref No."] = [str(base_ref) + str(100 + i) for i in range(len(df))]

    # Invoice No. → zs333xxx
    df["Invoice No."] = ["zs333" + str(100 + i) for i in range(len(df))]

    # HS Code preserve as string
    if "HS Code" in df.columns:
        df["HS Code"] = df["HS Code"].fillna("").astype(str)

    # Apply 5–10% random increase if Rate is Exempt or 0
    def adjust_value(row):
        rate_val = str(row["Rate"]).strip().lower()
        original_val = row["Value of Sales Excluding Sales Tax"]

        if pd.notna(original_val) and str(original_val).replace(".", "", 1).isdigit():
            if rate_val in ["exempt", "0", "0.0"]:
                factor = 1 + np.random.uniform(0.05, 0.10)  # random 5–10%
                return int(round(float(original_val) * factor, 0))
            else:
                return original_val
        return original_val

    df["Value of Sales Excluding Sales Tax"] = df.apply(adjust_value, axis=1)

    # Show preview
    st.subheader("Converted Sale Invoice")
    st.dataframe(df)

    # Download option
    output = io.BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        label="📥 Download Sale Invoice Excel",
        data=output.getvalue(),
        file_name="sale_invoice.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
