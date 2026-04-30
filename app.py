import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# URL ของ Web App จาก Google Apps Script (ใช้ตัวเดิมของคุณ)
API_URL = "https://script.google.com/macros/s/AKfycbzCrQzdQp7WMEZ1OTPOSf2mbJJjz25vKF7pwv4BebL3I2Fzcu7N2bqvXz77wY2m7PHv/exec"

st.set_page_config(page_title="ICT Assignment Pro", layout="wide", page_icon="🎓")

# Custom CSS เพื่อให้เข้ากับสไตล์ ICT Classic ที่คุณชอบ
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    </style>
    """, unsafe_allow_stdio=True)

def get_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            raw_json = response.json()
            return pd.DataFrame(raw_json) if raw_json else pd.DataFrame()
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def send_action(payload):
    try:
        requests.post(API_URL, json=payload)
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- HEADER ---
st.title("🎓 ICT Assignment Tracker")
st.write("จัดการงานค้างและกำหนดส่งได้ง่ายๆ ผ่าน LINE OA")

data = get_data()

# --- DASHBOARD & FILTER ---
if not data.empty:
    # คัดกรองข้อมูลเบื้องต้น
    waiting_count = len(data[data['Status'] == 'waiting'])
    
    col_m1, col_m2, col_m3 = st.columns([1, 1, 2])
    with col_m1:
        st.metric("งานที่ค้างอยู่", f"{waiting_count} งาน", delta_color="inverse")
    
    with col_m3:
        # ฟิลเตอร์สถานะ (เริ่มต้นที่ 'Waiting Only')
        filter_status = st.segmented_control(
            "แสดงสถานะ:", 
            options=["Waiting Only", "Completed Only", "All Tasks"], 
            default="Waiting Only"
        )

    # ค้นหาด้วย Keyword
    search_query = st.text_input("🔍 ค้นหาวิชาหรือชื่องาน...", placeholder="พิมพ์ชื่อวิชา เช่น Networking...")

    # ประมวลผลข้อมูลตาม Filter
    display_df = data.copy()
    if filter_status == "Waiting Only":
        display_df = display_df[display_df['Status'] == 'waiting']
    elif filter_status == "Completed Only":
        display_df = display_df[display_df['Status'] == 'complete']
    
    if search_query:
        display_df = display_df[
            display_df['Task'].str.contains(search_query, case=False, na=False) | 
            display_df['Subject'].str.contains(search_query, case=False, na=False)
        ]

    # --- 1. ส่วนแสดงผลตารางงาน ---
    st.subheader("📋 รายการงาน")
    if not display_df.empty:
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=["waiting", "complete"], required=True),
                "Deadline": st.column_config.TextColumn("Deadline (DD/MM/YYYY)")
            }
        )
    else:
        st.info("ไม่พบรายการงานที่ตรงกับเงื่อนไข")
else:
    st.info("ยังไม่มีข้อมูลในระบบ เริ่มเพิ่มงานใหม่ได้ที่แท็บด้านล่าง")

st.divider()

# --- 2. MANAGEMENT TABS (CRUD) ---
tab_add, tab_edit, tab_del = st.tabs(["➕ เพิ่มงานใหม่", "📝 แก้ไขรายละเอียด", "🗑️ ลบรายการ"])

with tab_add:
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            t = st.text_input("ชื่องาน (Task)", placeholder="เช่น ทำแล็บ OSI Model")
            s = st.text_input("วิชา (Subject)", placeholder="เช่น Computer Network")
        with c2:
            d = st.date_input("กำหนดส่ง", datetime.now())
        
        if st.form_submit_button("➕ บันทึกงานเข้า Sheet"):
            if t and s:
                send_action({"action": "add", "task": t, "subject": s, "deadline": d.strftime("%d/%m/%Y")})
                st.success(f"เพิ่ม '{t}' เข้าสู่ระบบแล้ว!")
                st.rerun()
            else:
                st.warning("กรุณากรอกชื่อและวิชาให้ครบถ้วน")

with tab_edit:
    if not data.empty:
        edit_target = st.selectbox("เลือกงานที่จะแก้ไข:", data['Task'].tolist(), key="edit_box")
        row = data[data['Task'] == edit_target].iloc[0]
        
        with st.form("edit_form"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                new_t = st.text_input("แก้ไขชื่อภารกิจ", value=row['Task'])
                new_s = st.text_input("แก้ไขวิชา", value=row['Subject'])
            with col_e2:
                try:
                    curr_d = datetime.strptime(str(row['Deadline']), "%d/%m/%Y")
                except:
                    curr_d = datetime.now()
                new_d = st.date_input("เปลี่ยนกำหนดส่ง", value=curr_d)
                new_st = st.selectbox("สถานะการทำงาน", ["waiting", "complete"], index=0 if row['Status'] == 'waiting' else 1)
            
            if st.form_submit_button("💾 บันทึกการเปลี่ยนแปลง"):
                send_action({
                    "action": "update", 
                    "old_task": edit_target,
                    "task": new_t, 
                    "subject": new_s, 
                    "deadline": new_d.strftime("%d/%m/%Y"),
                    "status": new_st
                })
                st.balloons()
                st.rerun()
    else:
        st.write("ไม่มีข้อมูลให้แก้ไข")

with tab_del:
    if not data.empty:
        st.warning("ระวัง! การลบข้อมูลจะไม่สามารถกู้คืนได้")
        del_target = st.selectbox("เลือกงานที่จะลบถาวร:", data['Task'].tolist(), key="del_box")
        if st.button("🔥 ยืนยันการลบรายการ", type="primary"):
            send_action({"action": "delete", "task": del_target})
            st.success("ลบข้อมูลสำเร็จ")
            st.rerun()