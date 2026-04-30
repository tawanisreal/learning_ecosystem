import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# วาง URL ที่ได้จาก Google Apps Script ตรงนี้
API_URL = "https://script.google.com/macros/s/AKfycbwRMQZI8gTCvlQcHNgn-VDC9qma16iARVvY0bit6DP-ALqYtwf7szLgc_yaNMfA0G8/exec"

st.set_page_config(page_title="Assignment Tracker", layout="wide")

def get_data():
    response = requests.get(API_URL)
    return pd.DataFrame(response.json())

def send_action(payload):
    requests.post(API_URL, json=payload)

st.title("🎓 University Assignment Tracker")

try:
    data = get_data()
    
    # ส่วนแสดงงานทั้งหมด
    st.subheader("📋 รายการงานปัจจุบัน")
    if not data.empty:
        st.table(data) # ใช้ st.table จะแสดงผลได้นิ่งกว่าบนมือถือ
    else:
        st.info("ยังไม่มีงานในระบบ")

    st.divider()

    # ส่วนเพิ่มงาน และ ลบงาน
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("➕ เพิ่มงานใหม่")
        with st.form("add_form", clear_on_submit=True):
            t = st.text_input("ชื่องาน")
            s = st.text_input("วิชา")
            d = st.date_input("กำหนดส่ง")
            if st.form_submit_button("บันทึก"):
                send_action({"action": "add", "task": t, "subject": s, "deadline": d.strftime("%d/%m/%Y")})
                st.success("เพิ่มงานสำเร็จ!")
                st.rerun()

    with col2:
        st.subheader("🗑️ ลบงาน")
        if not data.empty:
            del_task = st.selectbox("เลือกงานที่จะลบ", data['Task'].tolist())
            if st.button("ลบรายการนี้", type="primary"):
                send_action({"action": "delete", "task": del_task})
                st.success("ลบงานเรียบร้อย!")
                st.rerun()

except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อข้อมูลได้ กรุณาตรวจสอบ URL: {e}")