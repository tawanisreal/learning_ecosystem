import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# URL ของ Web App จาก Google Apps Script
API_URL = "https://script.google.com/macros/s/AKfycbzCrQzdQp7WMEZ1OTPOSf2mbJJjz25vKF7pwv4BebL3I2Fzcu7N2bqvXz77wY2m7PHv/exec"

st.set_page_config(page_title="ICT Assignment Pro", layout="wide", page_icon="🎓")

# --- Custom CSS (Font Sarabun & UI) ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
    }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

def get_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            raw_json = response.json()
            if not raw_json: return pd.DataFrame()
            df = pd.DataFrame(raw_json)
            # จัดการ Format วันที่ให้เป็น dd/mm/yy (ตัด Timezone ออก)
            if 'Deadline' in df.columns:
                df['Deadline'] = pd.to_datetime(df['Deadline'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%y')
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def send_action(payload):
    try:
        requests.post(API_URL, json=payload)
    except Exception as e:
        st.error(f"Error: {e}")

# --- UI START ---
st.title("🎓 ICT Assignment Tracker")

data = get_data()

if not data.empty:
    waiting_count = len(data[data['Status'] == 'waiting'])
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.metric("งานที่ค้างอยู่ (Waiting)", f"{waiting_count} รายการ")

    with col_m2:
        # ฟิลเตอร์สถานะ
        filter_status = st.radio(
            "มุมมองข้อมูล:", 
            options=["Waiting Only", "Completed Only", "All Tasks"], 
            horizontal=True
        )

    # กรองข้อมูล
    display_df = data.copy()
    if filter_status == "Waiting Only":
        display_df = display_df[display_df['Status'] == 'waiting']
    elif filter_status == "Completed Only":
        display_df = display_df[display_df['Status'] == 'complete']

    st.subheader("📋 รายการงานปัจจุบัน")
    
    # ฟังก์ชันกำหนดสี (เขียว/เหลือง)
    def style_status(val):
        if val == 'complete':
            return 'background-color: #d4edda; color: #155724;' # เขียว
        elif val == 'waiting':
            return 'background-color: #fff3cd; color: #856404;' # เหลือง
        return ''

    # แก้ไข AttributeError โดยใช้ .map() แทน .applymap()
    styled_df = display_df.style.map(style_status, subset=['Status'])

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Deadline": st.column_config.TextColumn("วันกำหนดส่ง (dd/mm/yy)")
        }
    )
else:
    st.info("ยังไม่มีข้อมูลในระบบ")

st.divider()

# --- CRUD TABS ---
tab_add, tab_edit, tab_del = st.tabs(["➕ เพิ่มงาน", "📝 แก้ไขสถานะ", "🗑️ ลบรายการ"])

with tab_add:
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            t = st.text_input("ชื่องาน")
            s = st.text_input("วิชา")
        with c2:
            d = st.date_input("กำหนดส่ง", datetime.now())
        if st.form_submit_button("บันทึก"):
            if t and s:
                send_action({"action": "add", "task": t, "subject": s, "deadline": d.strftime("%d/%m/%Y")})
                st.rerun()

with tab_edit:
    if not data.empty:
        edit_target = st.selectbox("เลือกงานที่จะแก้ไข:", data['Task'].tolist())
        row = data[data['Task'] == edit_target].iloc[0]
        with st.form("edit_form"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                new_t = st.text_input("ชื่อภารกิจ", value=row['Task'])
                new_s = st.text_input("วิชา", value=row['Subject'])
            with col_e2:
                try:
                    curr_d = datetime.strptime(str(row['Deadline']), "%d/%m/%y")
                except:
                    curr_d = datetime.now()
                new_d = st.date_input("กำหนดส่งใหม่", value=curr_d)
                new_st = st.selectbox("เปลี่ยนสถานะ", ["waiting", "complete"], index=0 if row['Status'] == 'waiting' else 1)
            if st.form_submit_button("อัปเดต"):
                send_action({"action": "update", "old_task": edit_target, "task": new_t, "subject": new_s, "deadline": new_d.strftime("%d/%m/%Y"), "status": new_st})
                st.rerun()

with tab_del:
    if not data.empty:
        del_target = st.selectbox("เลือกงานที่จะลบ:", data['Task'].tolist())
        if st.button("🔥 ลบรายการ", type="primary"):
            send_action({"action": "delete", "task": del_target})
            st.rerun()