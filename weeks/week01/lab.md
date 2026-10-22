---
title: "ปฏิบัติการสัปดาห์ที่ 1: ตั้งค่าสภาพแวดล้อมและสร้าง repository โครงการ"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO1
> **ผลงานที่ต้องส่ง:** ลิงก์ repository บน GitHub ที่มี pull request แรกถูก merge แล้ว

## สิ่งที่ต้องเตรียม

- บัญชี GitHub (สมัครด้วยอีเมลมหาวิทยาลัยเพื่อขอ GitHub Student Developer Pack ได้)
- คอมพิวเตอร์ที่ติดตั้งโปรแกรมได้ ถ้าเครื่องไม่พร้อมให้ใช้ Google Colab แทนในขั้นที่ 3 แต่ขั้นที่ 4–6 ยังต้องทำบนเครื่องห้องปฏิบัติการ

---

## ขั้นที่ 1: ติดตั้งโปรแกรมพื้นฐาน

ติดตั้งให้ครบตามลำดับ

1. **Git** — <https://git-scm.com/downloads> (Windows: เลือก "Git from the command line and also from 3rd-party software")
2. **VS Code** — <https://code.visualstudio.com/> แล้วติดตั้ง extension: *Python*, *Jupyter*
3. เลือกติดตั้ง **อย่างใดอย่างหนึ่ง**
   - **Miniforge** (conda) — <https://conda-forge.org/download/>
   - **uv** — <https://docs.astral.sh/uv/getting-started/installation/>

ตรวจสอบใน terminal

```bash
git --version
code --version
conda --version     # ถ้าเลือก conda
uv --version        # ถ้าเลือก uv
```

## ขั้นที่ 2: ตั้งค่า Git ครั้งแรก

```bash
git config --global user.name "ชื่อ นามสกุล"
git config --global user.email "อีเมลที่ใช้สมัคร GitHub"
git config --global init.defaultBranch main
```

## ขั้นที่ 3: สร้างสภาพแวดล้อมของรายวิชา

ดาวน์โหลด `environment.yml` (หรือ `pyproject.toml`) จาก repository รายวิชา แล้วรัน

```bash
# conda
conda env create -f environment.yml
conda activate dstoolbox

# หรือ uv (รันในโฟลเดอร์ที่มี pyproject.toml)
uv sync
```

ทดสอบว่าไลบรารีหลักพร้อมใช้

```bash
python -c "import pandas, duckdb, plotly, streamlit; print('พร้อมใช้งาน')"
```

> การติดตั้งครั้งแรกใช้เวลา 5–15 นาที ระหว่างรอให้ทำขั้นที่ 4 ต่อได้

## ขั้นที่ 4: สร้าง repository โครงการบน GitHub

1. ไปที่ GitHub → **New repository**
2. ตั้งชื่อตามโดเมนที่เลือก เช่น `pm25-explorer`
3. เลือก **Public** · ติ๊ก **Add a README file** · เลือก `.gitignore` template เป็น **Python**
4. กด **Create repository**

clone ลงเครื่อง

```bash
cd ~/projects                 # หรือโฟลเดอร์ที่ต้องการ
git clone https://github.com/<username>/pm25-explorer.git
cd pm25-explorer
code .                        # เปิดใน VS Code
```

## ขั้นที่ 5: สร้างโครงสร้างโครงการบน branch ใหม่

```bash
git switch -c week01-setup
mkdir src notebooks app
```

แก้ไขไฟล์ต่อไปนี้

**1) `.gitignore`** — เพิ่มท้ายไฟล์

```text
data/
*.duckdb
*.duckdb.wal
.env
```

**2) `README.md`** — เขียนอย่างน้อย

```markdown
# PM2.5 Explorer

ระบบสำรวจคุณภาพอากาศ PM2.5 ของประเทศไทย (รายวิชา 1145100 Data Science Toolbox)

## วิธีติดตั้ง
conda env create -f environment.yml

## ผู้จัดทำ
ชื่อ–สกุล รหัสนักศึกษา
```

**3) `AI_USAGE.md`** — สร้างไฟล์ว่างพร้อมหัวตาราง

```markdown
| วันที่ | ใช้ AI ช่วยเรื่องอะไร | เครื่องมือ | ตรวจสอบผลอย่างไร |
|---|---|---|---|
```

**4)** คัดลอก `environment.yml` ของรายวิชาเข้ามาไว้ใน repo

**5) `notebooks/01_hello.ipynb`** — สร้าง notebook เลือก kernel `dstoolbox` แล้วรัน

```python
import sys, pandas as pd, duckdb
print(sys.version)
print("pandas", pd.__version__, "| duckdb", duckdb.__version__)
duckdb.sql("SELECT 'สวัสดี EDA' AS msg").df()
```

> **โฟลเดอร์ว่าง:** Git ไม่ติดตามโฟลเดอร์ว่าง ถ้าโฟลเดอร์ `src/` และ `app/` ยังไม่มีไฟล์ ให้สร้างไฟล์ว่างชื่อ `.gitkeep` ไว้ในโฟลเดอร์นั้น

## ขั้นที่ 6: commit, push และเปิด pull request

```bash
git status
git add .gitignore README.md AI_USAGE.md environment.yml notebooks/ src/ app/
git commit -m "ตั้งโครงสร้างโครงการและสภาพแวดล้อม"
git push -u origin week01-setup
```

บน GitHub

1. กด **Compare & pull request**
2. เขียนคำอธิบายว่า PR นี้ทำอะไร
3. **ขอ review จากเพื่อน 1 คน** (Reviewers → ใส่ username ของเพื่อน)
4. เมื่อเพื่อน approve แล้ว กด **Merge pull request**

กลับมาที่เครื่อง

```bash
git switch main
git pull
```

## ขั้นที่ 7: review PR ของเพื่อน

เปิด PR ที่เพื่อนขอให้ review แล้วตรวจตาม checklist นี้ ก่อนกด **Approve** หรือ **Request changes**

- [ ] `.gitignore` มี `data/` และ `.env`
- [ ] README บอกได้ว่าโครงการนี้คืออะไรและติดตั้งอย่างไร
- [ ] ไม่มีไฟล์ข้อมูล รหัสผ่าน หรือ output ขนาดใหญ่ถูก commit
- [ ] commit message สื่อความหมาย

เขียนความคิดเห็นอย่างน้อย 1 ข้อที่เป็นประโยชน์ ไม่ใช่แค่ "LGTM"

---

## Checklist ก่อนส่งงาน

- [ ] `python -c "import pandas, duckdb, plotly, streamlit"` รันผ่าน
- [ ] repo มี `README.md`, `.gitignore`, `AI_USAGE.md`, `environment.yml`, `notebooks/01_hello.ipynb`
- [ ] มี PR อย่างน้อย 1 รายการที่เพื่อน review และ merge แล้ว
- [ ] ได้ review PR ของเพื่อนอย่างน้อย 1 รายการ
- [ ] ส่งลิงก์ repo ในระบบส่งงานของรายวิชา

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `conda: command not found` | เปิด terminal ใหม่หลังติดตั้ง หรือใช้ "Miniforge Prompt" บน Windows |
| VS Code ไม่เห็น kernel `dstoolbox` | กด `Ctrl+Shift+P` → *Python: Select Interpreter* → เลือก `dstoolbox` |
| `git push` ขอรหัสผ่านแล้วไม่ผ่าน | GitHub ไม่รับรหัสผ่านบัญชีแล้ว ให้ login ผ่าน browser ที่ Git Credential Manager เปิดขึ้น หรือใช้ `gh auth login` |
| ติดตั้ง GeoPandas ด้วย pip แล้ว error | ใช้ conda (Miniforge) แทน เพราะ GeoPandas มีส่วนประกอบภาษา C |
| เผลอ commit ไฟล์ `.env` | **เปลี่ยน key ใหม่ทันที** แล้วลบไฟล์ออก (`git rm --cached .env`) และเพิ่มใน `.gitignore` การลบออกจาก commit ถัดไปไม่ได้ลบออกจากประวัติ |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 2)

1. เลือกโดเมนข้อมูลของโครงการ (ใช้ PM2.5 ได้) และหาแหล่งข้อมูลที่ดึงด้วยโค้ดได้
2. อ่าน Pro Git บทที่ 2 (Git Basics)
3. คิดคำถามที่อยากรู้เกี่ยวกับโดเมนนั้น 3 ข้อ แล้วจดไว้ จะใช้ในสัปดาห์ที่ 2
