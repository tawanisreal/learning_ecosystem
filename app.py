import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# URL ของ Web App จาก Google Apps Script
API_URL = "https://script.google.com/macros/s/AKfycbwtaTfO7oV14LjnAp-8fzu2y-k-aNk2izzonUPR4Zb9bO9-F_wkn_7S1FsTSHrcih8t/exec"

st.set_page_config(page_title="Assignment Tracker", layout="wide")

def get_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            raw_json = response.json()
            if raw_json:
                return pd.DataFrame(raw_json)
            else:
                st.warning("⚠️ ดึงข้อมูลได้สำเร็จแต่ไม่มีข้อมูลใน Sheet (แผ่นงานว่างเปล่า)")
                return pd.DataFrame()
        else:
            st.error(f"❌ ดึงข้อมูลไม่สำเร็จ Status: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {e}")
        return pd.DataFrame()

def send_action(payload):
    try:
        requests.post(API_URL, json=payload)
    except Exception as e:
        st.error(f"Error: {e}")

st.title("🎓 University Assignment Tracker")

data = get_data()

# --- 1. ส่วนแสดงผลตารางงาน ---
st.subheader("📋 รายการงานปัจจุบัน")
if not data.empty:
    # แสดงตารางแบบสวยงาม
    st.dataframe(data, use_container_width=True, hide_index=True)
else:
    st.info("ยังไม่มีงานในระบบ")

st.divider()

# --- 2. ส่วนการจัดการข้อมูล (Add, Edit, Delete) ---
# ใช้ Tabs เพื่อประหยัดพื้นที่บนหน้าจอมือถือ
tab1, tab2, tab3 = st.tabs(["➕ เพิ่มงานใหม่", "📝 แก้ไขงาน", "🗑️ ลบงาน"])

with tab1:
    with st.form("add_form", clear_on_submit=True):
        t = st.text_input("ชื่องาน (Task)")
        s = st.text_input("วิชา (Subject)")
        d = st.date_input("กำหนดส่ง", datetime.now(), key="add_date")
        if st.form_submit_button("บันทึกงานใหม่"):
            if t and s:
                send_action({"action": "add", "task": t, "subject": s, "deadline": d.strftime("%d/%m/%Y")})
                st.success(f"เพิ่มงาน '{t}' สำเร็จ!")
                st.rerun()
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")

with tab2:
    if not data.empty:
        edit_target = st.selectbox("เลือกงานที่ต้องการแก้ไข", data['Task'].tolist(), key="edit_sel")
        row = data[data['Task'] == edit_target].iloc[0]
        
        with st.form("edit_form"):
            new_t = st.text_input("ชื่อภารกิจ", value=row['Task'])
            new_s = st.text_input("วิชา", value=row['Subject'])
            
            # แปลงวันที่เดิมกลับเป็น Date Object
            try:
                curr_d = datetime.strptime(str(row['Deadline']), "%d/%m/%Y")
            except:
                curr_d = datetime.now()
            
            new_d = st.date_input("กำหนดส่งใหม่", value=curr_d)
            new_st = st.selectbox("สถานะ", ["waiting", "complete"], index=0 if row['Status'] == 'waiting' else 1)
            
            if st.form_submit_button("อัปเดตข้อมูล"):
                send_action({
                    "action": "update", 
                    "old_task": edit_target,
                    "task": new_t, 
                    "subject": new_s, 
                    "deadline": new_d.strftime("%d/%m/%Y"),
                    "status": new_st
                })
                st.success("แก้ไขข้อมูลเรียบร้อย!")
                st.rerun()
    else:
        st.write("ไม่มีข้อมูลให้แก้ไข")

with tab3:
    if not data.empty:
        del_target = st.selectbox("เลือกงานที่จะลบ", data['Task'].tolist(), key="del_sel")
        if st.button("ยืนยันการลบ", type="primary"):
            send_action({"action": "delete", "task": del_target})
            st.success("ลบงานเรียบร้อย!")
            st.rerun()
    else:
        st.write("ไม่มีข้อมูลให้ลบ")