# คู่มือใช้งาน GIGA PHONE AI แบบ Hybrid Coding Agent

เอกสารนี้อธิบายวิธีใช้งานรุ่นที่เหมาะกับงานหนักที่สุดของ **GIGA PHONE AI** โดยแยกหน้าที่อย่างชัดเจน: โทรศัพท์ Redmi 10a ใช้แอป Telegram เป็นแผงควบคุมและอนุมัติคำสั่ง ส่วนเครื่อง Ubuntu ที่เปิดใช้งานอยู่ทำหน้าที่เป็น worker สำหรับวิเคราะห์โค้ด รันคำสั่ง ทดสอบ ตรวจผล และจัดการ Git

> โทรศัพท์ไม่ต้องรัน Ollama และไม่ต้องโหลดโมเดลภาษาใด ๆ การให้ Gemini ทำ reasoning ผ่าน API ช่วยลดภาระ RAM ของ Redmi 10a แต่ Ubuntu worker ยังต้องมีอินเทอร์เน็ตเพื่อเชื่อม Telegram และ Gemini

## 1. โครงสร้างการทำงาน

| ส่วน | หน้าที่ |
|---|---|
| Redmi 10a | เปิด Telegram เพื่อส่งงาน ดูแผน และกดยืนยันด้วย task ID |
| Telegram Bot API | รับคำสั่งแบบ long polling และส่งผลลัพธ์กลับแบบจำกัดขนาด |
| Ubuntu worker | รัน `main.py`, shell tools, tests, Git และงาน pipeline ใน workspace ที่กำหนด |
| Gemini API | ทำหน้าที่ planner, security reviewer, error corrector และ verifier |
| Local policy | ตรวจคำสั่งทุกครั้งก่อน shell execution ด้วยกฎ deterministic ไม่พึ่ง Gemini |
| Runtime state | เก็บ task state, audit JSONL, memory และ checkpoint ใน `data/` ซึ่งไม่ commit เข้า Git |

ลำดับหลักคือ **planner → security reviewer → executor → verifier** โดย `/task` จะยังไม่รันคำสั่งทันที ระบบจะแสดงรายการคำสั่งและสร้าง task ID ก่อนเสมอ

## 2. ติดตั้งบน Ubuntu

ให้เปิด Terminal บนเครื่อง Ubuntu ที่จะเป็น worker แล้วรันคำสั่งต่อไปนี้

```bash
git clone https://github.com/mega674p-sudo/the-origin-ai.git
cd the-origin-ai
bash setup_ubuntu.sh
```

สคริปต์จะติดตั้งเฉพาะ runtime ขนาดเล็กที่จำเป็น ได้แก่ Git, Python 3 และ `python3-requests` จากนั้นจะถามข้อมูลต่อไปนี้แบบโต้ตอบ

| ข้อมูล | วิธีใช้ |
|---|---|
| Gemini API key | ใช้สำหรับวางแผน แก้ error และตรวจผล |
| Telegram bot token | token จาก BotFather |
| Telegram chat/user | เปิดแชตกับบอต ส่ง `/start` แล้วกด Enter ตามที่สคริปต์แจ้ง |

ค่าลับจะถูกเขียนไว้ที่ `config/settings.local.json` ซึ่งถูกใส่ใน `.gitignore` และตั้ง permission เป็น `600` ห้ามนำค่าลับไปใส่ใน `config/settings.json`, goal, shell command หรือ commit message

เมื่อ setup เสร็จ ระบบจะรันทดสอบทั้งหมดก่อนเริ่ม worker หากต้องการเริ่มใหม่ภายหลัง ให้ใช้

```bash
cd ~/the-origin-ai
bash start_worker.sh
```

`start_giga.sh` ยังเก็บไว้เป็น compatibility launcher สำหรับ Termux และจะเรียก worker แบบเดียวกัน โดยเปิด `termux-wake-lock` เฉพาะเมื่อคำสั่งนี้มีอยู่ในระบบ

## 3. Workflow ที่แนะนำ

เริ่มด้วยการส่งงานใน Telegram

```text
/task ตรวจไฟล์ Python ใน workspace และรัน unit tests ที่เกี่ยวข้อง
```

ระบบจะส่งแผนพร้อม task ID เช่น `task_1770000000_a1b2c3` กลับมา ให้ตรวจ command, purpose, policy label และ verification command ก่อน หากแผนเหมาะสมจึงส่ง

```text
/approve task_1770000000_a1b2c3
```

การอนุมัติต้องใช้ task ID ที่ตรงกันเท่านั้น หากส่ง ID ผิดระบบจะไม่รันคำสั่ง สำหรับงานที่เกี่ยวข้องกับ Git เช่น `git commit` หรือ `git push` ระบบจะหยุดและบังคับให้สร้าง checkpoint ก่อน

```text
/checkpoint before-git
/approve task_1770000000_a1b2c3
```

## 4. คำสั่ง Telegram ที่สำคัญ

| คำสั่ง | พฤติกรรม |
|---|---|
| `/task <goal>` | ให้ Gemini สร้างแผนและ security review โดยยังไม่รันคำสั่ง |
| `/approve <task-id>` | อนุมัติและเริ่ม sequential execution ของแผนที่ตรงกัน |
| `/cancel <task-id>` | ลบแผนที่รออนุมัติเมื่อ task ID ตรงกัน |
| `/explore <command>` | รันเฉพาะคำสั่ง read-only เช่น `pwd`, `ls -la`, `git status` |
| `/inspect <command>` | alias ของ `/explore` |
| `/review` | แสดง Git status, diff stat, diff check และ commit ล่าสุดแบบ read-only |
| `/checkpoint [label]` | สร้าง snapshot ของ review, task state และ memory ก่อนงานเสี่ยง |
| `/debug <request>` | ใช้ debug playbook แล้วสร้าง task plan |
| `/review <request>` | ใช้ review playbook แล้วสร้าง task plan |
| `/deploy <request>` | ใช้ deploy playbook พร้อม health check และ rollback evidence |
| `/n8n <request>` | ใช้ playbook สำหรับ n8n โดยแยก credential และ health check |
| `/video <request>` | ใช้ playbook สำหรับงาน media pipeline บน Ubuntu |
| `/run <command>` | รันเฉพาะคำสั่งที่ local policy จัดเป็น low-risk; คำสั่ง review-sensitive ต้องใช้ `/task` |
| `/status` | ดูสถานะ task ปัจจุบัน |
| `/help` | แสดงรายการคำสั่ง |

## 5. ขอบเขตความปลอดภัย

Local policy ทำงานก่อน shell ทุกครั้งและแบ่งผลเป็นสามระดับ

| ผล | ตัวอย่าง | การดำเนินการ |
|---|---|---|
| `allow` | `pwd`, `ls`, `git status` | อนุญาตตามเส้นทางที่กำหนด |
| `review` | `git commit`, `git push`, `pip install`, `python3 script.py`, file mutation | ต้องอยู่ใน task plan และได้รับ `/approve <task-id>` |
| `deny` | `rm -rf`, `sudo`, `su`, `mkfs`, `dd if=`, reboot/shutdown, download-and-execute | บล็อกทันที |

เมื่อคำสั่งล้มเหลว SelfCorrector จะส่ง error ที่จำเป็นไป Gemini เพื่อขอคำสั่งแก้ไขที่มีขอบเขต แต่คำสั่งแก้ไขจะถูกตรวจ policy ซ้ำก่อนรัน จึงไม่สามารถใช้ Gemini เพื่อข้าม local safety boundary ได้

## 6. การตรวจสอบและข้อมูลหลักฐาน

แต่ละ task สามารถมี `verify` command แบบ read-only ต่อ step ได้ เช่น ตรวจ `git status`, ตรวจไฟล์ที่สร้าง หรือรัน test แบบที่ planner ประกาศไว้ หาก verification ล้มเหลว task จะไม่ถูกประกาศว่าสำเร็จ ระบบจะรายงานสถานะ `verification_failed` แทน

ไฟล์ runtime สำคัญมีดังนี้

| ไฟล์ | หน้าที่ |
|---|---|
| `data/pending_task.json` | task ที่รออนุมัติหรือกำลังทำงาน |
| `data/audit.jsonl` | audit แบบ append-only และจำกัดขนาด พร้อม redaction เบื้องต้น |
| `data/memory.json` | memory ล่าสุดแบบ bounded สูงสุด 40 รายการ |
| `data/checkpoints/` | snapshot ก่อนงาน Git หรือการเปลี่ยนแปลงเสี่ยง |

ข้อมูลใน `data/` ถูก ignore จาก Git แต่ยังควรป้องกัน permission ของเครื่อง Ubuntu และไม่ส่งไฟล์เหล่านี้ให้บุคคลอื่นโดยไม่ตรวจสอบก่อน

## 7. การทดสอบและการอัปเดต

รันชุดทดสอบจาก project root ได้ด้วย

```bash
python3 -m unittest -v test_*.py
```

ตรวจ shell syntax และ policy smoke check ได้ด้วย

```bash
bash -n setup_ubuntu.sh setup_termux.sh start_giga.sh start_worker.sh
python3 -m py_compile main.py core/*.py
```

เมื่อจะอัปเดต worker ให้ตรวจแผนก่อน จากนั้นรัน

```bash
git pull --ff-only origin main
python3 -m unittest -v test_*.py
bash start_worker.sh
```

การเปลี่ยนแปลงล่าสุดที่เผยแพร่แล้วอยู่ใน commit `4b71f43` บน branch `main` ของ [mega674p-sudo/the-origin-ai](https://github.com/mega674p-sudo/the-origin-ai)

## 8. ข้อจำกัดที่ควรรู้

รุ่นนี้เป็นสถาปัตยกรรม hybrid ที่เน้นความปลอดภัยและการใช้งานหนัก ไม่ใช่การคัดลอก Claude Code แบบหนึ่งต่อหนึ่ง และไม่ควรตีความว่า Gemini สามารถอนุมัติคำสั่งแทนผู้ใช้ได้ จุดอนุมัติที่ Telegram และ local policy ยังคงเป็นขอบเขตบังคับ

นอกจากนี้ worker รุ่นนี้ทำงานแบบ sequential เพื่อควบคุม RAM และทำให้ audit ตรวจสอบย้อนกลับได้ จึงยังไม่มี parallel subagents, browser automation หรือการ push/publication แบบไร้การอนุมัติ งานที่ใช้เวลานานมากควรตั้ง `execution.timeout` ให้เหมาะกับเครื่อง Ubuntu และแบ่งเป็น task ย่อยเพื่อให้ verifier ให้หลักฐานได้ชัดเจน
