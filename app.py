import streamlit as st
import pandas as pd
import random

st.title("📑 Purchase → Sale Invoice Converter")

# 🔹 Conversion function (directly inside app.py, no external files needed)
def convert_purchase_to_sale(input_file, output_file):
    # Load the Excel file
    df = pd.read_excel(input_file)

    # ✅ Map Seller → Buyer
    if "Seller Registration No." in df.columns:
        df["Buyer Registration No."] = df["Seller Registration No."]
    if "Seller Name" in df.columns:
        df["Buyer Name"] = df["Seller Name"]

    # ✅ Force Buyer Name & Buyer Registration format
    df["Buyer Name"] = "Retail Customer"
    df["Buyer Registration No."] = [
        f"11223387347{str(i).zfill(2)}" for i in range(1, len(df) + 1)
    ]

    # ✅ Force Taxpayer Type to Unregistered
    df["Taxpayer Type"] = "Unregistered"

    # Save as new Excel file
    df.to_excel(output_file, index=False)

# 🔹 Streamlit UI
uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    temp_file = "uploaded_file.xlsx"
    with open(temp_file, "wb") as f:
        f.write(uploaded_file.getbuffer())

    output_file = "sale_invoice.xlsx"
    convert_purchase_to_sale(temp_file, output_file)

    sale_df = pd.read_excel(output_file)

    st.subheader("✅ Converted Sale Invoice")
    st.dataframe(sale_df)

    with open(output_file, "rb") as f:
        st.download_button(
            label="📥 Download Sale Invoice Excel",
            data=f,
            file_name="sale_invoice.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
