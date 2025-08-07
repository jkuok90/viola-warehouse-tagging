import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import io
from datetime import datetime
import time

# === PAGE SETTINGS ===
st.set_page_config(page_title="VIOLA Warehouse Extractor (Google Sheets + Dropbox)", layout="centered")
st.title("📊 VIOLA Warehouse Column Extractor (Google Sheets + Dropbox)")

st.markdown("""
✅ **How it works:**  
1️⃣ Picks a file from your Google Sheet list  
2️⃣ Downloads directly from Dropbox (`?dl=1` guarantees raw binary)  
3️⃣ Shows progress bar during download + processing  
4️⃣ Lets you download the tagged CSV.
""")

# === GOOGLE SHEETS SETUP ===
SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "driven-density-445501-s7",
  "private_key_id": "8caae213e1bc0521a7af9ceecbeb02a13bb2450a",
  "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCxDIk2YpTpcvJs
zVJ4xZtGIyd3gyOAyt2WWqJCGOfCnJLj5swkwwyoK0vYdXjP8OSiPPI7r4G4sP6a
SW5WKb9ZPbSVUjq3n6NuN1/WhOKsz7J00f/wWozewi57dbJa+WUyui4gkWy3Im1i
RO3QeW10P2v8k4VgQ5eKo4iUMAu43ZBv6zu5Szt1y6X7bPd/eduR3NlROM12V6tS
qYPnmVRoxexYbBkYMnwl0WqZfFa41oMONnBwsA/hX9m2ZVVYFFeON2mCiQWE/bQl
bEYkd/xF8/4I9eQ555jbBGYPaFYRO+2ikQzPrwcRuewnMmQxZA0UavSiLp6XMLqn
FWwCNTVtAgMBAAECggEALfTukv7g334WXlanjzDf/sM2Ref06cP+473P+29CjXoe
COlKWUqF+QsQC3Zmrzc86b3/NK34cqwC0qK38MayZCRHwTDQjAR0pDHcfy8MNcZN
8NPn5whiI5ps/WAONV4iPhokyhBlk13s3cK9pk02s6OY0L2sM9InvnV3iNu11zzA
Ybqiop0XpjkANOFFvVJqxCxfhIjPHZG9WnnTagK5zIiOWgXG670bmip9dU5rABYc
oaQKdTyL28NxjnHrP9X+pVoulS/wEGEXourkKy0x8gGtlldrZnT/SaFyn89xQTs7
CwPjOhZ0FSxXMNSFbDFRgkrYRse6yVKbrk7lmzf3MwKBgQD0dABlQ4D7hDDfoEwg
+frUrndhvjXynE2BIiYVGP6SL6SFNQrVXxYNjA8Pk8pvHB3V+ZYeYxqhSyc5QPTC
+n3Nbxoayz37p0NgB2TqfxMIoEI0Wqj94jg4I2RElqf6m30gsK6p0+3+AF7tNNHf
/vLnta5EmJeZN78BJjTz9yrPCwKBgQC5aXazrdAN+j9uPYzsTY7bVB+nT1j371+T
FTR3fCxo661jGLGG/3DCbrf8NCyul8LcWiIi2zkur4Nvsf7vvwBzwQhvnUI3XGW/
WKSOCRIyij5wROCEC/BztO2ijCuw1ApTWR560iJh7ZndF6ByXmNOQ1nJc+amXrVc
VqoKDQS4ZwKBgGq90IJnRIYPRewQKc3oeh+ugxCaJyJmH+24RJrHzDl3Nka4T5+2
IoIN23G43hdAVsLddjCUo8c0cs8sTvRovtAaqHJ0tv8RHXlsISPIEz6cA+yqfcpG
orfYtGrCwlzK0ouYutwLX4ufC9RWUSKXR+fnzE3Ft8S+s9fDoDG7huTbAoGAY72X
LGtJK+u96ZjU0V2bhuNHL+Lgcmfj2ySiF9DFtx9pI5DqFzwctYuID/UlQDrFiXI3
QNb7eODT7OcsxF3UaXCjEB/huhRLa9bMltfMYUG6+vwiZwZhMG1ZFIMhEbvPXizn
15xpAJMnnScTmdKqyzQx/cwKfN8f4u+AA24jZusCgYBMv0/hMZEfSfioXGk4s77Y
PsSXGL3yfr8mhqrPkelh8/iJFF5m+z/TPOGQQrwXe9oXqAOrEp1i6DxJQshm7rBI
KMKuO/2QPLpS9AYDHVMM7+EMKmrYp57jIJwbjPedPoTDSBKrYumwqHnzg1eACJhh
/rz2dTeItqF4fPPcYuX8ew==
-----END PRIVATE KEY-----"""
  "client_email": "service-account-101@driven-density-445501-s7.iam.gserviceaccount.com",
  "client_id": "108315625001173526202",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-account-101%40driven-density-445501-s7.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_INFO, scope)
gc = gspread.authorize(credentials)

# === CONFIG ===
SPREADSHEET_NAME = "VIOLA File List"
WORKSHEET_NAME = "Sheet1"

# === 1) Load file list ===
@st.cache_data
def load_file_list():
    worksheet = gc.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

try:
    file_list = load_file_list()
    st.write("📄 **Columns loaded:**", file_list.columns.tolist())
    st.write("🔍 **First rows:**", file_list.head())

    selected_file = st.selectbox("📁 **Choose a file:**", file_list['File Name'])
    file_link = file_list.loc[file_list['File Name'] == selected_file, 'File Link'].values[0]

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
        progress = st.progress(0)
        status = st.empty()
        status.info(f"Starting download for **{selected_file}**...")
        progress.progress(10)

        response = requests.get(file_link)
        if response.status_code != 200:
            st.error(f"❌ Failed to download file. Status code: {response.status_code}")
            st.stop()

        progress.progress(40)
        status.info("✅ Download complete. Reading file...")

        file_bytes = io.BytesIO(response.content)

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
        df = pd.read_excel(file_bytes, sheet_name='Main Data', engine='pyxlsb', keep_default_na=False)

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
