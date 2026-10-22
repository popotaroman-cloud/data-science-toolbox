---
title: "ปฏิบัติการสัปดาห์ที่ 7: วิเคราะห์ข้อมูลสูญหายและสร้างชุดข้อมูลสะอาด"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO3
> **ผลงานที่ต้องส่ง:** PR ที่มี `notebooks/07_missing.ipynb`, `src/clean.py` และ `data_dictionary.md` ซึ่งเพื่อน review และ merge แล้ว โดย `python src/clean.py` สร้างตาราง `measurements_clean` และ view `daily_pm25_clean` ใน `data/pm25.duckdb`

## สิ่งที่ต้องเตรียม

- งานสัปดาห์ที่ 6 ถูก merge แล้ว: `python src/validate.py` รันผ่าน และมี `reports/profiling_notes.md` ที่ระบุ sentinel value และเซนเซอร์ค้างที่พบ
- `data/pm25.duckdb` ที่มี `measurements` อย่างน้อย 2–4 สัปดาห์จากหลายสถานี (ถ้ายังน้อย ใช้ไฟล์ตัวอย่างจากผู้สอนที่ `data/sample/`)
- `questions.md` เลือกคำถาม 1–2 ข้อที่ใช้ค่าเฉลี่ยรายวัน จะใช้ในขั้นที่ 6

---

## ขั้นที่ 1: สร้าง branch และโหลดข้อมูลเป็น full grid

```bash
git switch main
git pull
git switch -c week07-missing
```

สร้าง `notebooks/07_missing.ipynb`

```python
import duckdb
import pandas as pd
import missingno as msno

con = duckdb.connect("data/pm25.duckdb", read_only=True)
m = con.execute("SELECT station_id, ts, pm25, pm10 FROM measurements").df()
con.close()

start = m["ts"].min().floor("D")
end = m["ts"].max().floor("D") + pd.Timedelta(days=1)
hours = pd.date_range(start, end, freq="h", inclusive="left")
full_idx = pd.MultiIndex.from_product([m["station_id"].unique(), hours],
                                      names=["station_id", "ts"])
hourly = m.set_index(["station_id", "ts"]).reindex(full_idx).reset_index()

print(f"แถวจริง {len(m):,} · แถวที่ควรมี {len(hourly):,} · แถวที่หายไปทั้งแถว {len(hourly) - len(m):,}")
print(f"pm25 ว่าง (ก่อนทำ grid) {m['pm25'].isna().mean():.1%} · (หลังทำ grid) {hourly['pm25'].isna().mean():.1%}")
```

ถ้าบรรทัดแรก error เรื่อง duplicate index แปลว่ามี `(station_id, ts)` ซ้ำ ให้กลับไปตรวจ `src/validate.py` จากสัปดาห์ที่ 6

## ขั้นที่ 2: ดูภาพรวมด้วย missingno

```python
wide = hourly.pivot(index="ts", columns="station_id", values="pm25")
msno.bar(wide)
```

เลือก 8–15 สถานีที่เกี่ยวข้องกับคำถามของตนเอง แล้วดู matrix และ heatmap

```python
stations = wide.columns[:10]            # เปลี่ยนเป็นรายชื่อสถานีที่เลือกเอง
msno.matrix(wide[stations])
msno.heatmap(wide[stations])
```

จดลงใน notebook (Markdown cell): ช่องว่างเป็นช่วงสั้นกระจาย หรือช่วงยาว · มีช่วงที่หายพร้อมกันทุกสถานีหรือไม่ · สถานีใดหายพร้อมกันบ่อย

## ขั้นที่ 3: ทดสอบว่าการสูญหายสัมพันธ์กับเวลาและสถานี

```python
hourly["is_na"] = hourly["pm25"].isna()

by_hour = hourly.groupby(hourly["ts"].dt.hour)["is_na"].mean()
by_dow = hourly.groupby(hourly["ts"].dt.dayofweek)["is_na"].mean()
by_station = hourly.groupby("station_id")["is_na"].mean().sort_values(ascending=False)

by_hour.plot(kind="bar", title="สัดส่วนค่าว่างตามชั่วโมงของวัน")
```

```python
by_station.head(10)       # สถานีที่หายมากที่สุด
```

## ขั้นที่ 4: ทดสอบว่าการสูญหายสัมพันธ์กับระดับมลพิษหรือไม่

```python
hourly = hourly.sort_values(["station_id", "ts"], ignore_index=True)
hourly["pm25_prev"] = hourly.groupby("station_id")["pm25"].shift(1)

hourly.groupby("is_na")[["pm10", "pm25_prev"]].median()
```

ทำซ้ำแยกสถานีที่หายมากที่สุด 3 สถานี

```python
for sid in by_station.index[:3]:
    g = hourly[hourly["station_id"] == sid]
    print(sid, g.groupby("is_na")[["pm10", "pm25_prev"]].median().round(1).to_dict())
```

สรุปลงใน notebook ด้วยตารางนี้ (หนึ่งแถวต่อรูปแบบที่พบ)

| รูปแบบที่พบ | หลักฐาน | กลไกที่สงสัย (MCAR / MAR / MNAR) | ความมั่นใจ |
|---|---|---|---|
| | | | |

## ขั้นที่ 5: เขียน `src/clean.py`

ปรับค่าคงที่ด้านบนให้ตรงกับสิ่งที่พบในสัปดาห์ที่ 6 และขั้นที่ 2–4

```python
"""สร้าง measurements_clean และ daily_pm25_clean จาก measurements (สัปดาห์ที่ 7)"""
import duckdb
import numpy as np
import pandas as pd

DB_PATH = "data/pm25.duckdb"
SENTINELS = [-1, 999, 9999]   # จาก profiling_notes.md
STUCK_HOURS = 6               # ค่าเดิมติดกัน >= 6 ชม. ถือว่าเซนเซอร์ค้าง
MAX_GAP = 3                   # เติมเฉพาะช่องว่าง <= 3 ชม.
MIN_HOURS = 18                # วันที่มี >= 18 จาก 24 ชม. ถือว่าครบ

def fill_short_gaps(s: pd.Series, max_gap: int) -> pd.Series:
    is_na = s.isna()
    run_len = is_na.groupby((is_na != is_na.shift()).cumsum()).transform("sum")
    filled = s.interpolate(method="time", limit_area="inside")
    return s.where(~(is_na & (run_len <= max_gap)), filled)

def build_hourly(m: pd.DataFrame) -> pd.DataFrame:
    m = m.assign(has_row=True)
    start = m["ts"].min().floor("D")
    end = m["ts"].max().floor("D") + pd.Timedelta(days=1)
    hours = pd.date_range(start, end, freq="h", inclusive="left")
    idx = pd.MultiIndex.from_product([m["station_id"].unique(), hours], names=["station_id", "ts"])
    h = m.set_index(["station_id", "ts"]).reindex(idx).reset_index()
    h = h.sort_values(["station_id", "ts"], ignore_index=True)

    # สถานะของแต่ละชั่วโมง
    h["status"] = np.select([h["has_row"].isna(), h["pm25"].isna()], ["no_row", "null"], default="ok")
    h.loc[h["pm25"].isin(SENTINELS) | (h["pm25"] < 0), "status"] = "sentinel"
    new_run = h["pm25"] != h.groupby("station_id")["pm25"].shift()
    run_len = h.groupby(new_run.cumsum())["pm25"].transform("size")
    h.loc[(h["status"] == "ok") & (run_len >= STUCK_HOURS), "status"] = "stuck"

    # เก็บค่าดิบไว้ ใช้เฉพาะค่าที่ status = ok
    h["pm25_raw"] = h["pm25"]
    h["pm25"] = h["pm25"].where(h["status"] == "ok")

    parts = []
    for _, g in h.groupby("station_id"):
        g = g.copy()
        g["pm25_filled"] = fill_short_gaps(g.set_index("ts")["pm25"], MAX_GAP).to_numpy()
        parts.append(g)
    h = pd.concat(parts, ignore_index=True)
    h["is_filled"] = h["pm25"].isna() & h["pm25_filled"].notna()
    return h[["station_id", "ts", "pm25_raw", "pm25", "pm25_filled", "status", "is_filled"]]

def main() -> None:
    con = duckdb.connect(DB_PATH)
    m = con.execute("SELECT station_id, ts, pm25 FROM measurements").df()
    hourly = build_hourly(m)
    con.register("hourly_df", hourly)
    con.execute("CREATE OR REPLACE TABLE measurements_clean AS SELECT * FROM hourly_df")
    con.execute(f"""
        CREATE OR REPLACE VIEW daily_pm25_clean AS
        SELECT station_id,
               CAST(ts AS DATE)            AS date,
               avg(pm25_filled)            AS pm25_mean,
               max(pm25_filled)            AS pm25_max,
               count(pm25_filled)          AS n_hours,
               count(pm25)                 AS n_hours_observed,
               count(pm25_filled) >= {MIN_HOURS} AS is_complete
        FROM measurements_clean
        GROUP BY station_id, CAST(ts AS DATE)
    """)
    print(hourly["status"].value_counts().to_string())
    print(f"เติมค่า {hourly['is_filled'].sum():,} ชั่วโมง")
    con.close()

if __name__ == "__main__":
    main()
```

ปิด notebook ที่เปิดฐานข้อมูลอยู่ก่อน แล้วรันจาก root ของ repo

```bash
python src/clean.py
```

## ขั้นที่ 6: ตรวจผลและทำ sensitivity analysis

กลับไปที่ notebook (เปิด connection ใหม่)

```python
con = duckdb.connect("data/pm25.duckdb", read_only=True)
d = con.execute("SELECT * FROM daily_pm25_clean").df()

assert not d.duplicated(["station_id", "date"]).any()
assert d["n_hours"].between(0, 24).all()
print(d["is_complete"].mean())         # สัดส่วนวันที่ครบตามเกณฑ์
```

ผลของเกณฑ์ความครบต่อคำตอบ (จำนวนวันที่ค่าเฉลี่ยเกิน 37.5 µg/m³)

```python
rows = []
for k in [1, 12, 18, 24]:
    sub = d[d["n_hours"] >= k]
    rows.append({"n_hours >=": k, "วันที่ใช้ได้": len(sub),
                 "วันเกิน 37.5": int((sub["pm25_mean"] > 37.5).sum()),
                 "วันเกิน WHO 15": int((sub["pm25_mean"] > 15).sum())})
pd.DataFrame(rows)
```

เปรียบเทียบกับ view `daily_pm25` เดิมจากสัปดาห์ที่ 5 สำหรับคำถามที่เลือกจาก `questions.md` แล้วเขียน 3–5 ประโยคว่าคำตอบเปลี่ยนไปอย่างไร และตัดสินใจเลือกเกณฑ์ใด

## ขั้นที่ 7: เขียน `data_dictionary.md`

สร้างที่ root ของ repo อย่างน้อยต้องมี

1. ตาราง `stations`, `measurements`, `measurements_clean` และ view `daily_pm25`, `daily_pm25_clean` ระบุที่มา script ที่สร้าง และ "1 แถว = อะไร"
2. ทุกคอลัมน์: ชนิด หน่วย ความหมาย และค่าที่เป็นไปได้ (เช่น `status`: `ok`, `null`, `no_row`, `sentinel`, `stuck`)
3. **บันทึกการตัดสินใจ** ทุกข้อ: ค่าคงที่ใน `src/clean.py` แต่ละตัว เหตุผลและหลักฐาน (อ้างอิง notebook) และผลที่อาจทำให้คำตอบเอนเอียง
4. ข้อจำกัดที่ทราบ เช่น "ถ้าการสูญหายเป็น MNAR จำนวนวันเกินมาตรฐานน่าจะต่ำกว่าความจริง"

ใช้รูปแบบตามตัวอย่างในเอกสารประกอบการสอนหัวข้อที่ 6

## ขั้นที่ 8: commit, push และเปิด pull request

```bash
git status                     # ต้องไม่เห็น data/ หรือไฟล์ .duckdb
git add notebooks/07_missing.ipynb src/clean.py data_dictionary.md
git commit -m "เพิ่มการวิเคราะห์ข้อมูลสูญหายและสร้าง daily_pm25_clean ด้วยเกณฑ์ n_hours >= 18"
git push -u origin week07-missing
```

ในคำอธิบาย PR ใส่ตาราง sensitivity analysis จากขั้นที่ 6 และสรุปกลไกที่สงสัยในประโยคเดียว บันทึกการใช้ AI ใน `AI_USAGE.md`

## ขั้นที่ 9: review PR ของเพื่อน

- [ ] รัน `python src/clean.py` บนเครื่องตนเองได้ และได้ view `daily_pm25_clean`
- [ ] ตาราง `measurements` ต้นฉบับไม่ถูกแก้ไข ค่าดิบยังอยู่ใน `pm25_raw`
- [ ] ข้อสรุปเรื่อง MCAR / MAR / MNAR มีหลักฐานจาก notebook รองรับ ไม่ใช่เดา
- [ ] ค่าคงที่ทุกตัวใน `clean.py` มีเหตุผลใน `data_dictionary.md`
- [ ] มีการพูดถึงผลที่อาจเอนเอียงต่อคำถามใน `questions.md`

เขียนความคิดเห็นอย่างน้อย 1 ข้อ เช่น เสนอหลักฐานเพิ่มเติมที่ควรตรวจ หรือชี้การตัดสินใจที่ยังไม่ได้บันทึก

---

## Checklist ก่อนส่งงาน

- [ ] notebook แสดงจำนวนแถวที่หายไปทั้งแถว (implicit missing) ไม่ใช่แค่ `isna()`
- [ ] มีภาพ missingno อย่างน้อย 2 แบบ พร้อมการตีความ
- [ ] มีตารางหลักฐานและกลไกที่สงสัย
- [ ] `python src/clean.py` รันซ้ำได้โดยไม่ error (ใช้ `CREATE OR REPLACE`)
- [ ] มีตาราง sensitivity analysis และเหตุผลที่เลือกเกณฑ์ `n_hours`
- [ ] `data_dictionary.md` ครอบคลุมทุกตาราง/view และทุกการตัดสินใจ
- [ ] PR ถูก review และ merge แล้ว และได้ review PR ของเพื่อน 1 รายการ

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `ValueError: cannot reindex on an axis with duplicate labels` | มี `(station_id, ts)` ซ้ำ แก้ที่ `src/load_duckdb.py` แล้วตรวจด้วย `src/validate.py` |
| `IO Error: Could not set lock on file` ตอนรัน `clean.py` | notebook หรือ DBeaver เปิด `pm25.duckdb` ค้างไว้ ปิด connection (`con.close()`) หรือ restart kernel |
| `interpolate(method="time")` error | Series ต้องมี `DatetimeIndex` ใช้ `g.set_index("ts")["pm25"]` ตามโค้ด |
| ภาพ `msno.matrix` อ่านไม่ออก | สถานีหรือชั่วโมงมากเกินไป เลือกสถานีน้อยลง หรือดูทีละเดือน `wide.loc["2026-03"]` |
| `msno.heatmap` ว่างหรือ error | สถานีที่ไม่มีค่าว่างเลยหรือว่างทั้งหมดจะถูกตัดออก เลือกสถานีที่มีค่าว่างบางส่วน |
| `n_hours` ใน `daily_pm25` เดิมไม่เท่ากับของใหม่ | เดิมนับแถว ส่วนใหม่นับค่าที่ไม่ว่างรวมค่าที่เติม ระบุความต่างนี้ใน `data_dictionary.md` |
| วันแรก/วันสุดท้ายไม่ครบทุกสถานี | ปกติ เพราะดึงข้อมูลไม่ครบวัน ระบุใน "ข้อจำกัดที่ทราบ" |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 8)

1. อ่านเอกสารประกอบการสอนสัปดาห์ที่ 8 (Checkpoint 1) โดยเฉพาะเกณฑ์การให้คะแนน
2. ลบโฟลเดอร์ `data/` บนเครื่องตนเอง (หรือ clone repo ใหม่ในโฟลเดอร์อื่น) แล้วลองรัน pipeline ตั้งแต่ต้นตาม README ของตนเอง จดทุกขั้นที่ติด
3. ปรับ `README.md` ของโครงการให้มีขั้นตอนรัน pipeline ครบทุก script ตามลำดับ
