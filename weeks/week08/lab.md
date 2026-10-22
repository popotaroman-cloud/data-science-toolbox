---
title: "ปฏิบัติการสัปดาห์ที่ 8: เตรียมและซ้อมนำเสนอ Checkpoint 1"
---

> **เวลา:** 2 ชั่วโมง (คาบซ้อมและ fresh clone test) + 10 นาทีต่อคนในวันนำเสนอ · **CLO:** CLO1–CLO3
> **ผลงานที่ต้องส่ง:** tag `checkpoint1` บน GitHub · แบบบันทึก fresh clone test ที่เพื่อนกรอกแล้ว · แบบ peer review สำหรับเพื่อน 2 คน

## สิ่งที่ต้องเตรียม

- งานสัปดาห์ที่ 3–7 ถูก merge เข้า `main` แล้ว: `fetch_air4thai.py`, `load_duckdb.py`, `schema.py`, `validate.py`, `clean.py`, `data_dictionary.md`, `reports/profiling_notes.md`
- ไฟล์ JSON ดิบสำรองอย่างน้อย 1 ชุด (ที่ดึงไว้เองหรือไฟล์ตัวอย่างจากผู้สอนที่ `data/sample/`) เก็บไว้นอก repo หรือใน `data/` ซึ่งไม่ถูก commit
- จับคู่กับเพื่อน 1 คนสำหรับ fresh clone test (ผู้สอนอาจกำหนดคู่ให้) คู่ควรใช้ระบบปฏิบัติการต่างกันถ้าเป็นไปได้

---

## ขั้นที่ 1: หยุดเพิ่มฟีเจอร์ และสร้าง branch เตรียมงาน

ตั้งแต่ตอนนี้ถึงวันนำเสนอ **แก้เฉพาะสิ่งที่ทำให้ pipeline ทำงานหรือทำซ้ำได้** ไม่เพิ่มการวิเคราะห์ใหม่

```bash
git switch main
git pull
git switch -c checkpoint1-prep
```

ไล่ดูรายการไฟล์ตามหัวข้อที่ 3 ของเอกสารประกอบการสอน ไฟล์ใดขาดให้จดไว้ในตารางนี้แล้วทำให้ครบก่อนขั้นถัดไป

| ไฟล์ / สิ่งที่ต้องมี | มีแล้ว | ต้องแก้อะไร |
|---|---|---|
| `README.md` หัวข้อติดตั้ง รัน ผลลัพธ์ แผนสำรอง ข้อจำกัด | | |
| `environment.yml` มีทุกแพ็กเกจที่ import จริง | | |
| `src/run_pipeline.py` | | |
| `data_dictionary.md` ตรงกับตารางจริงใน DuckDB | | |
| `AI_USAGE.md` บันทึกถึงสัปดาห์ที่ 7 | | |

## ขั้นที่ 2: รัน pipeline จากศูนย์บนเครื่องตนเอง

สร้าง `src/run_pipeline.py` ตามเอกสารประกอบการสอนหัวข้อที่ 2 (ถ้ายังไม่มี) แล้วลบข้อมูลทั้งหมดก่อนรัน

```bash
# ย้ายข้อมูลเดิมไปไว้ที่อื่นก่อน เผื่อต้องใช้ (อย่าลบไฟล์ดิบที่ดึงไว้แล้วถ้าไม่มีสำรอง)
mv data ../data_backup
python src/run_pipeline.py
```

ตรวจผลลัพธ์

```bash
python -c "import duckdb; c=duckdb.connect('data/pm25.duckdb', read_only=True); print(c.sql('SELECT count(*), sum(is_complete::INT) FROM daily_pm25_clean'))"
```

ถ้าขั้นใดล้ม ให้แก้ในโค้ด **ไม่ใช่แก้ด้วยมือบนเครื่อง** สาเหตุที่พบบ่อยคือ script ไม่สร้างโฟลเดอร์ `data/raw/` เอง แก้ได้ด้วย

```python
from pathlib import Path
Path("data/raw").mkdir(parents=True, exist_ok=True)
```

ทดสอบแผนสำรองด้วย: คัดลอกไฟล์ JSON สำรองเข้า `data/raw/` แล้วรันตั้งแต่ `load_duckdb.py` ให้ผ่าน จับเวลาว่าสลับได้ภายใน 1 นาที

## ขั้นที่ 3: ปรับ README และ commit

แก้ README ตามสิ่งที่เจอในขั้นที่ 2 ทุกขั้นที่ทำด้วยมือต้องถูกเขียนเป็นคำสั่งใน README หรือย้ายเข้าไปในโค้ด

```bash
git add README.md src/run_pipeline.py environment.yml
git commit -m "เพิ่ม run_pipeline.py และขั้นตอนรันจากศูนย์ใน README"
git push -u origin checkpoint1-prep
```

เปิด PR แต่ **ยังไม่ merge** จนกว่าจะผ่าน fresh clone test ในขั้นที่ 4

## ขั้นที่ 4: Fresh clone test (ทำโดยเพื่อน)

สลับเครื่องกับคู่ เพื่อนทำตาม README ของเรา **โดยห้ามเจ้าของ repo พูดหรือชี้** เจ้าของทำหน้าที่จดอย่างเดียว ใช้เวลาไม่เกิน 25 นาทีต่อคน

ผู้ทดสอบทำดังนี้

```bash
cd ~/fresh-test                         # โฟลเดอร์ใหม่ที่ไม่มีอะไรอยู่
git clone https://github.com/<เจ้าของ>/pm25-explorer.git
cd pm25-explorer
git switch checkpoint1-prep
# จากนี้ทำตาม README ของเจ้าของเท่านั้น
```

ถ้าเครื่องผู้ทดสอบมีสภาพแวดล้อม `dstoolbox` อยู่แล้ว ให้สร้างใหม่ด้วยชื่ออื่นตาม `environment.yml` ของเจ้าของ เช่น `conda env create -f environment.yml -n fresh-test` เพื่อจับแพ็กเกจที่ขาด

**แบบบันทึก fresh clone test** (ผู้ทดสอบกรอก แล้วโพสต์เป็นความคิดเห็นใน PR ของเจ้าของ)

```markdown
## Fresh clone test
ผู้ทดสอบ: ... · ระบบปฏิบัติการ: ... · วันที่: ...
repo: ... · branch/commit: ...

| ขั้น | ผ่าน/ไม่ผ่าน | ต้องถามหรือแก้อะไร | เวลา (นาที) |
|---|---|---|---|
| clone + สร้าง environment | | | |
| fetch_air4thai.py (หรือแผนสำรอง) | | | |
| load_duckdb.py | | | |
| validate.py | | | |
| clean.py | | | |
| ได้ daily_pm25_clean จำนวนแถวใกล้เคียงที่ README ระบุ | | | |

จุดที่ README ไม่ชัด: ...
ข้อเสนอแนะ 1 ข้อ: ...
```

เจ้าของ repo แก้ทุกจุดที่ "ต้องถามหรือแก้" ใน commit ใหม่บน branch เดิม แล้วขอให้เพื่อนทดสอบซ้ำเฉพาะขั้นที่ไม่ผ่าน

## ขั้นที่ 5: เตรียมบทนำเสนอ 7 นาที

เขียนโครงบทพูดลงในตารางนี้ (ไม่ต้อง commit) ให้ตรงกับเกณฑ์การให้คะแนน

| นาที | หัวข้อ | สิ่งที่จะเปิดให้ดู | ประโยคสำคัญที่ต้องพูด |
|---|---|---|---|
| 0–1 | คำถามและแหล่งข้อมูล | `questions.md` | |
| 1–3 | Live demo | terminal: `python src/run_pipeline.py` | |
| 3–5 | คุณภาพข้อมูล | `src/schema.py`, `profiling_notes.md` | |
| 5–7 | ข้อมูลสูญหาย | ภาพ missingno, ตาราง sensitivity, `data_dictionary.md` | |

เตรียมล่วงหน้าเพื่อไม่เสียเวลาระหว่าง demo

- เปิดไฟล์ที่จะแสดงไว้เป็น tab ใน VS Code ตามลำดับ
- ขยายตัวอักษรของ terminal และ editor ให้คนหลังห้องอ่านได้
- รัน notebook ไว้ล่วงหน้าให้เห็นภาพแล้ว ไม่ต้องรันสดระหว่างนำเสนอ
- ปิดการแจ้งเตือนและหน้าต่างที่ไม่เกี่ยวข้อง

## ขั้นที่ 6: ซ้อมกับเพื่อนและจับเวลา

ซ้อมกับคู่ (หรือกลุ่ม 3 คน) คนหนึ่งนำเสนอ คนหนึ่งจับเวลา อีกคนถามคำถามจากตาราง "คำถามที่ผู้ประเมินมักถาม" ในเอกสารประกอบการสอน 2 ข้อ

- [ ] demo จบใน 7 นาที (เกิน 30 วินาทีขึ้นไปให้ตัดเนื้อหา ไม่ใช่พูดเร็วขึ้น)
- [ ] live demo เริ่มจากไม่มีฐานข้อมูลจริง
- [ ] อธิบายได้ว่าทำไมแบ่งกฎ fail / warn แบบนี้
- [ ] บอกได้ว่าเกณฑ์ `n_hours` ที่เลือกทำให้คำตอบเอนเอียงไปทางใด
- [ ] ตอบคำถามเรื่องโค้ดส่วนที่ใช้ AI ช่วยได้

## ขั้นที่ 7: merge และสร้าง tag `checkpoint1`

เมื่อผ่าน fresh clone test และเพื่อน approve PR แล้ว

```bash
git switch main
git pull                              # หลัง merge PR บน GitHub
git tag -a checkpoint1 -m "Checkpoint 1: data pipeline"
git push origin checkpoint1
```

ตรวจบน GitHub ว่ามี tag ในหน้า **Tags** แล้วส่งลิงก์ `https://github.com/<username>/pm25-explorer/tree/checkpoint1` ในระบบส่งงาน

> ถ้าต้องแก้หลังสร้าง tag แล้วและยังไม่ถึงกำหนดส่ง ให้ลบ tag เดิม (`git tag -d checkpoint1` และ `git push origin --delete checkpoint1`) แล้วสร้างใหม่ หลังกำหนดส่งห้ามย้าย tag

## ขั้นที่ 8: Peer review ในวันนำเสนอ

แต่ละคนได้รับมอบหมายให้ประเมินเพื่อน 2 คน กรอกแบบฟอร์มนี้ระหว่างฟังและส่งภายในวันนำเสนอ

| # | คำถาม | คำตอบ |
|---|---|---|
| 1 | pipeline รันครบทุกขั้นต่อหน้าผู้ฟังหรือไม่ ถ้าไม่ ติดที่ขั้นใด | ครบ / ไม่ครบ: ... |
| 2 | ผู้นำเสนอเริ่ม demo จากไม่มีฐานข้อมูลหรือไม่ | ใช่ / ไม่ใช่ |
| 3 | ปัญหาคุณภาพข้อมูลที่น่าสนใจที่สุดที่ผู้นำเสนอพบคืออะไร | |
| 4 | เหตุผลของการแบ่ง fail / warn ฟังขึ้นหรือไม่ เพราะอะไร | 1–5: ... |
| 5 | ผู้นำเสนอมีหลักฐานสนับสนุนกลไกการสูญหายที่สรุปหรือไม่ | 1–5: ... |
| 6 | ผู้นำเสนอบอกได้ไหมว่าการตัดสินใจเรื่องข้อมูลสูญหายกระทบคำตอบของคำถามอย่างไร | 1–5: ... |
| 7 | ถ้าคุณต้องใช้ข้อมูลจาก pipeline นี้ คุณกังวลเรื่องใดมากที่สุด | |
| 8 | สิ่งหนึ่งที่คุณจะนำไปใช้กับโครงการของตนเอง | |
| 9 | ข้อเสนอแนะ 1 ข้อที่ทำได้จริงภายในสัปดาห์ที่ 9 | |

ความเห็นต้องเจาะจงและสุภาพ เช่น "เกณฑ์ stuck sensor 6 ชั่วโมงอาจตัดช่วงกลางคืนที่อากาศนิ่งจริง ลองเทียบกับสถานีใกล้เคียง" ดีกว่า "ดีมาก" หรือ "ควรปรับปรุง"

---

## Checklist ก่อนส่งงาน

- [ ] `python src/run_pipeline.py` ผ่านจากสถานะไม่มีโฟลเดอร์ `data/`
- [ ] แผนสำรอง (ไฟล์ JSON ดิบ) ทดสอบแล้วและเขียนไว้ใน README
- [ ] เพื่อนทำ fresh clone test ผ่าน และแบบบันทึกอยู่ในความคิดเห็นของ PR
- [ ] `data_dictionary.md` และ `AI_USAGE.md` เป็นปัจจุบัน
- [ ] ไม่มี `data/`, `*.duckdb`, `reports/*.html` หรือ `.env` ใน repo (`git ls-files` ตรวจได้)
- [ ] tag `checkpoint1` อยู่บน GitHub และส่งลิงก์แล้ว
- [ ] ซ้อมจับเวลาแล้วอย่างน้อย 1 รอบ
- [ ] ส่งแบบ peer review ครบ 2 คน

## แก้ปัญหาที่พบบ่อย (ก่อนวันนำเสนอ)

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `FileNotFoundError: data/raw/...` บนเครื่องเพื่อน | `data/` ไม่ถูก commit โฟลเดอร์จึงไม่มี ให้ script สร้างเองด้วย `Path(...).mkdir(parents=True, exist_ok=True)` |
| `ModuleNotFoundError` บนเครื่องเพื่อนแต่เครื่องตนเองรันได้ | ติดตั้งแพ็กเกจเพิ่มด้วย `pip install` โดยไม่ได้ใส่ใน `environment.yml` เพิ่มแล้วทดสอบด้วย environment ใหม่ |
| path แบบ `C:\Users\...` หรือ `/home/...` ในโค้ด | ใช้ path สัมพัทธ์จาก root ของ repo เช่น `data/pm25.duckdb` และระบุใน README ว่าต้องรันจาก root |
| รันได้เฉพาะเมื่อรัน notebook ก่อน | มีขั้นตอนสำคัญซ่อนอยู่ใน notebook ย้ายเข้า `src/` และเรียกจาก `run_pipeline.py` |
| `load_duckdb.py` รันซ้ำแล้วข้อมูลซ้ำ จน `validate.py` fail | ใช้ `CREATE OR REPLACE` หรือ `INSERT ... ON CONFLICT` / ลบช่วงเวลาเดิมก่อนแทรก ให้การโหลดเป็น idempotent |
| `IO Error: Could not set lock on file` ระหว่าง demo | notebook ที่เปิดไว้ถือ connection อยู่ ปิด kernel ก่อนเริ่ม demo หรือเปิดฐานข้อมูลใน notebook ด้วย `read_only=True` |
| Air4Thai ตอบช้าหรือ error ในห้องเรียน | Wi-Fi ห้องเรียนอาจช้า สลับไปใช้แผนสำรองทันที อย่ารอ timeout ซ้ำหลายรอบ |
| ข้อความภาษาไทยใน terminal เป็นตัวอักษรแปลก (Windows) | ตั้ง `set PYTHONUTF8=1` (cmd) หรือ `$env:PYTHONUTF8=1` (PowerShell) ก่อนรัน หรือใช้ terminal ของ VS Code |
| demo เกินเวลา | ตัดหัวข้อที่ไม่อยู่ในเกณฑ์การให้คะแนน และให้ pipeline รันระหว่างที่พูดอธิบาย |
| ลืม push tag | `git push` ไม่ส่ง tag ไปด้วย ต้องใช้ `git push origin checkpoint1` |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 9)

1. นำข้อเสนอแนะจากผู้สอนและ peer review เปิดเป็น GitHub Issue อย่างน้อย 2 รายการ และวางแผนแก้ภายในสัปดาห์ที่ 9
2. อ่านเรื่อง grammar of graphics: Wickham, H. (2010). A layered grammar of graphics. *Journal of Computational and Graphical Statistics*, 19(1)
3. ร่างกราฟ 2 แบบด้วยมือบนกระดาษ ที่จะตอบคำถามใน `questions.md` จาก `daily_pm25_clean` เช่น การกระจายของค่าเฉลี่ยรายวัน และแนวโน้มตามเวลาของสถานีที่สนใจ
