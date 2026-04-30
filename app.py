import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# URL ของ Web App จาก Google Apps Script
API_URL = "https://script.google.com/macros/s/AKfycbwtaTfO7oV14LjnAp-8fzu2y-k-aNk2izzonUPR4Zb9bO9-F_wkn_7S1FsTSHrcih8t/exec"

st.set_page_config(page_title="Tawan Assignment", layout="wide", page_icon="🌻")

# --- Custom CSS (Modern & Dark Mode Support) ---
st.markdown("""
    <style>
    .stMetric { padding: 15px; border-radius: 10px; border: 1px solid #444; }
    thead th { background-color: #222 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

def get_all_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            res = response.json()
            # 1. จัดการข้อมูลงาน
            df = pd.DataFrame(res.get("tasks", []))
            if not df.empty and 'Deadline' in df.columns:
                df['Deadline'] = pd.to_datetime(df['Deadline'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%y')
            
            # 2. จัดการข้อมูลวิชา
            subjects = res.get("subjects", [])
            if subjects and (subjects[0] == "Subject" or subjects[0] == "วิชา"):
                subjects = subjects[1:]
            
            subjects = sorted([str(s).strip() for s in subjects if s])
            return df, subjects
        return pd.DataFrame(), []
    except Exception as e:
        st.error(f"การดึงข้อมูลผิดพลาด: {e}")
        return pd.DataFrame(), []

def send_action(payload):
    try:
        requests.post(API_URL, json=payload)
    except Exception as e:
        st.error(f"Error: {e}")

# --- START UI ---
st.title("🌞 Tawan Assignment Tracker")

data, subjects_list = get_all_data()

if not data.empty:
    waiting_count = len(data[data['Status'] == 'Waiting'])
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.metric("งานที่ค้างอยู่", f"{waiting_count} รายการ")
    with col_m2:
        filter_status = st.radio("มุมมองข้อมูล:", options=["⏳ Waiting Only", "✅ Completed Only", "🗃️ All Tasks"], horizontal=True)

    display_df = data.copy()
    if filter_status == "⏳ Waiting Only":
        display_df = display_df[display_df['Status'] == 'Waiting']
    elif filter_status == "✅ Completed Only":
        display_df = display_df[display_df['Status'] == 'Complete']

    st.subheader("📋 รายการงานปัจจุบัน")
    
    def style_status(val):
        if val == 'Complete': 
            return 'color: #28a745; font-weight: bold;'
        elif val == 'Waiting': 
            return 'color: #ffc107; font-weight: bold;'
        return ''

    styled_df = display_df.style.map(style_status, subset=['Status'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังเชื่อมต่อข้อมูล...")

st.divider()

# --- CRUD TABS ---
tab_add, tab_edit, tab_del = st.tabs(["➕ เพิ่มงาน", "📝 แก้ไขสถานะ", "🗑️ ลบรายการ"])

with tab_add:
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            t = st.text_input("ชื่องาน", placeholder="ระบุชื่องาน หรือรายละเอียด")
            s = st.selectbox("เลือกวิชา", options=subjects_list if subjects_list else ["-- ไม่พบรายชื่อวิชา --"])
        with c2:
            d = st.date_input("กำหนดส่ง", datetime.now())
        
        if st.form_submit_button("บันทึกข้อมูล"):
            if t and s and s != "-- ไม่พบรายชื่อวิชา --":
                # ปรับ Default Status เป็น Waiting
                send_action({"action": "add", "task": t, "subject": s, "deadline": d.strftime("%d/%m/%Y"), "status": "Waiting"})
                st.success(f"บันทึกงาน '{t}' สำเร็จ!")
                st.rerun()
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")

with tab_edit:
    # กรองเฉพาะงานที่มีสถานะเป็น Waiting เท่านั้นสำหรับการแก้ไข
    waiting_tasks = data[data['Status'] == 'Waiting']
    
    if not waiting_tasks.empty:
        edit_target = st.selectbox("เลือกงานที่ยังค้างอยู่เพื่อแก้ไข/ปิดงาน:", waiting_tasks['Task'].tolist(), key="edit_box")
        row = waiting_tasks[waiting_tasks['Task'] == edit_target].iloc[0]
        
        with st.form("edit_form"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                new_t = st.text_input("แก้ไขชื่องาน", value=row['Task'])
                current_subject_idx = subjects_list.index(row['Subject']) if row['Subject'] in subjects_list else 0
                new_s = st.selectbox("วิชา", options=subjects_list, index=current_subject_idx)
            with col_e2:
                try:
                    curr_d = datetime.strptime(str(row['Deadline']), "%d/%m/%y")
                except:
                    curr_d = datetime.now()
                new_d = st.date_input("แก้ไขวันส่ง", value=curr_d)
                new_st = st.selectbox("เปลี่ยนสถานะเป็น", ["Waiting", "Complete"], index=0)
            
            if st.form_submit_button("ยืนยันการแก้ไข"):
                send_action({
                    "action": "update", 
                    "old_task": edit_target,
                    "task": new_t, 
                    "subject": new_s, 
                    "deadline": new_d.strftime("%d/%m/%Y"),
                    "status": new_st
                })
                st.success("อัปเดตข้อมูลเรียบร้อย!")
                st.rerun()
    else:
        st.info("🎉 ไม่มีงานค้างในระบบให้แก้ไขแล้ว!")

with tab_del:
    if not data.empty:
        del_target = st.selectbox("เลือกงานที่จะลบ:", data['Task'].tolist(), key="del_box")
        if st.button("🔥 ลบรายการนี้ถาวร", type="primary"):
            send_action({"action": "delete", "task": del_target})
            st.rerun()