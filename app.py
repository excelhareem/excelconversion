import streamlit as st
import pandas as pd

st.title("📑 Purchase → Sale Invoice Converter")

def convert_purchase_to_sale(input_file, output_file):
    # Load Excel
    df = pd.read_excel(input_file)
    n = len(df)

    # 🔹 Seller columns (old Buyer values copy)
    if "Buyer Registration No." in df.columns:
        df["Seller Registration No."] = df["Buyer Registration No."]
    else:
        df["Seller Registration No."] = ""

    if "Buyer Name" in df.columns:
        df["Seller Name"] = df["Buyer Name"]
    else:
        df["Seller Name"] = ""

    # 🔹 Buyer columns (new fixed values)
    df["Buyer Registration No."] = [
        f"1122456437{str(i).zfill(3)}" for i in range(1, n + 1)
    ]
    df["Buyer Name"] = "Retail Customer"

    # 🔹 Invoice Type fixed
    df["Invoice Type"] = "Sale Invoice"

    # 🔹 Invoice Ref No. (date + 3 running digits)
    df["Invoice Ref No."] = [f"17022025{str(i).zfill(3)}" for i in range(1, n + 1)]

    # 🔹 Invoice No. (ZS333 + running digits)
    df["Invoice No."] = [f"ZS333{str(i).zfill(3)}" for i in range(1, n + 1)]

    # 🔹 Define required output columns
    required_columns = [
        "Invoice Ref No.", "Invoice No.", "Invoice Type", "Invoice Date",
        "Buyer Registration No.", "Buyer Name", "Taxpayer Type",
        "Seller Registration No.", "Seller Name", "Sale Type",
        "Sale Origination Province of Supplier", "Quantity", "Product Description",
        "HS Code", "HSCode Description", "Rate", "UoM",
        "Value of Sales Excluding Sales Tax", "Reason", "Reason Remarks",
        "Sales Tax/ FED in ST Mode", "Extra Tax", "ST Withheld at Source",
        "SRO No. / Schedule No.", "Item Sr. No.", "Further Tax",
        "Fixed / notified value or Retail Price / Toll Charges",
        "Total Value of Sales."
    ]

    # 🔹 Make sure all required columns exist
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""

    # 🔹 Reorder & drop unwanted
    df = df[required_columns]

    # Save result
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
