---
title: "ปฏิบัติการสัปดาห์ที่ 6: profiling และเขียนกฎตรวจคุณภาพข้อมูล PM2.5"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO3
> **ผลงานที่ต้องส่ง:** PR ที่มี `src/schema.py`, `src/validate.py`, `notebooks/06_quality.ipynb` และ `reports/profiling_notes.md` ซึ่งเพื่อน review และ merge แล้ว

## สิ่งที่ต้องเตรียม

- งานจากสัปดาห์ที่ 3–5 ต้องรันได้: `src/fetch_air4thai.py`, `src/load_duckdb.py` และ `data/pm25.duckdb` ที่มีตาราง `stations`, `measurements` และ view `daily_pm25`
- ข้อมูลใน `measurements` ควรมีอย่างน้อยหลายวันจากหลายสถานี ถ้ายังมีไม่พอ ให้ใช้ไฟล์ตัวอย่างจากผู้สอนที่ `data/sample/` แล้วโหลดเข้า DuckDB ด้วย script ของสัปดาห์ที่ 4
- `questions.md` จากสัปดาห์ที่ 2 (จะใช้พิจารณาว่าปัญหาใดกระทบคำถามใด)

ตรวจว่าฐานข้อมูลพร้อม

```bash
python -c "import duckdb; c=duckdb.connect('data/pm25.duckdb', read_only=True); print(c.sql('SELECT count(*), min(ts), max(ts) FROM measurements'))"
```

---

## ขั้นที่ 1: สร้าง branch และโฟลเดอร์ reports

```bash
git switch main
git pull
git switch -c week06-quality
mkdir reports
```

เพิ่มท้าย `.gitignore`

```text
reports/*.html
```

ตรวจว่าไลบรารีพร้อม

```bash
python -c "import ydata_profiling, pandera, skimpy; print('พร้อมใช้งาน')"
```

## ขั้นที่ 2: โหลดข้อมูลและดูภาพรวม

สร้าง `notebooks/06_quality.ipynb` แล้วรันจาก root ของ repo (ถ้า notebook เปิดในโฟลเดอร์ `notebooks/` ให้ใช้ path `../data/pm25.duckdb`)

```python
import duckdb
import pandas as pd

con = duckdb.connect("data/pm25.duckdb", read_only=True)
m = con.execute("SELECT * FROM measurements ORDER BY station_id, ts").df()
con.close()

print(m.shape)
m.dtypes
```

ดูภาพรวมเร็ว ๆ ด้วย skimpy (เสริม)

```python
from skimpy import skim
skim(m)
```

จดไว้: จำนวนสถานี ช่วงเวลา สัดส่วนค่าว่างของ `pm25` และค่าต่ำสุด/สูงสุด

## ขั้นที่ 3: สร้างรายงาน profiling

```python
from ydata_profiling import ProfileReport

profile = ProfileReport(m, title="Air4Thai measurements", minimal=True)
profile.to_file("reports/profile_measurements.html")
```

เปิดไฟล์ HTML ใน browser แล้วสร้าง `reports/profiling_notes.md` ตามแม่แบบนี้

```markdown
# บันทึกการตีความ profiling: measurements

ข้อมูล ณ วันที่: YYYY-MM-DD · จำนวนแถว: ... · จำนวนสถานี: ... · ช่วงเวลา: ... ถึง ...

| มิติ | สิ่งที่พบ | ตรวจต่ออย่างไร | การตัดสินใจ | กระทบคำถามข้อใดใน questions.md |
|---|---|---|---|---|
| Completeness | | | | |
| Validity | | | | |
| Consistency | | | | |
| Uniqueness | | | | |
| Timeliness | | | | |
| Accuracy | | | | |

## Alerts จากรายงานที่เลือกไม่สนใจ และเหตุผล
```

> อย่าคัดลอก alert มาวางเฉย ๆ ทุกแถวต้องมีคอลัมน์ "ตรวจต่ออย่างไร" ที่ทำจริงใน notebook

## ขั้นที่ 4: ตรวจปัญหาเฉพาะของ Air4Thai

รันทีละ cell และบันทึกผลลงใน `profiling_notes.md`

**4.1 Sentinel value**

```python
m["pm25"].value_counts().head(10)
m.loc[(m["pm25"] < 0) | (m["pm25"] >= 999), ["station_id", "ts", "pm25"]]
```

ถ้าพบ ให้กลับไปแก้ `src/load_duckdb.py` ให้แปลงเป็น NULL แล้วโหลดใหม่ (แก้ใน commit แยก)

**4.2 เซนเซอร์ค้าง**

```python
m["roll_std"] = m.groupby("station_id")["pm25"].transform(lambda s: s.rolling(6).std())
stuck = m[m["roll_std"] == 0]
stuck.groupby("station_id").size().sort_values(ascending=False).head()
```

เลือกสถานีที่ค้างมากที่สุด แล้ว plot ดูด้วยตาเพื่อยืนยัน

```python
sid = stuck["station_id"].value_counts().index[0]
m[m["station_id"] == sid].set_index("ts")["pm25"].plot(figsize=(10, 3), title=sid)
```

**4.3 Timezone และข้อมูลจากอนาคต**

```python
print(m.groupby(m["ts"].dt.hour)["pm25"].mean().round(1))
now_bkk = pd.Timestamp.now(tz="Asia/Bangkok").tz_localize(None)
print("ข้อมูลจากอนาคต:", (m["ts"] > now_bkk).sum(), "แถว")
print("ข้อมูลล่าสุดเก่าแค่ไหน:", now_bkk - m["ts"].max())
```

**4.4 Key ซ้ำและความสอดคล้อง**

```python
print("key ซ้ำ:", m.duplicated(["station_id", "ts"]).sum())
print("pm25 > pm10:", (m["pm25"] > m["pm10"]).sum(), "แถว")
```

## ขั้นที่ 5: เขียน `src/schema.py`

คัดลอก `src/schema.py` จากเอกสารประกอบการสอนหัวข้อที่ 6 แล้ว **ปรับให้ตรงกับข้อมูลของตนเอง**

1. รายการ `SENTINELS` ใช้ค่าที่พบจริงในขั้นที่ 4.1
2. ขอบบนของสารแต่ละตัว ตรวจหน่วยจากข้อมูลจริงก่อน
3. ถ้าคอลัมน์ใดไม่มีในข้อมูลของตน (บางสถานีไม่วัด SO2) ให้ลบออก หรือคง `nullable=True`

ทดสอบใน notebook

```python
import sys; sys.path.append("src")      # ให้ notebook import จาก src/ ได้
import pandera.pandas as pa
from schema import allowed_station_ids, measurements_schema

schema = measurements_schema(allowed_station_ids())
try:
    schema.validate(m.drop(columns=["roll_std"]), lazy=True)
    print("ผ่านทุกกฎ")
except pa.errors.SchemaErrors as err:
    display(err.failure_cases.head(20))
```

**ทดสอบว่ากฎจับได้จริง** โดยสร้างข้อมูลเสียขึ้นมาเอง

```python
bad = m.drop(columns=["roll_std"]).head(5).copy()
bad.loc[0, "pm25"] = -1                      # sentinel
bad.loc[1, "station_id"] = "XX99"            # สถานีที่ไม่มีจริง
bad = pd.concat([bad, bad.iloc[[2]]])        # key ซ้ำ
try:
    schema.validate(bad, lazy=True)
except pa.errors.SchemaErrors as err:
    display(err.failure_cases[["column", "check", "failure_case"]])
```

ต้องเห็นข้อผิดพลาดครบทั้ง 3 แบบ ถ้าไม่ครบ แสดงว่ากฎยังไม่ทำงานตามที่ตั้งใจ

## ขั้นที่ 6: เขียน `src/validate.py` ที่แยก fail กับ warn

```python
"""ตรวจคุณภาพตาราง measurements: fail = exit 1, warn = พิมพ์เตือนแล้วทำงานต่อ"""
import sys
import duckdb
import pandas as pd
import pandera.pandas as pa
from schema import DB_PATH, allowed_station_ids, measurements_schema

def load() -> pd.DataFrame:
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("SELECT * FROM measurements ORDER BY station_id, ts").df()
    con.close()
    return df

def soft_checks(m: pd.DataFrame) -> list[str]:
    warns = []
    n_high = int((m["pm25"] > 500).sum())
    if n_high:
        warns.append(f"pm25 > 500 จำนวน {n_high} แถว")
    roll_std = m.groupby("station_id")["pm25"].transform(lambda s: s.rolling(6).std())
    n_stuck = int((roll_std == 0).sum())
    if n_stuck:
        warns.append(f"สงสัยเซนเซอร์ค้าง (ค่าเดิม 6 ชม.) {n_stuck} แถว")
    lag = pd.Timestamp.now(tz="Asia/Bangkok").tz_localize(None) - m["ts"].max()
    if lag > pd.Timedelta(days=2):
        warns.append(f"ข้อมูลล่าสุดเก่า {lag}")
    missing = m["pm25"].isna().mean()
    if missing > 0.2:
        warns.append(f"pm25 ว่าง {missing:.0%}")
    return warns

def main() -> None:
    m = load()
    schema = measurements_schema(allowed_station_ids())
    try:
        schema.validate(m, lazy=True)
    except pa.errors.SchemaErrors as err:
        print("FAIL: ข้อมูลไม่ผ่านกฎ")
        print(err.failure_cases[["column", "check", "failure_case"]].head(30))
        sys.exit(1)
    for w in soft_checks(m):
        print("WARN:", w)
    print(f"OK: ตรวจ {len(m):,} แถว")

if __name__ == "__main__":
    main()
```

รันจาก root ของ repo

```bash
python src/validate.py
echo $?          # 0 = ผ่าน, 1 = fail (PowerShell ใช้ $LASTEXITCODE)
```

เพิ่มตาราง "Fail หรือ Warn" ของตนเองลงใน `profiling_notes.md` พร้อมเหตุผลทุกแถว

## ขั้นที่ 7: commit, push และเปิด pull request

```bash
git status                     # ต้องไม่เห็นไฟล์ .html หรือ data/
git add .gitignore src/schema.py src/validate.py notebooks/06_quality.ipynb reports/profiling_notes.md
git commit -m "เพิ่มกฎตรวจคุณภาพ measurements ด้วย pandera และบันทึกผล profiling"
git push -u origin week06-quality
```

เปิด PR ใส่ผลลัพธ์ของ `python src/validate.py` ไว้ในคำอธิบาย แล้วขอ review จากเพื่อน 1 คน อย่าลืมบันทึกใน `AI_USAGE.md` ถ้าใช้ AI ช่วยเขียนกฎ

## ขั้นที่ 8: review PR ของเพื่อน

- [ ] รัน `python src/validate.py` บนเครื่องตนเองได้ (ใช้ฐานข้อมูลของตนเอง)
- [ ] schema มีกฎครบ: ชนิดข้อมูล ช่วงค่า `pm25`, sentinel, `station_id` ที่อนุญาต และ key ไม่ซ้ำ
- [ ] ขอบเขตค่าที่ใช้มีเหตุผลอธิบายไว้ ไม่ใช่ตัวเลขลอย ๆ
- [ ] `profiling_notes.md` มีการตีความ ไม่ใช่คัดลอก alert มาวาง
- [ ] การแบ่ง fail / warn สมเหตุสมผล
- [ ] ไม่มีไฟล์ `.html` หรือ `data/` ใน PR

เขียนความคิดเห็นอย่างน้อย 1 ข้อที่ชี้ปัญหาคุณภาพที่เพื่อนอาจยังไม่ได้ตรวจ

---

## Checklist ก่อนส่งงาน

- [ ] `reports/profile_measurements.html` สร้างได้ แต่ไม่ถูก commit
- [ ] `reports/profiling_notes.md` ครบ 6 มิติ และโยงกับ `questions.md`
- [ ] `src/schema.py` ทดสอบกับข้อมูลเสียที่สร้างเองแล้ว จับได้ครบ
- [ ] `python src/validate.py` จบด้วย exit code 0 กับข้อมูลจริง หรือมีคำอธิบายใน PR ว่าทำไมยัง fail
- [ ] PR ถูก review และ merge แล้ว และได้ review PR ของเพื่อน 1 รายการ

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `ModuleNotFoundError: pandera.pandas` | pandera รุ่นเก่า ให้อัปเดต (`conda update pandera`) หรือเปลี่ยนเป็น `import pandera as pa` |
| `ModuleNotFoundError: schema` | รัน script จาก root ของ repo ด้วย `python src/validate.py` และใน notebook ต้อง `sys.path.append("src")` |
| ProfileReport ช้ามากหรือหน่วยความจำเต็ม | ใช้ `minimal=True` หรือสุ่มตัวอย่าง `m.sample(50_000, random_state=0)` แล้วระบุในบันทึกว่าใช้ตัวอย่าง |
| `ts` ไม่ผ่านกฎชนิดข้อมูล | DuckDB อาจคืนค่าเป็นความละเอียดอื่น (เช่น `datetime64[us]`) `coerce=True` ควรแปลงให้ ถ้ายังไม่ผ่าน ให้ดู `m.dtypes` แล้วปรับ schema |
| `IO Error: Could not set lock on file` | มีโปรแกรมอื่นเปิด `pm25.duckdb` แบบเขียนอยู่ ปิด notebook อื่น หรือเปิดด้วย `read_only=True` |
| `import sweetviz` error เรื่อง numpy | Sweetviz เป็นเครื่องมือเสริมและอาจไม่เข้ากับ numpy รุ่นใหม่ ข้ามไปใช้ ydata-profiling ได้ |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 7)

1. อ่านเรื่อง MCAR / MAR / MNAR จาก *Flexible Imputation of Missing Data* (van Buuren) บทที่ 1.2 — <https://stefvanbuuren.name/fimd/>
2. คำนวณสัดส่วนค่าว่างของ `pm25` แยกตามสถานีและตามเดือน แล้วจดว่าสถานีใดมีปัญหามากที่สุด
3. คิดล่วงหน้า: ถ้าเซนเซอร์มักเสียช่วงที่ฝุ่นหนาที่สุด ค่าเฉลี่ยรายเดือนที่คำนวณได้จะสูงหรือต่ำกว่าความจริง
