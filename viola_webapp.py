import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime

st.set_page_config(page_title="VIOLA Warehouse Extractor (Google Drive)", layout="centered")

st.title("📊 VIOLA Warehouse Column Extractor (Google Drive)")

st.markdown("""
✅ **How it works:**  
1. Picks file from your Google Sheet list  
2. Downloads directly from Google Drive (raw export link)  
3. Processes & lets you download the tagged CSV
""")

# === CONFIG ===
GOOGLE_SHEET_ID = "1-eCtNpDvw7UxAYSkjnVoHxbOzJFTKa-fwokkh2Xta-g"  # Use your Google Sheet ID!
CSV_EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"

# === 1) Load file list ===
import time
CSV_EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&t={int(time.time())}"

# Then load without cache
def load_file_list():
    df = pd.read_csv(CSV_EXPORT_URL)
    return df

try:
    file_list = load_file_list()

    # ✅ Debug: show what columns we got
    st.write("📄 **Columns loaded from Google Sheet:**", file_list.columns.tolist())
    st.write("🔍 **First few rows:**", file_list.head())

    selected_file = st.selectbox("📁 Choose a file:", file_list['File Name'])
    file_link = file_list.loc[file_list['File Name'] == selected_file, 'File Link'].values[0]

except Exception as e:
    st.error(f"⚠️ Failed to load Google Sheet: {str(e)}")
    st.stop()

# === 2) Date input ===
as_of_date = st.date_input("Select AS_OF_DATE", value=datetime.today())
formatted_date = as_of_date.strftime('%m/%d/%Y')

# === 3) Process if user clicks ===
if st.button("📥 Download and Process"):
    try:
        st.info(f"Downloading **{selected_file}** from Google Drive...")
        response = requests.get(file_link)
        if response.status_code != 200:
            st.error(f"❌ Failed to download file. Status code: {response.status_code}")
            st.stop()

        file_bytes = io.BytesIO(response.content)

        # === Your column mapping ===
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

        df = pd.read_excel(
            file_bytes,
            sheet_name='Main Data',
            engine='pyxlsb',
            keep_default_na=False
        )

        if 'SPV Transfer Date' in df.columns:
            df['SPV Transfer Date'] = pd.to_numeric(df['SPV Transfer Date'], errors='coerce')
            df['SPV Transfer Date'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(df['SPV Transfer Date'], unit='D')
            df['SPV Transfer Date'] = df['SPV Transfer Date'].dt.strftime('%m/%d/%Y')

        df_filtered = df[list(column_map.keys())].rename(columns=column_map)
        df_filtered['AS_OF_DATE'] = formatted_date

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
        st.error(f"⚠️ Something went wrong: {str(e)}")
