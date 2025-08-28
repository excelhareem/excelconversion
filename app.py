def adjust_value(row):
    rate_val = str(row["Rate"]).strip().lower()

    try:
        original_val = float(str(row["Value of Sales Excluding Sales Tax"]).replace(",", ""))
    except:
        return row["Value of Sales Excluding Sales Tax"]

    # (1) Exempt / 0% wali cheezen
    if rate_val in ["exempt", "0", "0.0", "0%"]:
        factor = 1 + np.random.uniform(0.05, 0.10)  # random 5–10%
        return int(round(original_val * factor, 0))

    # (2) 3rd Schedule Goods (sirf agar exempt/0 nahi hai)
    sale_type_val = str(row.get("Sale Type", "")).lower()
    if "3rd schedule goods" in sale_type_val:
        found_val = None
        for inc_percent in [x / 1000 for x in range(5, 21)]:  # 0.5% to 2%
            new_val = math.ceil(original_val * (1 + inc_percent))
            try:
                tax = new_val * float(rate_val) / 100
            except:
                continue
            if tax.is_integer():
                found_val = new_val
                break
        if not found_val:
            found_val = math.ceil(original_val * 1.02)
        return found_val

    # (3) Normal taxable goods
    # check "Fixed / notified value..." column
    fixed_val_col = "Fixed / notified value or Retail Price / Toll Charges"
    fixed_val = None
    if fixed_val_col in row and str(row[fixed_val_col]).strip() not in ["", "nan", "None"]:
        try:
            fixed_val = float(str(row[fixed_val_col]).replace(",", ""))
        except:
            fixed_val = None

    base_val = fixed_val if fixed_val else original_val
    found_val = None
    for inc_percent in [x / 1000 for x in range(1, 21)]:  # 0.1% to 2%
        new_val = math.ceil(base_val * (1 + inc_percent))
        try:
            tax = new_val * float(rate_val) / 100
        except:
            continue
        if tax.is_integer():
            found_val = new_val
            break
    if not found_val:
        found_val = math.ceil(base_val * 1.02)

    return found_val
