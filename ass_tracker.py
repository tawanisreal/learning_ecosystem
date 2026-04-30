import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
print("Current Location:", os.getcwd())

# 1. ตั้งค่าสิทธิ์ (ไม่ต้องแก้)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    # 2. ใส่ชื่อไฟล์ JSON ที่คุณโหลดมา
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # 3. ใส่ชื่อไฟล์ Google Sheet ของคุณ
    spreadsheet = client.open("My_Assignments")
    sheet = spreadsheet.sheet1 # เลือก Sheet หน้าแรก

    def check_pending_tasks():
        all_tasks = sheet.get_all_records()
        
        print("📋 รายการงานที่ยังไม่เสร็จ:")
        count = 0
        for task in all_tasks:
            # เช็กว่าช่อง Status ไม่เท่ากับ 'Done' (แก้ชื่อ Column ให้ตรงกับใน Sheet)
            if task.get('Status') != 'Done':
                print(f"🔹 {task.get('Task')} | วิชา: {task.get('Subject')} | ส่ง: {task.get('Deadline')}")
                count += 1
        
        if count == 0:
            print("🎉 ยินดีด้วย! ไม่มีงานค้างแล้ว")

    check_pending_tasks()

except FileNotFoundError:
    print("❌ ไม่พบไฟล์ credentials.json ในโฟลเดอร์เดียวกับโค้ด")
except gspread.exceptions.SpreadsheetNotFound:
    print("❌ ไม่พบไฟล์ Google Sheet ชื่อนี้ (ตรวจสอบการพิมพ์หรือการ Share Email)")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")