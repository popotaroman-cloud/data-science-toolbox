---
title: "สัปดาห์ที่ 5: การจัดการข้อมูลและการเชื่อม SQL กับ Python"
---

> **CLO:** CLO2 · **เครื่องมือ:** pandas, DuckDB (หลัก), Polars (เสริม)
> **ผลงานที่เพิ่มในระบบ:** view `daily_pm25` ใน `data/pm25.duckdb` + tidy dataframe รายวันใน `notebooks/05_wrangling.ipynb`

## วัตถุประสงค์การเรียนรู้

เมื่อจบสัปดาห์นี้ ผู้เรียนสามารถ

1. ส่งข้อมูลระหว่าง DuckDB กับ pandas ได้ทั้งสองทิศทาง และเลือกได้ว่างานใดควรทำด้วย SQL หรือ pandas
2. อธิบายหลัก tidy data และแปลงรูปข้อมูลระหว่าง wide กับ long ด้วย `melt` / `pivot`
3. จัดการ datetime และ timezone ได้ถูกต้อง โดยเฉพาะขอบเขตของ "วัน" ในเวลาประเทศไทย
4. รวมข้อมูลรายชั่วโมงเป็นรายวันพร้อมคอลัมน์ความครบถ้วน `n_hours`
5. เปรียบเทียบการเขียนงานเดียวกันด้วย pandas และ Polars

---

## 1. จากฐานข้อมูลสู่คำถาม

สัปดาห์ที่ 4 เราได้ `measurements` รายชั่วโมง แต่คำถามส่วนใหญ่ใน `questions.md` ใช้ **ค่ารายวัน** เช่น Q1 นับ "จำนวนวันที่ค่าเฉลี่ย 24 ชั่วโมงเกิน 37.5 µg/m³" ส่วนคำถามเรื่องช่วงเวลาของวันต้องใช้รายชั่วโมงพร้อมคอลัมน์ชั่วโมง สัปดาห์นี้จึงแปลงข้อมูลให้อยู่ในรูปที่ตอบคำถามได้ตรง

```text
measurements (รายชั่วโมง)  ──SQL──►  daily_pm25 (view รายวัน)  ──.df()──►  pandas: tidy dataframe
       stations ──────────────────────────────────────────── JOIN ──┘         → สัปดาห์ที่ 6–7 ตรวจคุณภาพ
```

## 2. เชื่อม DuckDB กับ pandas

### จาก DuckDB ไป pandas

```python
import duckdb
import pandas as pd

con = duckdb.connect("data/pm25.duckdb", read_only=True)
st = con.sql("SELECT * FROM stations").df()                   # pandas DataFrame
h = con.sql("""
    SELECT station_id, ts, pm25 FROM measurements
    WHERE ts >= TIMESTAMP '2023-01-01' AND ts < TIMESTAMP '2024-01-01'
""").df()
h.dtypes      # station_id: object/str, ts: datetime64[...], pm25: float64
```

`duckdb.sql(...)` (ไม่มี `con`) ใช้ฐานข้อมูลในหน่วยความจำของ DuckDB ส่วน `con.sql(...)` ใช้ไฟล์ที่เปิดไว้ เวลาทำงานกับ `pm25.duckdb` ให้ใช้ `con` เสมอ

### จาก pandas กลับไป DuckDB

DuckDB query DataFrame ที่อยู่ในตัวแปร Python ได้โดยตรง โดยอ้างชื่อตัวแปรเหมือนชื่อตาราง

```python
top = duckdb.sql("""
    SELECT station_id, AVG(pm25) AS pm25_mean
    FROM h                       -- h คือ DataFrame ด้านบน
    GROUP BY station_id ORDER BY pm25_mean DESC LIMIT 5
""").df()
```

ถ้าต้องการใช้ร่วมกับตารางใน `pm25.duckdb` ให้ลงทะเบียน DataFrame กับ connection นั้น

```python
con.register("h_df", h)
con.sql("SELECT s.province, COUNT(*) n FROM h_df JOIN stations s USING (station_id) GROUP BY ALL").df()
```

### ควรทำงานไหนด้วยอะไร

| งาน | เครื่องมือที่เหมาะ | เหตุผล |
|---|---|---|
| กรองช่วงเวลา/สถานี ก่อนดึงออกมา | SQL | ไม่ต้องโหลดข้อมูลทั้งหมดเข้า RAM |
| รวมข้อมูลจำนวนมาก (`GROUP BY`) | SQL | DuckDB เร็วและประหยัดหน่วยความจำ |
| JOIN ตาราง | SQL หรือ pandas | ได้ทั้งคู่ SQL อ่านง่ายเมื่อหลายตาราง |
| แปลงรูป `melt`/`pivot`, จัดการ datetime ละเอียด | pandas | ยืดหยุ่นกว่า |
| ส่งต่อให้ seaborn / Plotly / Streamlit | pandas | ไลบรารีเหล่านี้รับ DataFrame |

หลักง่าย ๆ: **ลดขนาดข้อมูลด้วย SQL ก่อน แล้วค่อยปรับรูปด้วย pandas**

## 3. Tidy data

Hadley Wickham (2014) นิยาม **tidy data** ด้วยกฎ 3 ข้อ

1. ตัวแปรหนึ่งตัวอยู่ในคอลัมน์หนึ่งคอลัมน์
2. การสังเกตหนึ่งครั้งอยู่ในแถวหนึ่งแถว
3. หน่วยการสังเกตหนึ่งชนิดอยู่ในตารางหนึ่งตาราง

| ตัวอย่างที่ไม่ tidy | ปัญหา | แบบ tidy |
|---|---|---|
| คอลัมน์ `pm25_jan`, `pm25_feb`, … | ค่าของตัวแปร "เดือน" ไปอยู่ในชื่อคอลัมน์ | คอลัมน์ `month` + `pm25` |
| คอลัมน์ละสถานี `02t`, `35t`, … | ค่าของตัวแปร "สถานี" อยู่ในชื่อคอลัมน์ | คอลัมน์ `station_id` + `pm25` |
| ชื่อจังหวัดซ้ำทุกแถวของค่าวัด | หน่วยการสังเกตสองชนิดปนกัน | แยก `stations` กับ `measurements` แล้ว JOIN เมื่อใช้ |

`measurements` มีคอลัมน์ `pm25, pm10, o3, …` แยกกัน เป็น tidy เมื่อ *หน่วยการสังเกตคือสถานี-ชั่วโมง* แต่ถ้าคำถามคือ "เปรียบเทียบมลพิษแต่ละชนิด" รูปแบบ long (คอลัมน์ `pollutant` + `value`) จะสะดวกกว่า tidy จึงขึ้นกับคำถาม

### melt และ pivot

```python
wide = con.sql("""SELECT station_id, ts, pm25, pm10 FROM measurements
                  WHERE station_id = '35t' AND ts >= TIMESTAMP '2023-03-01' LIMIT 4""").df()

long = wide.melt(id_vars=["station_id", "ts"], var_name="pollutant", value_name="value")
#   station_id                  ts pollutant  value
# 0        35t 2023-03-01 00:00:00      pm25   88.0
# ...                                   pm10  120.0

back = long.pivot(index=["station_id", "ts"], columns="pollutant", values="value").reset_index()
```

| ฟังก์ชัน | จาก → ไป | ใช้เมื่อ |
|---|---|---|
| `melt` | wide → long | วาดกราฟหลายตัวแปรใน facet เดียว (สัปดาห์ที่ 9) |
| `pivot` | long → wide (key ไม่ซ้ำ) | ทำตารางสรุป หรือคำนวณอัตราส่วน `pm25 / pm10` |
| `pivot_table` | long → wide พร้อมรวมค่า (`aggfunc`) | key ซ้ำ เช่น เฉลี่ยรายเดือน × ภาค |

DuckDB ก็มี `UNPIVOT` / `PIVOT` เช่น `UNPIVOT measurements ON pm25, pm10 INTO NAME pollutant VALUE value` ใช้ได้เมื่อข้อมูลใหญ่เกินจะ `melt` ใน pandas

## 4. Datetime และ timezone

### ข้อตกลงของรายวิชา

คอลัมน์ `ts` เป็น `TIMESTAMP` **ไม่มี timezone กำกับ** แต่ตกลงกันว่าเป็นเวลาท้องถิ่น `Asia/Bangkok` (UTC+7) ตามที่ Air4Thai ส่งมา

| ปัญหาที่พบบ่อย | ผลกระทบ |
|---|---|
| รวมข้อมูลจากแหล่งที่ใช้ UTC กับแหล่งที่ใช้เวลาไทย | เวลาเลื่อนกัน 7 ชั่วโมง ค่ายอดสูงช่วงเช้ากลายเป็นช่วงดึก |
| ตัด "วัน" ด้วยเวลา UTC | วันของไทยเริ่ม 07:00 UTC ค่าเฉลี่ยรายวันจะปนระหว่างสองวันจริง |
| ปี พ.ศ. ในข้อมูล | `pd.to_datetime` ไม่รู้จัก พ.ศ. ต้องลบ 543 ก่อน แสดงผลเป็น พ.ศ. ได้ แต่คำนวณด้วย ค.ศ. |

### ทำงานกับ timezone ใน pandas

```python
h["ts_bkk"] = h["ts"].dt.tz_localize("Asia/Bangkok")    # ประกาศว่าเวลานี้เป็นเวลาไทย
h["ts_utc"] = h["ts_bkk"].dt.tz_convert("UTC")          # แปลงเป็น UTC (เวลาจริงเดียวกัน)
h[["ts", "ts_bkk", "ts_utc"]].head(2)
#                    ts                    ts_bkk                    ts_utc
# 0 2023-01-01 00:00:00 2023-01-01 00:00:00+07:00 2022-12-31 17:00:00+00:00
```

| เมธอด | ทำอะไร |
|---|---|
| `tz_localize(tz)` | ติดป้าย timezone ให้เวลาที่ยังไม่มี โดยตัวเลขไม่เปลี่ยน |
| `tz_convert(tz)` | แปลงเวลาที่มี timezone แล้วไปอีก timezone ตัวเลขเปลี่ยนแต่เป็นเวลาจริงเดียวกัน |
| `tz_localize(None)` | ลบป้าย timezone ก่อนบันทึกกลับเข้า `TIMESTAMP` |

ประเทศไทยไม่มี daylight saving time จึงไม่มีชั่วโมงซ้ำหรือหายจากการปรับนาฬิกา แต่ข้อมูลจากต่างประเทศมีปัญหานี้

### แยกส่วนประกอบของเวลา

```python
h["date"] = h["ts"].dt.date            # วันที่ (ใช้ตัดวันตามเวลาไทย เพราะ ts เป็นเวลาไทย)
h["hour"] = h["ts"].dt.hour            # ใช้ตอบคำถามช่วงเวลาของวัน
h["month"] = h["ts"].dt.month
h["dow"] = h["ts"].dt.day_of_week      # 0 = จันทร์
h["year_be"] = h["ts"].dt.year + 543   # ปี พ.ศ. สำหรับแสดงผลเท่านั้น
```

## 5. รายชั่วโมงเป็นรายวัน พร้อมความครบถ้วน

ค่าเฉลี่ยรายวันจากข้อมูลที่หายไป 20 ชั่วโมงไม่ได้แทน "ค่าเฉลี่ย 24 ชั่วโมง" จริง ถ้าชั่วโมงที่หายคือช่วงที่ฝุ่นสูง ค่าเฉลี่ยจะต่ำเกินจริงและคำตอบของ Q1 จะผิด จึงต้องเก็บ **`n_hours`** (จำนวนชั่วโมงที่มีค่า) ไว้คู่กับค่าเฉลี่ยเสมอ

### ด้วย SQL: view `daily_pm25`

```sql
CREATE OR REPLACE VIEW daily_pm25 AS
SELECT station_id,
       CAST(ts AS DATE) AS date,          -- ตัดวันตามเวลาไทย
       AVG(pm25)        AS pm25_mean,     -- AVG ข้าม NULL อัตโนมัติ
       MAX(pm25)        AS pm25_max,
       COUNT(pm25)      AS n_hours        -- นับเฉพาะชั่วโมงที่มีค่า
FROM measurements
GROUP BY station_id, CAST(ts AS DATE);
```

**view** คือ query ที่ตั้งชื่อไว้ ไม่เก็บข้อมูลซ้ำ ทุกครั้งที่ query จะคำนวณจาก `measurements` ล่าสุด จึงไม่ต้องสร้างใหม่หลังโหลดข้อมูลเพิ่ม ถ้าข้อมูลใหญ่มากและ query ช้า ค่อยเปลี่ยนเป็น `CREATE OR REPLACE TABLE`

### ด้วย pandas: `resample`

```python
daily_pd = (
    h.set_index("ts")
     .groupby("station_id")["pm25"]
     .resample("D")
     .agg(["mean", "max", "count"])
     .rename(columns={"mean": "pm25_mean", "max": "pm25_max", "count": "n_hours"})
     .reset_index()
     .rename(columns={"ts": "date"})
)
```

ความต่างที่ต้องรู้: `resample` สร้างแถวให้ **ทุกวันในช่วง** แม้วันนั้นไม่มีข้อมูลเลย (`n_hours = 0`) ส่วน `GROUP BY` ใน SQL ไม่มีแถวของวันที่ไม่มีข้อมูล ถ้าจะนับ "วันที่ขาดข้อมูล" ต้องรู้ความต่างนี้

### เกณฑ์ความครบถ้วน

| `n_hours` | การใช้ |
|---|---|
| 24 | ครบ |
| 18–23 | ใช้ได้ตามเกณฑ์ของโครงการ (ตัวอย่างนี้ใช้ ≥ 18 ชั่วโมง หรือ 75%) |
| < 18 | ไม่นำมานับวันเกินมาตรฐาน แต่ต้องรายงานจำนวนวันที่ตัดออก |

เกณฑ์ 18 ชั่วโมงเป็น *การตัดสินใจของโครงการ* ไม่ใช่ข้อเท็จจริง ให้บันทึกไว้ใน `questions.md` ใต้คำถามที่ใช้ และระวังไม่เลือกเกณฑ์ที่ทำให้ผล "ดูดี" (garden of forking paths จากสัปดาห์ที่ 2) สัปดาห์ที่ 7 จะวิเคราะห์ว่าชั่วโมงที่หายเป็นแบบสุ่มหรือไม่

```python
daily = con.sql("""
    SELECT d.*, s.province, s.region,
           d.n_hours >= 18                       AS complete,
           d.n_hours >= 18 AND d.pm25_mean > 37.5 AS exceed_th,   -- มาตรฐานไทย 24 ชม.
           d.n_hours >= 18 AND d.pm25_mean > 15   AS exceed_who   -- WHO 2021
    FROM daily_pm25 d JOIN stations s USING (station_id)
""").df()
```

## 6. pandas กับ Polars (เสริม)

**Polars** เป็นไลบรารี DataFrame ที่เขียนด้วย Rust ใช้ Apache Arrow ในหน่วยความจำ (สัปดาห์ที่ 4) ทำงานหลาย core และมีโหมด lazy ที่วางแผน query ก่อนรัน

| ประเด็น | pandas | Polars |
|---|---|---|
| ความแพร่หลาย / ไลบรารีที่รองรับ | มากที่สุด (seaborn, statsmodels, scikit-learn) | เพิ่มขึ้นเร็ว บางไลบรารีต้องแปลงเป็น pandas ก่อน |
| index | มี (`set_index`, `reset_index`) | ไม่มี index ลดความสับสน |
| รูปแบบการเขียน | เมธอดหลายแบบ มีหลายวิธีทำสิ่งเดียวกัน | expression (`pl.col(...)`) สม่ำเสมอ |
| ความเร็ว / หน่วยความจำ | พอสำหรับข้อมูลหลักล้านแถว | เร็วกว่าชัดเจนเมื่อข้อมูลใหญ่ |
| รับข้อมูลจาก DuckDB | `.df()` | `.pl()` |

งานเดียวกัน (ค่ารายวัน) ด้วย Polars

```python
import polars as pl

hp = con.sql("SELECT station_id, ts, pm25 FROM measurements").pl()
daily_pl = (
    hp.group_by("station_id", pl.col("ts").dt.date().alias("date"))
      .agg(
          pl.col("pm25").mean().alias("pm25_mean"),
          pl.col("pm25").max().alias("pm25_max"),
          pl.col("pm25").count().alias("n_hours"),    # count ไม่นับ null
      )
      .sort("station_id", "date")
)
```

ในรายวิชานี้ใช้ **pandas เป็นหลัก** เพราะไลบรารีสัปดาห์ถัดไปรับ pandas ผู้ที่สนใจใช้ Polars ได้ แต่ต้องแปลงด้วย `.to_pandas()` ก่อนส่งต่อ และเมื่อข้อมูลใหญ่ ให้ลองให้ DuckDB รวมข้อมูลก่อน ซึ่งมักเร็วพอโดยไม่ต้องเปลี่ยนไลบรารี

## สรุป

- ลดขนาดข้อมูลด้วย SQL แล้วส่งเข้า pandas ด้วย `.df()` และ DuckDB query DataFrame ได้โดยตรง
- tidy data: ตัวแปรหนึ่งคอลัมน์ การสังเกตหนึ่งแถว และรูปแบบที่ "tidy" ขึ้นกับคำถาม ใช้ `melt` / `pivot` สลับรูป
- `ts` เป็นเวลาไทยแบบไม่มี timezone กำกับ ใช้ `tz_localize` / `tz_convert` เมื่อต้องรวมกับแหล่งอื่น และตัดวันตามเวลาไทยเสมอ
- ค่ารายวันต้องมี `n_hours` คู่กัน และเกณฑ์ความครบถ้วนเป็นการตัดสินใจที่ต้องบันทึกไว้
- Polars เป็นทางเลือกที่เร็วกว่า แต่ pandas ยังเป็นภาษากลางของไลบรารีอื่น

## คำถามทบทวน

1. ทำไมควรกรองช่วงเวลาใน SQL ก่อน `.df()` แทนการดึงทั้งตารางแล้วกรองใน pandas
2. ตารางที่มีคอลัมน์ `pm25_2563`, `pm25_2564`, … เป็น tidy หรือไม่ แปลงอย่างไร
3. ถ้า `ts` เป็น UTC แต่เราใช้ `CAST(ts AS DATE)` ตัดวัน ค่าเฉลี่ยของ "วันที่ 1 มีนาคม" จะครอบคลุมช่วงเวลาไทยใด
4. สถานีหนึ่งมี `n_hours = 6` และ `pm25_mean = 20` ในวันที่ฝุ่นสูงทั้งจังหวัด ควรตีความอย่างไร
5. `resample("D")` กับ `GROUP BY CAST(ts AS DATE)` ให้จำนวนแถวต่างกันเมื่อใด
6. ถ้าใช้เกณฑ์ `n_hours >= 12` แทน `>= 18` คำตอบของ Q1 อาจเปลี่ยนอย่างไร และควรรายงานอย่างไร

## อ่านเพิ่มเติม

- Wickham, H. (2014). Tidy Data. *Journal of Statistical Software*, 59(10).
- McKinney, W. *Python for Data Analysis* (3e), บทที่ 8 (Data Wrangling) และบทที่ 11 (Time Series)
- เอกสาร DuckDB: *Python API — SQL on Pandas* และ `PIVOT` / `UNPIVOT` — <https://duckdb.org/docs/>
- เอกสาร pandas: *Time series / date functionality* — <https://pandas.pydata.org/docs/user_guide/timeseries.html>
- Polars User Guide: *Coming from Pandas* — <https://docs.pola.rs/>

➡️ [คู่มือปฏิบัติการสัปดาห์ที่ 5](lab.md)
