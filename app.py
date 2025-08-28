import streamlit as st
import pandas as pd
import numpy as np
import math

st.title("📑 Purchase → Sale Invoice Converter")

uploaded_file = st.file_uploader("Upload Purchase Invoice (Excel)", type=["xlsx", "xls"])

# Hide Streamlit default UI elements
hide_footer_style = """
    <style>
    #MainMenu {visibility: hidden;}     /* Hide hamburger menu */
    footer {visibility: hidden;}        /* Hide footer ("Hosted with Streamlit") */
    header {visibility: hidden;}        /* Hide Streamlit header */
    .stStatusWidget {display: none;}    /* Hide bottom-right running status */
    </style>
"""
st.markdown(hide_footer_style, unsafe_allow_html=True)

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
    df["Invoice Ref No."] = [
        f"17022025{str(i).zfill(3)}" for i in range(1, len(df) + 1)
    ]

    # 2. Invoice No.
    df["Invoice No."] = [
        f"zs333{str(i).zfill(3)}" for i in range(1, len(df) + 1)
    ]

    # 3. Invoice Type
    df["Invoice Type"] = "Sale Invoice"

    # 4. Swap Buyer → Seller
    df["Seller Registration No."] = df["Buyer Registration No."]
    df["Seller Name"] = df["Buyer Name"]

    # 5. New Buyer values
    base_buyer = 1122456437000
    df["Buyer Registration No."] = [
        str(base_buyer + i) for i in range(1, len(df) + 1)
    ]
    df["Buyer Name"] = "Retail Customers"

    # 6. Taxpayer Type
    df["Taxpayer Type"] = "Unregistered"

    # 7. Preserve HS Code
    if "HS Code" in df.columns:
        df["HS Code"] = df["HS Code"].astype(str)

    # ---------- MAIN ADJUSTMENT FUNCTION ----------
    def adjust_row(row):
        rate_val = str(row.get("Rate", "")).strip().lower()
        sale_type = str(row.get("Sale Type", "")).strip()
        fixed_val = row.get("Fixed / notified value or Retail Price / Toll Charges", None)

        try:
            val_excl = float(str(row["Value of Sales Excluding Sales Tax"]).replace(",", ""))
        except:
            val_excl = 0

        # Original values backup
        original_val = val_excl
        tax_rate = 0
        try:
            tax_rate = float(rate_val) if rate_val.replace(".", "").isdigit() else 0
        except:
            pass

        new_val = original_val
        factor = 1.0

        # CASE 1: Exempt / 0%
        if rate_val in ["exempt", "0", "0.0", "0%"]:
            factor = 1 + np.random.uniform(0.05, 0.10)  # 5–10%
            new_val = round(original_val * factor)

        # CASE 2: 3rd Schedule Goods
        elif "3rd schedule goods" in sale_type.lower():
            found_val = None
            for inc_percent in [x / 1000 for x in range(5, 21)]:  # 0.5% – 2%
                candidate = math.ceil(original_val * (1 + inc_percent))
                tax = candidate * tax_rate / 100
                if tax.is_integer():
                    found_val = candidate
                    factor = (candidate / original_val) if original_val else 1
                    break
            if not found_val:
                candidate = math.ceil(original_val * 1.02)  # force 2%
                found_val = candidate
                factor = (candidate / original_val) if original_val else 1
            new_val = found_val

        # CASE 3: Other rows
        else:
            base_val = None
            try:
                base_val = float(str(fixed_val).replace(",", ""))
            except:
                base_val = None

            if base_val:  # Fixed value present
                factor = 1 + np.random.uniform(0.001, 0.02)  # 0.1% – 2%
                new_val = round(base_val * factor)
                row["Fixed / notified value or Retail Price / Toll Charges"] = new_val
            else:  # Apply on Value Excl
                factor = 1 + np.random.uniform(0.001, 0.02)
                new_val = round(original_val * factor)

        # Apply updates
        row["Value of Sales Excluding Sales Tax"] = int(new_val)

        # Sales Tax / FED
        sales_tax = int(round(new_val * tax_rate / 100)) if tax_rate > 0 else 0
        row["Sales Tax/ FED in ST Mode"] = sales_tax

        # Total Value
        row["Total Value of Sales."] = int(new_val + sales_tax)

        # Apply same factor on Extra Tax & Further Tax if present
        for col in ["Extra Tax", "Further Tax"]:
            if col in row and str(row[col]).strip() not in ["", "nan", "None"]:
                try:
                    old_val = float(str(row[col]).replace(",", ""))
                    row[col] = int(round(old_val * factor))
                except:
                    pass

        return row

    df = df.apply(adjust_row, axis=1)

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
