import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="VIOLA Warehouse Extractor", layout="centered")

st.title("📊 VIOLA Warehouse Column Extractor")
st.markdown("Upload a `.xlsb` file and select an AS_OF_DATE to extract and convert specified columns into a CSV.")

# Upload XLSB file
uploaded_file = st.file_uploader("Upload Borrowing Base Certified Report (.xlsb)", type="xlsb")

# Column mapping: Original -> Target
column_map = {
    'Verified Y/N': 'VERIFICATION_FLAG',
    'Scratch True False': 'SCRATCH_FLAG',
    'Cohort - Final': 'COHORT',
    'Final Creditor Name': 'FINAL_CREDITOR_NAME',
    'Manual Pay Flag': 'MANUAL_PAY_FLAG',
    'Exclusion Reason': 'EXCLUSION_REASON',
    'RECEIVABLE_ID': 'RECEIVABLE_ID',
    'SPV Transfer Date': 'SPV_TRANSFER_DATE'
}

# Date input
as_of_date = st.date_input("Select AS_OF_DATE", value=datetime.today())
formatted_date = as_of_date.strftime('%m/%d/%Y')

if uploaded_file:
    try:
        sheet_name = 'Main Data'

        # Read XLSB file without interpreting "n/a" as NaN
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine='pyxlsb', keep_default_na=False)

        # Fix SPV Transfer Date if present and numeric
        if 'SPV Transfer Date' in df.columns:
            # Convert Excel serial to datetime
            df['SPV Transfer Date'] = pd.to_datetime(
                '1899-12-30'
            ) + pd.to_timedelta(df['SPV Transfer Date'].astype(float), unit='D')

            # Format to MM/DD/YYYY string
            df['SPV Transfer Date'] = df['SPV Transfer Date'].dt.strftime('%m/%d/%Y')

        # Filter and rename columns
        df_filtered = df[list(column_map.keys())].rename(columns=column_map)

        # Add user-selected AS_OF_DATE
        df_filtered['AS_OF_DATE'] = formatted_date

        # Convert to CSV in memory
        csv_buffer = io.StringIO()
        df_filtered.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        st.success("✅ File processed successfully!")

        st.download_button(
            label="⬇️ Download VIOLA_WAREHOUSE_1_TAGGING.csv",
            data=csv_buffer.getvalue(),
            file_name="VIOLA_WAREHOUSE_1_TAGGING.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"⚠️ Something went wrong:\n\n{str(e)}")
else:
    st.info("👈 Please upload a `.xlsb` file to begin.")
