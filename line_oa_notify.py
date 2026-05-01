import os
import json
import gspread
from google.oauth2.service_account import Credentials
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from datetime import datetime

# รูปแบบใหม่ที่ใช้ google-auth (ตามที่คุยกันก่อนหน้า)
google_json_str = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
creds_info = json.loads(google_json_str)
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# บรรทัดนี้สำคัญมาก ต้องเปลี่ยนเป็น Credentials.from_service_account_info
creds = Credentials.from_service_account_info(creds_info, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("My_Assignments").sheet1

# --- 2. ตั้งค่า LINE Messaging API ---
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.environ.get('LINE_USER_ID')
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

def send_line_push(message_text):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        push_message_request = PushMessageRequest(
            to=USER_ID,
            messages=[TextMessage(text=message_text)]
        )
        try:
            line_bot_api.push_message(push_message_request)
            print("✅ ส่งการแจ้งเตือนเข้า LINE เรียบร้อยแล้ว")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการส่ง LINE: {e}")

# --- 3. ฟังก์ชันเช็กงานและแจ้งเตือน ---
def check_assignments_and_notify():
    # ดึงข้อมูลทั้งหมด
    all_tasks = sheet.get_all_records()
    today = datetime.now().date() # ใช้เฉพาะวันที่เพื่อการเปรียบเทียบที่แม่นยำ
    notification_list = []

    print(f"🔍 เริ่มตรวจสอบงาน... (วันนี้คือ: {today.strftime('%d/%m/%Y')})")

    for task in all_tasks:
        # ดึงสถานะและลบช่องว่างทับศัพท์ตัวเล็กใหญ่
        status = str(task.get('Status', '')).strip()
        
        # เช็กเฉพาะงานที่ยังไม่เสร็จ (ไม่ใช่ 'Complete')
        if status != 'Complete':
            try:
                # จัดการวันที่ ลบเครื่องหมาย ' ออกถ้ามี
                deadline_str = str(task.get('Deadline', '')).replace("'", "").strip()
                if not deadline_str: continue
                
                deadline_date = datetime.strptime(deadline_str, '%d/%m/%Y').date()
                
                # ตรรกะการแจ้งเตือน
                if deadline_date == today:
                    notification_list.append(f"📌 {task['Task']}\n⚠️ ต้องส่งภายในวันนี้! 💀")
                elif deadline_date > today:
                    diff = (deadline_date - today).days
                    # แจ้งเตือนถ้างงานส่งภายใน 3 วัน หรือตามความเหมาะสม
                    notification_list.append(f"📌 {task['Task']}\n📅 ส่งในอีก {diff} วัน ({deadline_str})")
                    
            except ValueError as e:
                print(f"⚠️ ข้ามงาน {task.get('Task')}: รูปแบบวันที่ผิด ({task.get('Deadline')})")
                continue

    if notification_list:
        summary_message = "📢 Tawan Assignment Tracker\nแจ้งเตือนงานใกล้กำหนดส่ง!\n\n" + "\n\n".join(notification_list)
        send_line_push(summary_message)
    else:
        print("💡 ไม่มีงานที่ตรงตามเงื่อนไขการแจ้งเตือน")

if __name__ == "__main__":
    check_assignments_and_notify()
