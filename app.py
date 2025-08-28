import streamlit as st
import pandas as pd
import numpy as np

st.title("📑 Purchase → Sale Invoice Converter")

uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

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
import streamlit as st

hide_footer_style = """
    <style>
    #MainMenu {visibility: hidden;}     /* Hide hamburger menu */
    footer {visibility: hidden;}        /* Hide footer ("Hosted with Streamlit") */
    header {visibility: hidden;}        /* Hide Streamlit header */
    .stStatusWidget {display: none;}    /* Hide bottom-right running status */
    </style>
"""

st.markdown(hide_footer_style, unsafe_allow_html=True)

    # 1. Invoice Ref No. → month-like code + unique digits
    df["Invoice Ref No."] = [
        f"17022025{str(i).zfill(3)}" for i in range(1, len(df) + 1)
    ]

    # 2. Invoice No. → zs333XXX format
    df["Invoice No."] = [
        f"zs333{str(i).zfill(3)}" for i in range(1, len(df) + 1)
    ]

    # 3. Invoice Type → always "Sale Invoice"
    df["Invoice Type"] = "Sale Invoice"

    # 4. Swap Buyer → Seller
    df["Seller Registration No."] = df["Buyer Registration No."]
    df["Seller Name"] = df["Buyer Name"]

    # 5. New Buyer values (fixed + random last 3 digits)
    base_buyer = 1122456437000
    df["Buyer Registration No."] = [
        str(base_buyer + i) for i in range(1, len(df) + 1)
    ]
    df["Buyer Name"] = "Retail Customers"

    # 6. Taxpayer Type → Unregistered
    df["Taxpayer Type"] = "Unregistered"

    # 7. Preserve HS Code exactly (no formatting loss)
    if "HS Code" in df.columns:
        df["HS Code"] = df["HS Code"].astype(str)

    # 8. Adjust Value of Sales Excluding Sales Tax (Exempt + 0% both covered)
    def adjust_value(row):
        rate_val = str(row["Rate"]).strip().lower()
        try:
            original_val = float(str(row["Value of Sales Excluding Sales Tax"]).replace(",", ""))
        except:
            return row["Value of Sales Excluding Sales Tax"]

        if rate_val in ["exempt", "0", "0.0", "0%"]:
            factor = 1 + np.random.uniform(0.05, 0.10)  # random 5–10%
            return int(round(original_val * factor, 0))
        else:
            return int(round(original_val, 0))

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
