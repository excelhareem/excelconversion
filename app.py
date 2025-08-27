import streamlit as st
import pandas as pd
import io
from convert_invoice import convert_purchase_to_sale

st.title("📑 Purchase → Sale Invoice Converter")

uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    # Save uploaded file temporarily
    temp_file = "uploaded_file.xlsx"
    with open(temp_file, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Run conversion (output file is sale_invoice.xlsx)
    output_file = "sale_invoice.xlsx"
    convert_purchase_to_sale(temp_file, output_file)

    # Load converted file
    sale_df = pd.read_excel(output_file)

    st.subheader("Converted Sale Invoice")
    st.dataframe(sale_df)

    # Download option
    with open(output_file, "rb") as f:
        st.download_button(
            label="📥 Download Sale Invoice Excel",
            data=f,
            file_name="sale_invoice.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
