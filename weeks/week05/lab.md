---
title: "ปฏิบัติการสัปดาห์ที่ 5: สร้าง daily_pm25 และ tidy dataframe"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO2
> **ผลงานที่ต้องส่ง:** PR ที่ merge แล้ว ประกอบด้วย `src/load_duckdb.py` ที่สร้าง view `daily_pm25` และ `notebooks/05_wrangling.ipynb` ที่ได้ tidy dataframe รายวัน

## สิ่งที่ต้องเตรียม

- `data/pm25.duckdb` จากสัปดาห์ที่ 4 ที่มี `stations` (ทุกสถานีมี `region`) และ `measurements` ซึ่งรวมข้อมูลย้อนหลังจากไฟล์ตัวอย่างจากผู้สอนแล้ว (`python src/load_duckdb.py --sample`)
- `questions.md` ที่ระบุช่วงสำรวจ 2563–2566 และช่วงทดสอบ 2567–2568
- ตรวจ: `python -c "import pandas, polars, duckdb; print(pandas.__version__, polars.__version__, duckdb.__version__)"`

> **เวอร์ชัน DuckDB:** ไฟล์ `.duckdb` ที่สร้างด้วย DuckDB เวอร์ชันใหม่อาจเปิดด้วยเวอร์ชันเก่าไม่ได้ ใช้สภาพแวดล้อม `dstoolbox` เดียวกันทั้ง script และ notebook

---

## ขั้นที่ 1: สร้าง branch

```bash
git switch main
git pull
git switch -c week05-wrangling
```

## ขั้นที่ 2: เพิ่ม view `daily_pm25` ใน `src/load_duckdb.py`

เพิ่มค่าคงที่นี้ต่อจาก `SCHEMA`

```python
VIEWS = """
CREATE OR REPLACE VIEW daily_pm25 AS
SELECT station_id,
       CAST(ts AS DATE) AS date,        -- ts เป็นเวลาไทย จึงตัดวันตามเวลาไทย
       AVG(pm25)        AS pm25_mean,
       MAX(pm25)        AS pm25_max,
       COUNT(pm25)      AS n_hours
FROM measurements
GROUP BY station_id, CAST(ts AS DATE);
"""
```

แล้วใน `main()` เพิ่มบรรทัดนี้ก่อนส่วน "สรุปและตรวจสอบ"

```python
    con.execute(VIEWS)
    print(con.sql("SELECT COUNT(*) AS n_days, AVG(n_hours) AS avg_hours FROM daily_pm25").df())
```

รันและตรวจ

```bash
python src/load_duckdb.py
```

view ถูกสร้างใหม่ทุกครั้งที่รัน (`CREATE OR REPLACE`) จึงยัง idempotent และไม่ต้องแก้อะไรเมื่อมีข้อมูลใหม่

## ขั้นที่ 3: ดึงข้อมูลเข้า pandas (เฉพาะช่วงสำรวจ)

สร้าง `notebooks/05_wrangling.ipynb`

```python
import duckdb
import pandas as pd

con = duckdb.connect("../data/pm25.duckdb", read_only=True)
EXPLORE_END = "2024-01-01"        # ช่วงสำรวจ 2563–2566 ตาม questions.md

h = con.execute("""
    SELECT m.station_id, m.ts, m.pm25, m.pm10, s.region
    FROM measurements m JOIN stations s USING (station_id)
    WHERE m.ts < CAST(? AS TIMESTAMP)
""", [EXPLORE_END]).df()
print(h.shape)
h.dtypes
```

ตอบใน Markdown cell: `ts` มีชนิดอะไร มี timezone กำกับหรือไม่ และหนึ่งแถวคืออะไร

## ขั้นที่ 4: เปรียบเทียบค่ารายวันจาก SQL กับ pandas

```python
# จาก view
d_sql = con.execute("SELECT * FROM daily_pm25 WHERE date < CAST(? AS DATE)", [EXPLORE_END]).df()

# จาก pandas resample
d_pd = (
    h.set_index("ts")
     .groupby("station_id")["pm25"]
     .resample("D")
     .agg(["mean", "max", "count"])
     .rename(columns={"mean": "pm25_mean", "max": "pm25_max", "count": "n_hours"})
     .reset_index()
     .rename(columns={"ts": "date"})
)
print(len(d_sql), len(d_pd))
```

```python
# ตรวจว่าค่าตรงกันในวันที่มีทั้งสองแบบ
d_sql["date"] = pd.to_datetime(d_sql["date"])
cmp = d_sql.merge(d_pd, on=["station_id", "date"], suffixes=("_sql", "_pd"))
print((cmp["n_hours_sql"] != cmp["n_hours_pd"]).sum(), "แถวที่ n_hours ไม่ตรงกัน")
print("วันที่มีใน pandas แต่ไม่มีใน SQL:", (d_pd["n_hours"] == 0).sum())
```

อธิบายใน Markdown cell ว่าทำไมจำนวนแถวไม่เท่ากัน (ดูเอกสารประกอบการสอนหัวข้อที่ 5) และค่าตรงกันหรือไม่

## ขั้นที่ 5: ดูการกระจายของ `n_hours` และกำหนดเกณฑ์

```python
d_sql["n_hours"].value_counts().sort_index()
```

```python
# สัดส่วนวันที่ครบตามเกณฑ์ ต่อภาค
d_sql.merge(con.sql("SELECT station_id, region FROM stations").df(), on="station_id") \
     .assign(complete=lambda d: d["n_hours"] >= 18) \
     .groupby("region")["complete"].mean().round(3)
```

ตัดสินใจเกณฑ์ความครบถ้วน (ค่าเริ่มต้น `>= 18`) แล้วเขียนเหตุผลใน `questions.md` ใต้ Q1 เช่น

```markdown
- **เกณฑ์ความครบถ้วนรายวัน:** n_hours >= 18 (75%) ตัดสินใจเมื่อ <วันที่> ก่อนดูผลจำนวนวันเกินมาตรฐาน
  วันที่ไม่ครบตามเกณฑ์จะไม่นับ และรายงานจำนวนที่ตัดออกแยกตามภาค
```

> กำหนดเกณฑ์ **ก่อน** คำนวณจำนวนวันเกินมาตรฐาน ถ้าเปลี่ยนเกณฑ์ภายหลัง ต้องบันทึกเหตุผลและ commit แยก

## ขั้นที่ 6: สร้าง tidy dataframe รายวัน

```python
daily = con.execute("""
    SELECT d.station_id, s.province, s.region, d.date,
           d.pm25_mean, d.pm25_max, d.n_hours,
           d.n_hours >= 18                         AS complete,
           d.n_hours >= 18 AND d.pm25_mean > 37.5  AS exceed_th,
           d.n_hours >= 18 AND d.pm25_mean > 15    AS exceed_who
    FROM daily_pm25 d JOIN stations s USING (station_id)
    WHERE d.date < CAST(? AS DATE)
    ORDER BY d.station_id, d.date
""", [EXPLORE_END]).df()

daily["date"] = pd.to_datetime(daily["date"])
daily["year"] = daily["date"].dt.year
daily["month"] = daily["date"].dt.month
daily.head()
```

ตรวจว่า tidy: หนึ่งแถวคือหนึ่งสถานี-หนึ่งวัน และไม่มีแถวซ้ำ

```python
assert not daily.duplicated(["station_id", "date"]).any()
daily.shape, daily["station_id"].nunique()
```

สรุปเบื้องต้นสำหรับ Q1 (ช่วงสำรวจ) ด้วย `pivot_table`

```python
pd.pivot_table(daily[daily["complete"]], index="region", columns="year",
               values="exceed_th", aggfunc="sum")       # จำนวนสถานี-วันที่เกินมาตรฐานไทย
```

เขียน Markdown cell ตีความด้วยถ้อยคำที่ตรงกับหลักฐาน ("ข้อมูลช่วงสำรวจบ่งชี้ว่า…") และสังเกตว่าตัวเลขนี้เป็น *สถานี-วัน* ภาคที่มีสถานีมากย่อมมีค่ามากกว่า ควรหารด้วยอะไร

## ขั้นที่ 7: แปลงรูป wide ↔ long และเวลาของวัน

```python
# wide → long สำหรับเปรียบเทียบ pm25 กับ pm10
long = h.melt(id_vars=["station_id", "ts", "region"], value_vars=["pm25", "pm10"],
              var_name="pollutant", value_name="value")
long.groupby("pollutant")["value"].describe()
```

```python
# โปรไฟล์รายชั่วโมงของวัน (ตอบคำถามแนว "ชั่วโมงใดสูงสุด")
h["hour"] = h["ts"].dt.hour
h["month"] = h["ts"].dt.month
prof = (h[h["month"].isin([1, 2, 3])]
        .pivot_table(index="hour", columns="region", values="pm25", aggfunc="mean")
        .round(1))
prof
```

```python
# timezone: ตรวจความเข้าใจ
x = h["ts"].head(3).dt.tz_localize("Asia/Bangkok")
pd.DataFrame({"bkk": x, "utc": x.dt.tz_convert("UTC")})
```

## ขั้นที่ 8 (เสริม): ทำค่ารายวันด้วย Polars แล้วเทียบเวลา

```python
import time
import polars as pl

hp = con.sql(f"SELECT station_id, ts, pm25 FROM measurements "
             f"WHERE ts < TIMESTAMP '{EXPLORE_END}'").pl()     # ค่าคงที่ของเราเอง ใช้ f-string ได้

t0 = time.perf_counter()
d_pl = (hp.group_by("station_id", pl.col("ts").dt.date().alias("date"))
          .agg(pl.col("pm25").mean().alias("pm25_mean"),
               pl.col("pm25").max().alias("pm25_max"),
               pl.col("pm25").count().alias("n_hours")))
print("polars", round(time.perf_counter() - t0, 3), "s", d_pl.shape)

t0 = time.perf_counter()
_ = h.groupby(["station_id", h["ts"].dt.date])["pm25"].agg(["mean", "max", "count"])
print("pandas", round(time.perf_counter() - t0, 3), "s")
```

บันทึกผลเทียบเวลาและความรู้สึกในการเขียนโค้ดแต่ละแบบ 2–3 บรรทัด

## ขั้นที่ 9: บันทึกผลสำหรับสัปดาห์ถัดไป

```python
import os
os.makedirs("../data/processed", exist_ok=True)
daily.to_parquet("../data/processed/daily_explore.parquet", index=False)
con.close()
```

สัปดาห์ที่ 6 จะใช้ view `daily_pm25` และไฟล์นี้ทำ profiling และกฎตรวจคุณภาพข้อมูล

## ขั้นที่ 10: commit, push และเปิด pull request

Restart Kernel and Run All ก่อน commit

```bash
git status                       # ต้องไม่เห็นไฟล์ใน data/
git add src/load_duckdb.py notebooks/05_wrangling.ipynb questions.md AI_USAGE.md
git commit -m "เพิ่ม view daily_pm25 พร้อม n_hours และ tidy dataframe รายวัน"
git push -u origin week05-wrangling
```

## ขั้นที่ 11: review PR ของเพื่อน

- [ ] รัน `python src/load_duckdb.py` แล้ว query `SELECT * FROM daily_pm25 LIMIT 5` ได้
- [ ] `daily_pm25` มีคอลัมน์ `station_id, date, pm25_mean, pm25_max, n_hours` ตามที่ตกลง
- [ ] ตัดวันตามเวลาไทย และ notebook อธิบายชนิดและ timezone ของ `ts` ถูกต้อง
- [ ] มีการเปรียบเทียบ SQL กับ pandas และอธิบายได้ว่าทำไมจำนวนแถวต่างกัน
- [ ] เกณฑ์ความครบถ้วนเขียนไว้ใน `questions.md` พร้อมเหตุผล และ commit ก่อนการสรุปผล
- [ ] tidy dataframe ไม่มีแถวซ้ำ `(station_id, date)`
- [ ] ใช้เฉพาะช่วงสำรวจ ไม่มี query ที่ดูข้อมูลปี 2567–2568
- [ ] ถ้อยคำตีความไม่เกินหลักฐาน และไม่มีไฟล์ใน `data/` ใน PR

---

## Checklist ก่อนส่งงาน

- [ ] view `daily_pm25` อยู่ใน `data/pm25.duckdb` และสร้างจาก `src/load_duckdb.py`
- [ ] `notebooks/05_wrangling.ipynb` มี tidy dataframe `daily` พร้อม `complete`, `exceed_th`, `exceed_who`
- [ ] มีตัวอย่าง `melt` และ `pivot_table` อย่างละ 1 ครั้ง
- [ ] `questions.md` มีเกณฑ์ความครบถ้วนรายวัน
- [ ] `data/processed/daily_explore.parquet` อยู่ในเครื่อง (ไม่ commit)
- [ ] PR ถูก review และ merge แล้ว และได้ review PR ของเพื่อน

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `Catalog Error: Table with name daily_pm25 does not exist` | ยังไม่ได้รัน `load_duckdb.py` เวอร์ชันใหม่ หรือ notebook เปิดไฟล์ก่อนสร้าง view ให้ restart kernel |
| `IOException: Could not set lock on file` | notebook เปิด connection แบบเขียนค้างไว้ ใช้ `read_only=True` ใน notebook และ `con.close()` ก่อนรัน script |
| `merge` แล้วไม่มีแถวตรงกัน | `date` ฝั่งหนึ่งเป็น `datetime64` อีกฝั่งเป็น `object` (Python `date`) แปลงด้วย `pd.to_datetime` ทั้งสองฝั่ง |
| `TypeError: Already tz-aware` | เรียก `tz_localize` กับคอลัมน์ที่มี timezone แล้ว ใช้ `tz_convert` แทน |
| `ValueError: Index contains duplicate entries, cannot reshape` | `pivot` เจอ key ซ้ำ ใช้ `pivot_table(..., aggfunc=...)` หรือตรวจแถวซ้ำ |
| `resample` ช้าหรือใช้ RAM มาก | กรองช่วงเวลา/สถานีใน SQL ก่อน หรือใช้ view `daily_pm25` แทน |
| ค่าเฉลี่ยใน pandas กับ SQL ต่างกันเล็กน้อย | ตรวจว่ามีค่า `-999` หรือค่าติดลบหลุดเข้ามา (ควรเป็น `NULL` ตั้งแต่สัปดาห์ที่ 4) |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 6)

1. ให้ pipeline `fetch_air4thai.py` → `load_duckdb.py` รันต่อเนื่อง และสังเกตว่ามีวันใดที่ `n_hours` ต่ำผิดปกติ
2. ทบทวน `questions.md`: ปัญหาคุณภาพข้อมูลแบบใดจะกระทบคำตอบแต่ละข้อมากที่สุด จดไว้ 2–3 ข้อ
3. อ่านเอกสาร ydata-profiling หัวข้อ Quickstart และ pandera หัวข้อ DataFrame Schemas
4. (เสริม) อ่าน Polars User Guide หัวข้อ *Lazy API*
