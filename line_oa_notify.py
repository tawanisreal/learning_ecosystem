import gspread
from oauth2client.service_account import ServiceAccountCredentials
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from datetime import datetime, timedelta

# --- 1. ตั้งค่า Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("My_Assignments").sheet1

# --- 2. ตั้งค่า LINE Messaging API ---
CHANNEL_ACCESS_TOKEN = 'GbmZbSXVxQcqBhL1TcaZo4dB82lrJhS0JK4icaLcwlhDsILhKKpRwrqL3GHPAHojAAonnvVQCNBARXz4GrteFk9XXYBl5GC5LzJlGQMRHptIKrMQOFDsqPaIzcVDzS17QJ4A8xKAtLPKyHvXBiORLAdB04t89/1O/w1cDnyilFU='
USER_ID = 'Ufa1d80e239eff8c82d46f55ac2488e1c' # ดูได้จากหน้า Basic Settings ใน LINE Developers

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
    all_tasks = sheet.get_all_records()
    today = datetime.now()
    notification_list = []

    print(f"🔍 เริ่มตรวจสอบงาน... (วันนี้คือ: {today.strftime('%d/%m/%Y')})")

    for task in all_tasks:
        status = str(task.get('Status')).lower()
        # เช็กงานที่สถานะไม่ใช่ 'done' หรือ 'complete'
        if status not in ['done', 'complete']:
            try:
                # ปรับให้รองรับรูปแบบ วัน/เดือน/ปี (2026) ตามในรูปของคุณ
                deadline = datetime.strptime(str(task['Deadline']), '%d/%m/%Y')
                
                # เช็กว่างานจะถึงกำหนดในอีก 3 วัน (ปรับให้กว้างขึ้นเพื่อทดสอบ)
                if today <= deadline <= today + timedelta(days=3):
                    diff = (deadline - today).days + 1
                    notification_list.append(f"📌 {task['Task']}\n📅 ส่งใน: {diff} วัน ({task['Deadline']})")
                    print(f"✅ พบงานใกล้กำหนด: {task['Task']}")
            except ValueError:
                print(f"⚠️ รูปแบบวันที่ผิดพลาดในงาน: {task['Task']} (ค่าที่พบ: {task['Deadline']})")
                continue

    if notification_list:
        summary_message = "📢 แจ้งเตือนงานใกล้กำหนดส่ง!\n\n" + "\n\n".join(notification_list)
        send_line_push(summary_message)
    else:
        print("💡 ไม่มีงานที่ตรงตามเงื่อนไขการแจ้งเตือน")

# รันระบบ
if __name__ == "__main__":
    check_assignments_and_notify()