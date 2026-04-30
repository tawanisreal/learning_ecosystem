import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import json  # เพิ่มการนำเข้า json

# --- 1. ตั้งค่าการเชื่อมต่อ (เปลี่ยนวิธีดึงข้อมูลกุญแจ) ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# ดึงข้อมูลจาก st.secrets แทนการอ่านไฟล์ตรงๆ
service_account_info = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)

# เปิดไฟล์ Sheet (ตรวจสอบชื่อไฟล์ให้ตรงเป๊ะ)
sheet = client.open("My_Assignments").sheet1

st.set_page_config(page_title="Assignment Tracker", layout="wide")

# --- 2. ฟังก์ชันจัดการข้อมูล ---
def get_data():
    return pd.DataFrame(sheet.get_all_records())

def add_task(task, subject, deadline):
    sheet.append_row([task, subject, deadline, "waiting"])

def update_task(row_index, task, subject, deadline, status):
    # อัปเดตทั้งแถว (row_index + 2 เพราะแถวแรกคือ Header)
    sheet.update(f"A{row_index + 2}:D{row_index + 2}", [[task, subject, deadline, status]])

def delete_task(row_index):
    sheet.delete_rows(row_index + 2)

# --- 3. หน้าจอ UI ---
st.title("🎓 University Assignment Tracker")

# ดึงข้อมูลล่าสุด
data = get_data()

# --- ส่วนที่ 1: แสดงงานทั้งหมด ---
st.subheader("📋 รายการงานทั้งหมด")
if not data.empty:
    st.dataframe(data, use_container_width=True)
else:
    st.info("ยังไม่มีงานในระบบ")

st.divider()

# --- ส่วนที่ 2: เพิ่มงานใหม่ (Add Task) ---
st.subheader("➕ เพิ่มงานใหม่")
with st.form("add_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        new_task = st.text_input("ชื่องาน (Task)")
    with col2:
        new_subject = st.text_input("วิชา (Subject)")
    with col3:
        new_deadline = st.date_input("กำหนดส่ง (Deadline)", datetime.now())
    
    if st.form_submit_button("บันทึกงาน"):
        if new_task and new_subject:
            formatted_date = new_deadline.strftime("%d/%m/%Y")
            add_task(new_task, new_subject, formatted_date)
            st.success("บันทึกงานใหม่เรียบร้อย!")
            st.rerun()
        else:
            st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")

st.divider()

# --- ส่วนที่ 3: จัดการงานเดิม (Edit & Delete) ---
if not data.empty:
    st.subheader("⚙️ จัดการงานเดิม")
    col_edit, col_del = st.columns(2)
    
    with col_edit:
        with st.expander("📝 แก้ไขงาน"):
            edit_task_name = st.selectbox("เลือกงานที่จะแก้ไข", data['Task'].tolist(), key="edit_sel")
            row_to_edit = data[data['Task'] == edit_task_name].iloc[0]
            row_idx = data[data['Task'] == edit_task_name].index[0]

            with st.form("edit_form"):
                e_t = st.text_input("ชื่อภารกิจ", value=row_to_edit['Task'])
                e_s = st.text_input("วิชา", value=row_to_edit['Subject'])
                try:
                    curr_d = datetime.strptime(str(row_to_edit['Deadline']), "%d/%m/%Y")
                except:
                    curr_d = datetime.now()
                e_d = st.date_input("กำหนดส่งใหม่", value=curr_d)
                e_st = st.selectbox("สถานะ", ["waiting", "complete"], index=0 if row_to_edit['Status'] == 'waiting' else 1)
                
                if st.form_submit_button("ยืนยันการแก้ไข"):
                    update_task(row_idx, e_t, e_s, e_d.strftime("%d/%m/%Y"), e_st)
                    st.success("อัปเดตเรียบร้อย!")
                    st.rerun()

    with col_del:
        with st.expander("🗑️ ลบงาน"):
            del_task_name = st.selectbox("เลือกงานที่จะลบ", data['Task'].tolist(), key="del_sel")
            if st.button("ยืนยันการลบ", type="primary"):
                idx = data[data['Task'] == del_task_name].index[0]
                delete_task(idx)
                st.success("ลบงานเรียบร้อย!")
                st.rerun()