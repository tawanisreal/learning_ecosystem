import streamlit as st
import pandas as pd
import requests
from datetime import datetime

API_URL = "https://script.google.com/macros/s/AKfycbzqSVvrWItgNP2kCloot03ODDF70VCKxnOE0CSh20G7_K2JqmdLflZu-J4lOwPL6tom/exec"

st.set_page_config(page_title="Tawan Assignment", layout="wide", page_icon="🌻")

# ใช้การโหลดข้อมูลแบบ Cache เพื่อความรวดเร็ว
@st.cache_data(ttl=30) # เก็บข้อมูลไว้ 30 วินาที ลดการดึง API บ่อย
def fetch_data():
    try:
        response = requests.get(API_URL, timeout=10) # เพิ่ม timeout ป้องกันค้าง
        if response.status_code == 200:
            res = response.json()
            df = pd.DataFrame(res.get("tasks", []))
            
            # จัดการวันที่ให้ตรงกับ Sheets (ใช้ Plain Text เพื่อความเร็ว)
            if not df.empty and 'Deadline' in df.columns:
                df['Deadline'] = pd.to_datetime(df['Deadline'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%y')
            
            subjects = res.get("subjects", [])
            if subjects and subjects[0] in ["Subject", "วิชา"]:
                subjects = subjects[1:]
            
            return df, sorted([str(s).strip() for s in subjects if s])
    except:
        return pd.DataFrame(), []
    return pd.DataFrame(), []

# --- UI START ---
st.title("🌞 Tawan Assignment Tracker")

data, subjects_list = fetch_data()

if not data.empty:
    waiting_tasks = data[data['Status'].str.contains('Waiting', case=False, na=False)]
    
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.metric("งานที่ค้างอยู่", f"{len(waiting_tasks)} รายการ")
    with col_m2:
        filter_status = st.radio("มุมมอง:", options=["⏳ Waiting Only", "✅ Completed Only", "🗃️ All Tasks"], horizontal=True)

    # กรองข้อมูล
    display_df = data.copy()
    if "Waiting Only" in filter_status:
        display_df = waiting_tasks
    elif "Completed Only" in filter_status:
        display_df = data[data['Status'].str.contains('Complete', case=False, na=False)]

    # แสดงผลตารางแบบ Minimal Style
    def style_status(val):
        v = str(val).lower()
        if v == 'complete': return 'color: #28a745; font-weight: bold;'
        if v == 'waiting': return 'color: #ffc107; font-weight: bold;'
        return ''

    st.dataframe(display_df.style.map(style_status, subset=['Status']), use_container_width=True, hide_index=True)

st.divider()

# --- Tabs ---
tab_add, tab_edit, tab_del = st.tabs(["➕ เพิ่มงาน", "📝 แก้ไขสถานะ", "🗑️ ลบรายการ"])

def send_update(payload):
    requests.post(API_URL, json=payload)
    st.cache_data.clear() # ล้าง Cache เมื่อมีการแก้ไขข้อมูลเพื่อให้ข้อมูลใหม่แสดงทันที
    st.rerun()

with tab_add:
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            t = st.text_input("ชื่องาน")
            s = st.selectbox("เลือกวิชา", options=subjects_list if subjects_list else ["-- ไม่มีวิชา --"], index=None, placeholder="--- เลือวิชา ---",)
        with c2:
            d = st.date_input("กำหนดส่ง", datetime.now())
        # ในส่วน tab_add ของ app.py
        if st.form_submit_button("บันทึก"):
            if t and s:
                # ใส่เครื่องหมาย ' นำหน้าวันที่ก่อนส่งไปที่ API
                plain_text_deadline = f"'{d.strftime('%d/%m/%Y')}"
                
                send_update({
                    "action": "add", 
                    "task": t, 
                    "subject": s, 
                    "deadline": plain_text_deadline, # ส่งค่าที่มี ' นำหน้า
                    "status": "Waiting"
                })

with tab_edit:
    if not waiting_tasks.empty:
        # ดึงรายชื่อจากคอลัมน์ Task มาทำเป็น list
        task_options = waiting_tasks['Task'].tolist()
        
        # ปรับ index=None เพื่อให้เริ่มต้นเป็นค่าว่าง (Placeholder)
        edit_target = st.selectbox(
            "แก้ไขงานค้าง:", 
            options=task_options,
            index=None, 
            placeholder="--- เลือกงานที่ต้องการแก้ไข ---"
        )
        
        # ตรวจสอบว่ามีการเลือกงานแล้วจริงๆ (ไม่ใช่ค่า None)
        if edit_target:
            row = waiting_tasks[waiting_tasks['Task'] == edit_target].iloc[0]
            with st.form("edit_form"):
                # แสดงรายละเอียดงานที่กำลังแก้ไขเพื่อให้แน่ใจ
                st.write(f"กำลังแก้ไขงาน: **{edit_target}**")
                
                # กำหนดค่า default ของสถานะตามข้อมูลจริงในแถวนั้น
                current_status = "Waiting" if row['Status'] == "Waiting" else "Complete"
                new_st = st.selectbox("เปลี่ยนสถานะเป็น", ["Waiting", "Complete"], index=["Waiting", "Complete"].index(current_status))
                
                if st.form_submit_button("อัปเดต"):
                    send_update({
                        "action": "update", 
                        "old_task": edit_target, 
                        "task": row['Task'], 
                        "subject": row['Subject'], 
                        "deadline": row['Deadline'], 
                        "status": new_st
                    })
                    st.success(f"อัปเดตสถานะงาน '{edit_target}' เรียบร้อย!")
                    st.rerun() # สั่งให้แอปรีโหลดข้อมูลใหม่หลังจากอัปเดต
    else:
        st.info("ไม่มีงานค้างให้แก้ไข")

with tab_del:
    # กรองเฉพาะงานที่มีสถานะเป็น Waiting สำหรับการลบ
    delete_candidates = data[data['Status'].str.contains('Waiting', case=False, na=False)]
    
    if not delete_candidates.empty:
        # กำหนดค่า default เป็น None และใส่ placeholder เพื่อให้ดูเหมือนยังไม่ได้เลือก
        del_target = st.selectbox(
            "ลบงานค้าง:",
            options=delete_candidates['Task'].tolist(),
            index=None,
            placeholder="--- เลือกงานที่ต้องการลบ ---",
            key="del_box_new"
        )
        
        # ตรวจสอบว่ามีการเลือกงานแล้วจริงๆ ถึงจะกดปุ่มลบได้
        if del_target:
            if st.button("🔥 ยืนยันการลบ", type="primary"):
                send_update({"action": "delete", "task": del_target})
                # ระบบจะ rerun อัตโนมัติจากฟังก์ชัน send_update ที่เราเขียนไว้
    else:
        st.info("✨ ไม่มีงานค้างในระบบให้ลบ")
            