---
title: "สัปดาห์ที่ 4: การจัดเก็บและสืบค้นข้อมูลด้วย DuckDB, SQL และ Parquet"
---

> **CLO:** CLO2 · **เครื่องมือ:** DuckDB, SQL, Parquet (หลัก), Apache Arrow (แนวคิด เสริม)
> **ผลงานที่เพิ่มในระบบ:** `src/load_duckdb.py` ที่สร้าง `data/pm25.duckdb` มีตาราง `stations` และ `measurements`

## วัตถุประสงค์การเรียนรู้

เมื่อจบสัปดาห์นี้ ผู้เรียนสามารถ

1. อธิบายได้ว่าทำไมฐานข้อมูลเชิงวิเคราะห์แบบไฟล์เดียว (DuckDB) เหมาะกับงาน EDA
2. ออกแบบตาราง `stations` และ `measurements` พร้อม primary key ที่เหมาะสม
3. เขียน SQL พื้นฐาน: `SELECT`, `WHERE`, `GROUP BY`, `JOIN` และ window function เบื้องต้น
4. เขียน script โหลดข้อมูลแบบ idempotent (รันซ้ำแล้วไม่เกิดแถวซ้ำ)
5. ส่งออกและอ่านไฟล์ Parquet และอธิบายแนวคิด columnar storage และ Apache Arrow

---

## 1. จากไฟล์ raw สู่ฐานข้อมูล

สัปดาห์ที่ 3 เราได้ไฟล์ `data/raw/air4thai_*.json` หลายไฟล์ ไฟล์ละหนึ่งชั่วโมง ถ้าจะตอบ Q1 ("ภาคเหนือมีวันเกินมาตรฐานมากกว่าภาคอื่นหรือไม่") จาก JSON โดยตรง ต้องเปิดทุกไฟล์ แกะ key ซ้อนชั้น และรวมเองทุกครั้ง สัปดาห์นี้เราแปลง raw ให้เป็น **ตาราง** ที่ถามด้วย SQL ได้

```text
data/raw/*.json  ──►  src/load_duckdb.py  ──►  data/pm25.duckdb  ──►  SQL / pandas (สัปดาห์ที่ 5)
data/sample/*.csv ─┘   (แปลง + ตัดซ้ำ)          stations, measurements
```

## 2. ทำไมใช้ฐานข้อมูลเชิงวิเคราะห์แบบไฟล์เดียว

| ตัวเลือก | จุดเด่น | ข้อจำกัดสำหรับงานนี้ |
|---|---|---|
| ไฟล์ CSV/JSON หลายไฟล์ | เปิดง่าย | ไม่มีชนิดข้อมูล ไม่มี key ป้องกันแถวซ้ำ ต้องโหลดใหม่ทุกครั้ง |
| SQLite | ไฟล์เดียว ใช้แพร่หลาย | ออกแบบสำหรับงานธุรกรรม (OLTP) อ่านทีละแถว รวมข้อมูลหลายล้านแถวช้า |
| PostgreSQL / MySQL | ครบเครื่อง หลายคนใช้พร้อมกัน | ต้องติดตั้งและดูแล server เกินความจำเป็นสำหรับโครงการคนเดียว |
| **DuckDB** | ไฟล์เดียว ไม่ต้องมี server, เก็บแบบ columnar รวมข้อมูลเร็วมาก, อ่าน CSV/Parquet/pandas ได้ตรง | เขียนพร้อมกันหลาย process ไม่ได้ (เหมาะกับงานวิเคราะห์ ไม่ใช่ระบบรับคำสั่งซื้อ) |

**OLTP กับ OLAP:** ระบบธุรกรรม (OLTP) อ่าน/เขียนทีละแถว เช่น "บันทึกการสั่งซื้อหนึ่งรายการ" ส่วนงานวิเคราะห์ (OLAP) อ่านคอลัมน์ไม่กี่คอลัมน์จากแถวจำนวนมาก เช่น "ค่าเฉลี่ย PM2.5 ทุกสถานีทั้งปี" DuckDB เก็บข้อมูลแบบ **columnar** (ค่าในคอลัมน์เดียวกันอยู่ติดกัน) จึงอ่านเฉพาะคอลัมน์ `pm25` และ `ts` ได้โดยไม่ต้องอ่านคอลัมน์อื่น

ข้อมูลรายชั่วโมง 80 สถานี × 5 ปี ≈ 3.5 ล้านแถว ใหญ่เกินกว่าจะเปิดใน Excel สบาย ๆ แต่เล็กมากสำหรับ DuckDB

```python
import duckdb

con = duckdb.connect("data/pm25.duckdb")     # ถ้าไม่มีไฟล์ จะสร้างใหม่
con.sql("SELECT 42 AS answer").show()
con.close()
```

## 3. ออกแบบตาราง (data model)

ข้อมูลจาก Air4Thai มีสองส่วนที่เปลี่ยนแปลงไม่เท่ากัน: ข้อมูลสถานี (แทบไม่เปลี่ยน) กับค่าที่วัด (เพิ่มทุกชั่วโมง) จึงแยกเป็นสองตาราง

```sql
CREATE TABLE IF NOT EXISTS stations (
    station_id   VARCHAR PRIMARY KEY,
    name_th      VARCHAR,
    name_en      VARCHAR,
    province     VARCHAR,
    region       VARCHAR,
    lat          DOUBLE,
    lon          DOUBLE,
    station_type VARCHAR
);

CREATE TABLE IF NOT EXISTS measurements (
    station_id VARCHAR,
    ts         TIMESTAMP,          -- เวลาท้องถิ่น Asia/Bangkok รายชั่วโมง
    pm25 DOUBLE, pm10 DOUBLE, o3 DOUBLE, co DOUBLE, no2 DOUBLE, so2 DOUBLE,
    PRIMARY KEY (station_id, ts)
);
```

| การตัดสินใจ | เหตุผล |
|---|---|
| แยก `stations` ออกจาก `measurements` | ไม่ต้องเก็บชื่อและพิกัดซ้ำทุกชั่วโมง แก้ชื่อสถานีที่เดียว |
| primary key `(station_id, ts)` | หนึ่งสถานีมีค่าได้เพียงหนึ่งแถวต่อหนึ่งชั่วโมง ฐานข้อมูลจะปฏิเสธแถวซ้ำให้ |
| `ts` เป็น `TIMESTAMP` เวลาท้องถิ่น | ค่าจาก Air4Thai เป็นเวลาประเทศไทย เก็บตามนั้นและตกลงกันทั้งโครงการ (สัปดาห์ที่ 5 จะลงรายละเอียด timezone) |
| ค่ามลพิษเป็น `DOUBLE` และค่าหายเป็น `NULL` | ห้ามเก็บค่าพิเศษ เช่น `-1` หรือ `-999` เพราะ `AVG()` จะนำไปคำนวณด้วย |
| `region` อยู่ใน `stations` | Air4Thai ไม่ส่งภาคมา เราเติมจากตาราง mapping จังหวัด → ภาค ที่เขียนเอง เพื่อตอบ Q1 |

## 4. SQL พื้นฐานกับข้อมูล PM2.5

DuckDB ใช้ SQL มาตรฐาน คำสั่งต่อไปนี้ใช้บ่อยที่สุด

### SELECT และ WHERE

```sql
SELECT station_id, ts, pm25
FROM measurements
WHERE pm25 > 75                         -- ค่ารายชั่วโมงสูง (มาตรฐาน 37.5 ใช้กับค่าเฉลี่ย 24 ชม. ดูสัปดาห์ที่ 5)
  AND ts >= TIMESTAMP '2023-01-01'
ORDER BY pm25 DESC
LIMIT 10;
```

### GROUP BY

```sql
SELECT station_id,
       COUNT(*)            AS n_rows,
       COUNT(pm25)         AS n_pm25,     -- นับเฉพาะค่าที่ไม่ใช่ NULL
       ROUND(AVG(pm25), 1) AS pm25_mean,
       MAX(pm25)           AS pm25_max
FROM measurements
GROUP BY station_id
ORDER BY pm25_mean DESC;
```

> `COUNT(*)` นับทุกแถว `COUNT(pm25)` นับเฉพาะแถวที่มีค่า ผลต่างของสองค่านี้คือจำนวนชั่วโมงที่ PM2.5 หาย ซึ่งสำคัญมากในสัปดาห์ที่ 6–7

### JOIN

```sql
SELECT s.region,
       COUNT(DISTINCT s.station_id) AS n_stations,
       ROUND(AVG(m.pm25), 1)        AS pm25_mean
FROM measurements AS m
JOIN stations     AS s USING (station_id)
GROUP BY s.region
ORDER BY pm25_mean DESC;
```

| ชนิด JOIN | ผลลัพธ์ |
|---|---|
| `JOIN` (INNER) | เฉพาะแถวที่ตรงกันทั้งสองตาราง |
| `LEFT JOIN` | ทุกแถวของตารางซ้าย ถ้าไม่ตรงได้ `NULL` (ใช้หาว่ามีค่าวัดของสถานีที่ไม่อยู่ใน `stations` หรือไม่) |

```sql
-- ตรวจสอบ: มี station_id ใน measurements ที่ไม่มีใน stations หรือไม่
SELECT DISTINCT m.station_id
FROM measurements m LEFT JOIN stations s USING (station_id)
WHERE s.station_id IS NULL;
```

### Window function (เบื้องต้น)

window function คำนวณข้ามหลายแถวโดย *ไม่ยุบแถว* ต่างจาก `GROUP BY`

```sql
-- ค่าเฉลี่ยเคลื่อนที่ 24 แถวล่าสุดของแต่ละสถานี
SELECT station_id, ts, pm25,
       AVG(pm25) OVER (
           PARTITION BY station_id ORDER BY ts
           ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
       ) AS pm25_roll24
FROM measurements;

-- 3 ชั่วโมงที่ PM2.5 สูงสุดของแต่ละสถานี
SELECT station_id, ts, pm25
FROM measurements
QUALIFY ROW_NUMBER() OVER (PARTITION BY station_id ORDER BY pm25 DESC NULLS LAST) <= 3;
```

`ROWS BETWEEN 23 PRECEDING` นับ 24 *แถว* ไม่ใช่ 24 *ชั่วโมง* ถ้ามีชั่วโมงหายผลจะคลาดเคลื่อน สัปดาห์ที่ 5 จะทำค่ารายวันพร้อมจำนวนชั่วโมงที่มีข้อมูลแทน `QUALIFY` เป็นส่วนขยายของ DuckDB ใช้กรองผลของ window function

### ใช้ SQL จาก Python

```python
con = duckdb.connect("data/pm25.duckdb", read_only=True)
con.sql("SELECT COUNT(*) FROM measurements").fetchall()      # [(3504000,)] list ของ tuple
df = con.sql("SELECT * FROM stations").df()                 # ได้ pandas DataFrame
con.execute("SELECT * FROM measurements WHERE station_id = ?", ["02t"]).df()   # ใช้ ? แทนการต่อ string
```

ใช้ `?` (parameter) แทนการต่อ string ด้วย f-string เมื่อค่ามาจากภายนอก เพื่อกัน SQL injection และปัญหาเครื่องหมายคำพูด

## 5. การโหลดแบบ idempotent

**idempotent** คือรันกี่ครั้งก็ได้ผลเหมือนรันครั้งเดียว script ที่ดีต้องรันซ้ำได้ เพราะเราจะรันหลังดึงข้อมูลทุกชั่วโมง และไฟล์ raw สองไฟล์อาจมีค่าของชั่วโมงเดียวกัน (ถ้าดึงสองครั้งในชั่วโมงเดียว)

| วิธี | คำสั่ง | ผล |
|---|---|---|
| `INSERT` ธรรมดา | `INSERT INTO measurements SELECT ...` | รันครั้งที่สอง error เพราะชน primary key (หรือแถวซ้ำถ้าไม่มี key) |
| ข้ามแถวที่มีแล้ว | `INSERT OR IGNORE INTO ...` | เก็บค่าเดิม ไม่สนใจค่าใหม่ |
| **upsert** | `INSERT OR REPLACE INTO ...` | ถ้ามี `(station_id, ts)` แล้ว แทนด้วยค่าใหม่ ถ้ายังไม่มี เพิ่ม |
| ลบแล้วสร้างใหม่ | `CREATE OR REPLACE TABLE ...` จากไฟล์ทั้งหมด | ง่ายและถูกต้อง แต่ช้าลงเมื่อไฟล์มากขึ้น |

ขั้นตอนที่ใช้ในรายวิชา

```text
1. อ่าน raw ทุกไฟล์ → DataFrame
2. ตัดซ้ำในชุดใหม่ก่อน: เหลือหนึ่งแถวต่อ (station_id, ts) โดยเลือกไฟล์ที่ดึงล่าสุด
3. INSERT OR REPLACE เข้าตาราง (primary key ป้องกันแถวซ้ำ)
4. ตรวจ: จำนวนแถวก่อน/หลัง, ไม่มี (station_id, ts) ซ้ำ
```

```sql
INSERT OR REPLACE INTO measurements (station_id, ts, pm25, pm10, o3, co, no2, so2)
SELECT station_id, ts, pm25, pm10, o3, co, no2, so2
FROM new_rows
QUALIFY ROW_NUMBER() OVER (PARTITION BY station_id, ts ORDER BY fetched_at DESC) = 1;
```

ขั้นที่ 2 จำเป็น เพราะ DuckDB ไม่ยอมให้คำสั่งเดียว upsert key เดียวกันสองครั้ง

ตรวจว่าไม่มีแถวซ้ำ (ควรได้ตารางว่าง)

```sql
SELECT station_id, ts, COUNT(*) AS n
FROM measurements GROUP BY ALL HAVING n > 1;
```

## 6. Parquet และ Apache Arrow

### Parquet

**Parquet** เป็นรูปแบบไฟล์แบบ columnar ที่บีบอัดและเก็บชนิดข้อมูลไว้ในไฟล์ ใช้แลกเปลี่ยนข้อมูลกับเครื่องมืออื่น (pandas, Polars, Spark, Power BI) หรือสำรองข้อมูล

| | CSV | Parquet |
|---|---|---|
| ชนิดข้อมูล | ไม่มี (ทุกอย่างเป็นข้อความ) | เก็บไว้ในไฟล์ (`TIMESTAMP`, `DOUBLE`) |
| ขนาด | ใหญ่ | เล็กกว่ามาก (บีบอัดรายคอลัมน์) |
| อ่านบางคอลัมน์ | ต้องอ่านทั้งไฟล์ | อ่านเฉพาะคอลัมน์ที่ต้องการได้ |
| เปิดด้วยตา | ได้ | ไม่ได้ ต้องใช้โปรแกรม |

```sql
-- ส่งออกทั้งตาราง
COPY measurements TO 'data/parquet/measurements.parquet' (FORMAT parquet);

-- ส่งออกแบบแบ่งโฟลเดอร์ตามปี (partition)
COPY (SELECT *, year(ts) AS year FROM measurements)
TO 'data/parquet/measurements' (FORMAT parquet, PARTITION_BY (year), OVERWRITE_OR_IGNORE);

-- อ่านกลับ: DuckDB query ไฟล์ Parquet ได้โดยตรงโดยไม่ต้องโหลดเข้าตาราง
SELECT year, COUNT(*) FROM read_parquet('data/parquet/measurements/*/*.parquet', hive_partitioning = true)
GROUP BY year ORDER BY year;
```

```python
import pandas as pd
pd.read_parquet("data/parquet/measurements.parquet", columns=["station_id", "ts", "pm25"])
```

### Apache Arrow (แนวคิด)

**Apache Arrow** เป็นรูปแบบการเก็บตารางแบบ columnar *ในหน่วยความจำ* ที่หลายเครื่องมือใช้ร่วมกัน เมื่อ DuckDB ส่งผลให้ pandas หรือ Polars ผ่าน Arrow ข้อมูลไม่ต้องถูกแปลงทีละค่า จึงเร็ว เปรียบเทียบง่าย ๆ: Parquet คือรูปแบบบน *ดิสก์* ส่วน Arrow คือรูปแบบใน *RAM*

```python
tbl = con.sql("SELECT * FROM stations").fetch_arrow_table()   # pyarrow.Table
```

ผู้เรียนไม่ต้องเขียนโค้ด Arrow โดยตรง แต่ควรรู้ว่าเป็นเหตุผลที่ DuckDB, pandas และ Polars ส่งข้อมูลถึงกันได้เร็ว

## 7. โครงสร้างของ `src/load_duckdb.py`

```text
1. เปิด data/pm25.duckdb และสร้างตาราง (CREATE TABLE IF NOT EXISTS)
2. อ่าน data/raw/air4thai_*.json ทุกไฟล์ → แปลงเป็นแถวของ stations และ measurements
   (ใช้ตารางจับคู่ key จากสัปดาห์ที่ 3 ไม่เดาชื่อ key)
3. แปลงค่า: string → ตัวเลข, ค่าติดลบ/ว่าง → NULL, date + time → TIMESTAMP
4. (ถ้าเลือก) โหลดไฟล์ตัวอย่างจากผู้สอนใน data/sample/ เป็นข้อมูลย้อนหลัง
5. upsert ทั้งสองตาราง แล้วเติม region จาก mapping จังหวัด → ภาค
6. พิมพ์สรุป: จำนวนสถานี จำนวนแถว ช่วงเวลา และตรวจแถวซ้ำ
```

โค้ดเต็มอยู่ในคู่มือปฏิบัติการ

## สรุป

- DuckDB เป็นฐานข้อมูลเชิงวิเคราะห์แบบไฟล์เดียว columnar ไม่ต้องมี server เหมาะกับงาน EDA
- แยก `stations` (แทบไม่เปลี่ยน) กับ `measurements` (เพิ่มทุกชั่วโมง) และใช้ primary key `(station_id, ts)`
- SQL หลัก: `SELECT`/`WHERE` กรอง, `GROUP BY` รวม, `JOIN` เชื่อมตาราง, window function คำนวณข้ามแถวโดยไม่ยุบแถว
- โหลดแบบ idempotent: ตัดซ้ำในชุดใหม่ แล้ว `INSERT OR REPLACE`
- Parquet สำหรับเก็บ/แลกเปลี่ยนบนดิสก์ Arrow สำหรับส่งข้อมูลในหน่วยความจำ

## คำถามทบทวน

1. ทำไม `COUNT(*)` กับ `COUNT(pm25)` ให้ค่าต่างกัน และค่าต่างนี้บอกอะไร
2. ถ้าเก็บค่าหายเป็น `-999` แทน `NULL` ค่าเฉลี่ยของสถานีที่ข้อมูลหาย 10% จะผิดไปทิศทางใด
3. ถ้าไม่มี primary key และรัน `load_duckdb.py` สามครั้ง จะเกิดอะไรกับคำตอบของ Q1
4. เขียน SQL หาจำนวนสถานีและค่าเฉลี่ย PM2.5 ของแต่ละจังหวัดในภาคเหนือ
5. `GROUP BY station_id` กับ `AVG(...) OVER (PARTITION BY station_id)` ให้ผลลัพธ์ต่างกันอย่างไร
6. เมื่อใดควรส่งออกเป็น Parquet แทนการส่งไฟล์ `pm25.duckdb` ให้เพื่อน

## อ่านเพิ่มเติม

- เอกสาร DuckDB: SQL Introduction, `INSERT` (ส่วน `INSERT OR REPLACE`), Window Functions, Parquet — <https://duckdb.org/docs/>
- เอกสาร DuckDB Python API — <https://duckdb.org/docs/stable/clients/python/overview>
- Apache Arrow: *Overview* — <https://arrow.apache.org/overview/>
- McKinney, W. *Python for Data Analysis* (3e), บท Data Loading, Storage, and File Formats

➡️ [คู่มือปฏิบัติการสัปดาห์ที่ 4](lab.md)
