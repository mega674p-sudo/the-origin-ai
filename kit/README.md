# 🎬 YouTube Shorts AI Automation Starter Kit (Blurr Content Style)

ชุดเครื่องมืออัตโนมัติ 100% สำหรับสร้างและอัปโหลดวิดีโอ YouTube Shorts แนวสารคดีวิทยาศาสตร์ลึกลับ (สไตล์ Blurr Content) พร้อมเสียงพากย์ **Charon** และการผสมผสานฟุตเทจ NASA กับภาพ AI 8K

---

## 📦 โครงสร้างไฟล์ในชุด (Kit Contents)
- `services/master_automation.py` - สคริปต์หลักรวบยอด (สุ่มหัวข้อ -> สร้างวิดีโอ -> อัปโหลด YouTube)
- `services/assemble_dm_v2.py` - สคริปต์ประมวลผลวิดีโอ (FFmpeg, ซับไทย, ภาพ 8K, เสียงพากย์, BGM)
- `services/uploader.py` - สคริปต์จัดการอัปโหลดวิดีโอขึ้น YouTube ผ่าน OAuth2
- `workflows/ai_video_automation.json` - ไฟล์ Workflow สำหรับนำเข้า n8n เพื่อตั้งเวลารันอัตโนมัติ
- `used_topics.json` - ไฟล์เก็บบันทึกประวัติหัวข้อ เพื่อป้องกันไม่ให้ AI สุ่มหัวข้อซ้ำเดิม

---

## 🚀 วิธีการติดตั้งและใช้งาน (สำหรับ Manus หรือผู้ใช้ทั่วไป)

### 1. การติดตั้งสภาพแวดล้อม (Environment Setup)
ติดตั้งเครื่องมือและไลบรารีที่จำเป็นบนระบบ (เช่น Ubuntu / Sandbox):
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
pip3 install google-genai google-api-python-client oauth2client pillow
```

### 2. การตั้งค่า API Keys และ Credentials
- **Google Gemini API Key**: ตั้งค่าตัวแปรสภาพแวดล้อม
  ```bash
  export GEMINI_API_KEY="your-gemini-api-key"
  ```
- **YouTube API Credentials**: วางไฟล์ `google_oauth_client.json` ไว้ที่ตำแหน่งที่ `uploader.py` เรียกใช้ (เช่น `~/.config/n8n/google_oauth_client.json` หรือในโฟลเดอร์โปรเจกต์)

### 3. การรันระบบอัตโนมัติด้วยตนเอง (Manual Test)
ทดสอบรันสคริปต์หลักเพื่อสร้างคลิปและอัปโหลดทันที:
```bash
python3 services/master_automation.py
```

### 4. การตั้งค่า n8n Automation
1. เปิดหน้าจอ n8n (`http://localhost:5678`)
2. ไปที่เมนู **Workflows** แล้วกด **Import from File**
3. เลือกไฟล์ `workflows/ai_video_automation.json`
4. เปิดใช้งาน (Active) Workflow เพื่อให้ระบบรันอัตโนมัติตามเวลาที่กำหนด (ค่าเริ่มต้น: 08:00 น. และ 18:00 น. ทุกวัน)

---
*Developed with ❤️ by Manus AI*
