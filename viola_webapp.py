import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime
import time

# === PAGE SETTINGS ===
st.set_page_config(page_title="VIOLA Warehouse Extractor (Dropbox)", layout="centered")

st.title("📊 VIOLA Warehouse Column Extractor (Dropbox)")

st.markdown("""
✅ **How it works:**  
1️⃣ Picks a file from your Google Sheet list  
2️⃣ Downloads directly from Dropbox (`?dl=1` guarantees raw binary)  
3️⃣ Shows progress bar during download + processing  
4️⃣ Lets you download the tagged CSV.
""")

# === CONFIG ===
GOOGLE_SHEET_ID = "1-eCtNpDvw7UxAYSkjnVoHxbOzJFTKa-fwokkh2Xta-g"
CSV_EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&t={int(time.time())}"

# === 1) Load file list ===
def load_file_list():
    df = pd.read_csv(CSV_EXPORT_URL)
    return df

try:
    file_list = load_file_list()

    st.write("📄 **Columns loaded:**", file_list.columns.tolist())
    st.write("🔍 **First rows:**", file_list.head())

    selected_file = st.selectbox("📁 **Choose a file:**", file_list['File Name'])
    matches = file_list.loc[file_list['File Name'] == selected_file, 'File Link'].values

    if len(matches) == 0:
        st.error(f"❌ No File Link found for: {selected_file}. Check your Google Sheet.")
        st.stop()

    file_link = matches[0]

    # ✅ Ensure Dropbox link uses ?dl=1
    if file_link.endswith("?dl=0"):
        file_link = file_link.replace("?dl=0", "?dl=1")

except Exception as e:
    st.error(f"⚠️ Failed to load Google Sheet: {str(e)}")
    st.stop()

# === 2) Date input ===
as_of_date = st.date_input("📅 **Select AS_OF_DATE**", value=datetime.today())
formatted_date = as_of_date.strftime('%m/%d/%Y')

# === 3) Process with progress bar ===
if st.button("📥 Download and Process"):
    try:
        # === Initialize progress bar + status ===
        progress = st.progress(0)
        status = st.empty()

        status.info(f"Starting download for **{selected_file}**...")
        progress.progress(10)

        # === 1) Download from Dropbox ===
        response = requests.get(file_link)
        if response.status_code != 200:
            st.error(f"❌ Failed to download file. Status code: {response.status_code}")
            st.stop()

        progress.progress(40)
        status.info("✅ Download complete. Reading file...")

        file_bytes = io.BytesIO(response.content)

        # === 2) Read XLSB ===
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

        progress.progress(60)
        df = pd.read_excel(
            file_bytes,
            sheet_name='Main Data',
            engine='pyxlsb',
            keep_default_na=False
        )

        progress.progress(75)
        status.info("🔄 Processing data...")

        if 'SPV Transfer Date' in df.columns:
            df['SPV Transfer Date'] = pd.to_numeric(df['SPV Transfer Date'], errors='coerce')
            df['SPV Transfer Date'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(df['SPV Transfer Date'], unit='D')
            df['SPV Transfer Date'] = df['SPV Transfer Date'].dt.strftime('%m/%d/%Y')

        df_filtered = df[list(column_map.keys())].rename(columns=column_map)
        df_filtered['AS_OF_DATE'] = formatted_date

        progress.progress(90)
        status.info("📄 Converting to CSV...")

        csv_buffer = io.StringIO()
        df_filtered.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        progress.progress(100)
        status.success("✅ Done! Download ready below.")

        st.download_button(
            label="⬇️ Download VIOLA_WAREHOUSE_1_TAGGING.csv",
            data=csv_buffer.getvalue(),
            file_name="VIOLA_WAREHOUSE_1_TAGGING.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"⚠️ Something went wrong: {str(e)}")
