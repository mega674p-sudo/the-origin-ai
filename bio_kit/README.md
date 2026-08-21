# 🧬 YouTube Shorts AI Automation Starter Kit (Biology Edition)

ชุดเครื่องมืออัตโนมัติ 100% สำหรับสร้างและอัปโหลดวิดีโอ YouTube Shorts แนวสารคดีชีววิทยา ธรรมชาติ และร่างกายมนุษย์ (สไตล์ Blurr Content) พร้อมเสียงพากย์ **Charon** ที่ปรับระดับเสียงให้ดังสะใจระดับ Extreme Audio Boost (x6)

---

## 📦 โครงสร้างไฟล์ในชุด (Kit Contents)
- `services/master_automation.py` - สคริปต์หลักรวบยอด (สุ่มหัวข้อชีววิทยา -> สร้างวิดีโอ -> อัปโหลด YouTube)
- `services/generate_dynamic_video.py` - สคริปต์สร้างบท, เสียง, ภาพ 8K, ซับไทย และบูสต์เสียงอัตโนมัติ
- `services/uploader.py` - สคริปต์จัดการอัปโหลดวิดีโอขึ้น YouTube ผ่าน OAuth2
- `workflows/ai_video_automation.json` - ไฟล์ Workflow สำหรับนำเข้า n8n เพื่อตั้งเวลารันอัตโนมัติ

---

## 🚀 วิธีการติดตั้งและใช้งาน

### 1. การติดตั้งสภาพแวดล้อม
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
pip3 install google-genai google-api-python-client oauth2client pillow gtts
```

### 2. การตั้งค่า API Keys
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```
วางไฟล์ `google_oauth_client.json` ไว้ที่ `~/.config/n8n/google_oauth_client.json`

### 3. การรันระบบ
```bash
python3 services/master_automation.py
```

---
*Developed with ❤️ by Manus AI*
