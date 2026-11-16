---
title: "ปฏิบัติการสัปดาห์ที่ 4: สร้างฐานข้อมูล DuckDB จากข้อมูล raw"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO2
> **ผลงานที่ต้องส่ง:** PR ที่ merge แล้ว ประกอบด้วย `src/load_duckdb.py`, `src/province_region.csv` และ `notebooks/04_sql.ipynb` ที่ query `data/pm25.duckdb` ได้

## สิ่งที่ต้องเตรียม

- `src/fetch_air4thai.py` จากสัปดาห์ที่ 3 และไฟล์ `data/raw/air4thai_*.json` อย่างน้อย 3 ไฟล์
- ตารางจับคู่ key ใน `notebooks/03_inspect_response.ipynb` (ห้ามข้าม ใช้เขียน `STATION_KEYS` ในขั้นที่ 3)
- ไฟล์ตัวอย่างจากผู้สอน `data/sample/pm25_hourly_sample.csv` (คอลัมน์ตรงกับตาราง `measurements`) และ `data/sample/stations_sample.csv` (คอลัมน์ตรงกับตาราง `stations`)
- ตรวจ: `python -c "import duckdb, pyarrow; print(duckdb.__version__)"` ควรได้ 1.x

---

## ขั้นที่ 1: สร้าง branch

```bash
git switch main
git pull
git switch -c week04-duckdb
```

## ขั้นที่ 2: สร้างตาราง mapping จังหวัด → ภาค

Air4Thai ไม่ส่งภาคมา แต่ Q1 ต้องใช้ สร้าง `src/province_region.csv` (ไฟล์อ้างอิงเล็ก ๆ ที่เราเขียนเอง จึง commit ได้ ต่างจากข้อมูลใน `data/`)

```text
province,region
เชียงใหม่,เหนือ
เชียงราย,เหนือ
ขอนแก่น,ตะวันออกเฉียงเหนือ
อุบลราชธานี,ตะวันออกเฉียงเหนือ
กรุงเทพฯ,กลาง
สงขลา,ใต้
```

เติมให้ครบทุกจังหวัดที่มีสถานี (ใช้การแบ่งภาคแบบเดียวทั้งโครงการ และระบุใน `README.md` ว่าใช้แบบใด เช่น 6 ภาคตามราชบัณฑิตยสถาน หรือ 5 ภาคตามกรมอุตุนิยมวิทยา) **ชื่อจังหวัดต้องสะกดตรงกับที่ได้จากข้อมูล** ตรวจในขั้นที่ 5

## ขั้นที่ 3: เขียน `src/load_duckdb.py`

```python
"""โหลด raw JSON จาก Air4Thai (และไฟล์ตัวอย่างจากผู้สอน) เข้า data/pm25.duckdb

รัน:  python src/load_duckdb.py            # โหลดเฉพาะ data/raw/
      python src/load_duckdb.py --sample   # โหลดข้อมูลย้อนหลังจาก data/sample/ ด้วย
"""
import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR, SAMPLE_DIR = ROOT / "data" / "raw", ROOT / "data" / "sample"
DB_PATH = ROOT / "data" / "pm25.duckdb"
REGION_CSV = ROOT / "src" / "province_region.csv"

# จับคู่ key จากตารางในสัปดาห์ที่ 3 -- แก้ให้ตรงกับ response จริง อย่าเชื่อค่าในเอกสาร
STATION_KEYS = {"station_id": "stationID", "name_th": "nameTH", "name_en": "nameEN",
                "area_th": "areaTH", "lat": "lat", "lon": "long", "station_type": "stationType"}
LAST_KEY, VALUE_KEY = "AQILast", "value"          # VALUE_KEY = ความเข้มข้น ไม่ใช่ค่า AQI
POLLUTANT_KEYS = {"pm25": "PM25", "pm10": "PM10", "o3": "O3",
                  "co": "CO", "no2": "NO2", "so2": "SO2"}
M_COLS = "station_id, ts, pm25, pm10, o3, co, no2, so2"

SCHEMA = """
CREATE TABLE IF NOT EXISTS stations (
    station_id VARCHAR PRIMARY KEY, name_th VARCHAR, name_en VARCHAR,
    province VARCHAR, region VARCHAR, lat DOUBLE, lon DOUBLE, station_type VARCHAR);
CREATE TABLE IF NOT EXISTS measurements (
    station_id VARCHAR, ts TIMESTAMP,
    pm25 DOUBLE, pm10 DOUBLE, o3 DOUBLE, co DOUBLE, no2 DOUBLE, so2 DOUBLE,
    PRIMARY KEY (station_id, ts));
"""


def to_num(x):
    """แปลงเป็น float; ค่าว่าง แปลงไม่ได้ หรือติดลบ (รหัสค่าหาย) → None"""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v >= 0 else None


def parse_file(path: Path):
    """แปลง raw JSON หนึ่งไฟล์ → (แถวสถานี, แถวค่าวัด)"""
    data = json.loads(path.read_bytes())
    fetched_at = path.stem.split("_")[-1]              # เช่น 20261023T140500
    st_rows, m_rows = [], []
    for s in data["stations"]:
        st = {col: s.get(key) for col, key in STATION_KEYS.items()}
        last = s.get(LAST_KEY) or {}
        row = {"station_id": st["station_id"], "fetched_at": fetched_at,
               "ts_text": f"{last.get('date', '')} {last.get('time', '')}"}
        for col, key in POLLUTANT_KEYS.items():
            p = last.get(key)
            row[col] = to_num(p.get(VALUE_KEY)) if isinstance(p, dict) else None
        st_rows.append(st)
        m_rows.append(row)
    return st_rows, m_rows


def read_raw():
    files = sorted(RAW_DIR.glob("air4thai_*.json"))    # เรียงตามเวลาที่ดึง
    st_all, m_all = [], []
    for f in files:
        try:
            st, m = parse_file(f)
        except (KeyError, ValueError) as e:
            print(f"ข้าม {f.name}: {e}")
            continue
        st_all += st
        m_all += m
    st = pd.DataFrame(st_all).drop_duplicates("station_id", keep="last")
    st["province"] = st["area_th"].str.split(",").str[-1].str.strip()   # ตรวจรูปแบบข้อความพื้นที่จริง
    # บางสถานี (เช่น stationType "BKK") ไม่มีจุลภาคใน areaTH จะได้ province ผิด -- ตรวจในขั้นที่ 5
    m = pd.DataFrame(m_all)
    m["ts"] = pd.to_datetime(m["ts_text"], errors="coerce")
    bad = m["ts"].isna().sum()
    if bad:
        print(f"เตือน: แปลงเวลาไม่ได้ {bad} แถว (ตัดทิ้ง)")
    m = m.dropna(subset=["station_id", "ts"])
    print(f"raw: {len(files)} ไฟล์, {len(st)} สถานี, {len(m)} แถวค่าวัด")
    return st, m


def upsert(con, st: pd.DataFrame, m: pd.DataFrame):
    con.register("new_st", st)
    con.execute("""
        INSERT OR REPLACE INTO stations
        SELECT station_id, name_th, name_en, province, CAST(NULL AS VARCHAR),
               TRY_CAST(lat AS DOUBLE), TRY_CAST(lon AS DOUBLE), station_type
        FROM new_st""")
    con.register("new_m", m)
    con.execute(f"""
        INSERT OR REPLACE INTO measurements ({M_COLS})
        SELECT {M_COLS} FROM new_m
        QUALIFY ROW_NUMBER() OVER (PARTITION BY station_id, ts ORDER BY fetched_at DESC) = 1""")
    con.unregister("new_st")
    con.unregister("new_m")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="โหลดไฟล์ตัวอย่างจากผู้สอนด้วย")
    args = ap.parse_args()

    con = duckdb.connect(str(DB_PATH))
    con.execute(SCHEMA)

    if args.sample:                                     # ข้อมูลย้อนหลัง (โหลดก่อน raw)
        st = pd.read_csv(SAMPLE_DIR / "stations_sample.csv", dtype={"station_id": str})
        m = pd.read_csv(SAMPLE_DIR / "pm25_hourly_sample.csv",
                        dtype={"station_id": str}, parse_dates=["ts"])
        upsert(con, st, m.assign(fetched_at="00000000T000000"))
        print(f"sample: {len(st)} สถานี, {len(m)} แถว")

    if any(RAW_DIR.glob("air4thai_*.json")):
        upsert(con, *read_raw())

    # เติมภาคจาก mapping
    con.register("region_map", pd.read_csv(REGION_CSV))
    con.execute("""UPDATE stations SET region = r.region FROM region_map r
                   WHERE stations.province = r.province""")

    # สรุปและตรวจสอบ
    print(con.sql("""SELECT COUNT(*) AS n_rows, COUNT(DISTINCT station_id) AS n_stations,
                            MIN(ts) AS ts_min, MAX(ts) AS ts_max FROM measurements""").df())
    dup = con.sql("""SELECT COUNT(*) FROM (SELECT 1 FROM measurements
                     GROUP BY station_id, ts HAVING COUNT(*) > 1)""").fetchall()[0][0]
    no_region = con.sql("SELECT COUNT(*) FROM stations WHERE region IS NULL").fetchall()[0][0]
    print(f"แถวซ้ำ: {dup} | สถานีที่ยังไม่มีภาค: {no_region}")
    con.close()


if __name__ == "__main__":
    main()
```

ประเด็นที่ต้องอธิบายได้ในการ review

1. `to_num()` ตัดค่าติดลบเป็น `None` เพราะอะไร ถ้าข้อมูลจริงใช้รหัสค่าหายแบบอื่นต้องแก้ตรงไหน
2. ทำไมต้องตัดซ้ำด้วย `QUALIFY ROW_NUMBER() ...` ก่อน `INSERT OR REPLACE`
3. ทำไมโหลด sample ก่อน raw และให้ `fetched_at` ของ sample เป็นค่าต่ำสุด
4. `province` ได้จากการตัดข้อความพื้นที่หลังเครื่องหมายจุลภาคตัวสุดท้าย ถ้ารูปแบบข้อความจริงไม่ใช่แบบนี้ต้องแก้

> ถ้า `STATION_KEYS` ไม่ตรงกับข้อมูลจริง จะได้คอลัมน์ที่เป็น `None` ทั้งหมดโดยไม่มี error **ตรวจผลในขั้นที่ 5 ทุกครั้ง**

## ขั้นที่ 4: รันและทดสอบว่า idempotent

```bash
python src/load_duckdb.py --sample
python src/load_duckdb.py --sample      # รันซ้ำ จำนวนแถวต้องเท่าเดิม และแถวซ้ำ = 0
python src/fetch_air4thai.py            # ดึงเพิ่มอีกหนึ่งไฟล์
python src/load_duckdb.py               # จำนวนแถวเพิ่มไม่เกินจำนวนสถานี
```

ผลที่คาด (ตัวเลขขึ้นกับข้อมูลของแต่ละคน)

```text
sample: 80 สถานี, 3504000 แถว
raw: 4 ไฟล์, 180 สถานี, 720 แถวค่าวัด
   n_rows  n_stations              ts_min              ts_max
0  3504700         182 2020-01-01 00:00:00 2026-10-23 14:00:00
แถวซ้ำ: 0 | สถานีที่ยังไม่มีภาค: 12
```

บันทึกตัวเลขของการรันแต่ละครั้งไว้ใส่ในคำอธิบาย PR

## ขั้นที่ 5: ตรวจข้อมูลและฝึก SQL ใน notebook

สร้าง `notebooks/04_sql.ipynb` เปิดแบบ `read_only=True` เพื่อไม่ให้ชนกับ script ที่อาจรันอยู่

```python
import duckdb
con = duckdb.connect("../data/pm25.duckdb", read_only=True)
con.sql("SELECT * FROM stations LIMIT 5").df()
```

```python
# ตรวจ mapping: สถานีที่ยังไม่มีภาค และชื่อจังหวัดที่ได้จากข้อมูล
con.sql("SELECT province, COUNT(*) n FROM stations WHERE region IS NULL GROUP BY province").df()
```

แก้ `src/province_region.csv` จนสถานีที่ไม่มีภาคเหลือ 0 แล้วรัน `python src/load_duckdb.py` อีกครั้ง

ข้อสังเกตจากข้อมูลจริง (ต.ค. 2569) ที่ต้องตรวจในข้อมูลของตนเอง

- สถานีเครือข่ายกรุงเทพมหานคร (`station_type = 'BKK'`) บางแห่งมี `areaTH` ที่ไม่มีจุลภาค เช่น `"สวนจตุจักร เขตจตุจักร"` จึงได้ `province` เป็นชื่อสถานที่ ให้แก้ใน `read_raw()` เช่น กำหนด `province = "กรุงเทพฯ"` เมื่อ `station_type == "BKK"` แล้วบันทึกเหตุผลไว้ใน comment
- `ts` ของค่าล่าสุดบางสถานีเก่ากว่าเวลาที่ดึงหลายวันหรือหลายสัปดาห์ (สถานีหยุดส่งข้อมูล แต่ API ยังส่งค่าเดิม) primary key ทำให้ค่าเดิมไม่ถูกนับซ้ำ แต่ควรจดไว้เป็นประเด็นคุณภาพข้อมูลสำหรับสัปดาห์ที่ 6

```python
con.sql("""SELECT station_id, MAX(ts) AS last_ts FROM measurements
           GROUP BY station_id ORDER BY last_ts LIMIT 10""").df()      # สถานีที่ข้อมูลเก่าที่สุด
```

เขียน SQL ตอบคำถามต่อไปนี้ใน notebook (หนึ่ง cell ต่อหนึ่งข้อ พร้อม Markdown อธิบายผล)

1. จำนวนสถานีและจำนวนแถวต่อภาค
2. 10 สถานีที่มีสัดส่วนชั่วโมงที่ PM2.5 เป็น `NULL` มากที่สุด (ใช้ `COUNT(*)` กับ `COUNT(pm25)`)
3. ค่าเฉลี่ย PM2.5 รายเดือนของแต่ละภาค เฉพาะช่วงสำรวจ 2563–2566 (`ts < '2024-01-01'`, ใช้ `month(ts)` และ `JOIN stations`)
4. 3 ชั่วโมงที่ PM2.5 สูงสุดของแต่ละสถานีในภาคเหนือ (ใช้ `QUALIFY ROW_NUMBER() OVER (...)`)
5. สถานีใน `measurements` ที่ไม่มีใน `stations` (ใช้ `LEFT JOIN`)

ตัวอย่างข้อ 3 (เติมส่วนที่ขาด)

```python
con.sql("""
    SELECT s.region, month(m.ts) AS month, ROUND(AVG(m.pm25), 1) AS pm25_mean
    FROM measurements m JOIN stations s USING (station_id)
    WHERE m.ts < TIMESTAMP '2024-01-01'
    GROUP BY ALL
    ORDER BY ...
""").df()
```

> ข้อ 3 เป็นการสำรวจ ใช้เฉพาะช่วงสำรวจตามที่ตกลงไว้ใน `questions.md` ห้ามดูช่วงทดสอบ 2567–2568

## ขั้นที่ 6: ส่งออกและอ่าน Parquet

```python
import os
os.makedirs("../data/parquet", exist_ok=True)         # DuckDB ไม่สร้างโฟลเดอร์แม่ให้
# COPY ... TO เขียนไฟล์ภายนอก ไม่แก้ฐานข้อมูล จึงใช้ connection แบบ read_only ได้
con.sql("COPY stations TO '../data/parquet/stations.parquet' (FORMAT parquet)")
con.sql("""COPY (SELECT *, year(ts) AS year FROM measurements)
           TO '../data/parquet/measurements' (FORMAT parquet, PARTITION_BY (year), OVERWRITE_OR_IGNORE)""")
```

```python
# อ่านกลับและเทียบขนาด
duckdb.sql("""SELECT year, COUNT(*) n FROM read_parquet('../data/parquet/measurements/*/*.parquet',
              hive_partitioning = true) GROUP BY year ORDER BY year""").df()
```

เปรียบเทียบขนาดไฟล์ `pm25_hourly_sample.csv` กับโฟลเดอร์ Parquet แล้วบันทึกผลใน Markdown cell

## ขั้นที่ 7: commit, push และเปิด pull request

```bash
git status                       # ต้องไม่เห็น pm25.duckdb หรือไฟล์ .parquet
git add src/load_duckdb.py src/province_region.csv notebooks/04_sql.ipynb README.md AI_USAGE.md
git commit -m "เพิ่ม script โหลดข้อมูลเข้า DuckDB แบบ idempotent พร้อม mapping ภาค"
git push -u origin week04-duckdb
```

## ขั้นที่ 8: review PR ของเพื่อน

- [ ] รัน `python src/load_duckdb.py --sample` บนเครื่องเราได้ และรันซ้ำแล้วจำนวนแถวเท่าเดิม
- [ ] ตารางมี primary key `(station_id, ts)` และผลตรวจแถวซ้ำเป็น 0
- [ ] ค่าหายเก็บเป็น `NULL` ไม่ใช่ `-1`, `-999` หรือ `0`
- [ ] `STATION_KEYS` ตรงกับ key ใน raw JSON จริง (เปิดไฟล์ raw ของตนเองเทียบ)
- [ ] สถานีทุกสถานีมี `region` และวิธีแบ่งภาคเขียนไว้ใน README
- [ ] SQL ใน notebook ข้อ 3 ใช้เฉพาะช่วงสำรวจ
- [ ] ไม่มีไฟล์ `.duckdb`, `.parquet` หรือ `data/` ใน PR

---

## Checklist ก่อนส่งงาน

- [ ] `data/pm25.duckdb` มีตาราง `stations` และ `measurements` ตาม data model ของรายวิชา
- [ ] `load_duckdb.py` idempotent: รันซ้ำแล้วไม่มีแถวซ้ำ
- [ ] `notebooks/04_sql.ipynb` ตอบครบ 5 ข้อ รันได้ด้วย Restart & Run All
- [ ] ส่งออก Parquet สำเร็จและอ่านกลับได้
- [ ] PR ถูก review และ merge แล้ว และได้ review PR ของเพื่อน

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `IOException: Could not set lock on file` | มีอีก process เปิด `pm25.duckdb` อยู่ (เช่น notebook) ปิด connection ด้วย `con.close()` หรือ restart kernel แล้วรันใหม่ |
| `Constraint Error: Duplicate key` | ใช้ `INSERT INTO` แทน `INSERT OR REPLACE` กับข้อมูลที่มีอยู่แล้วในตาราง |
| ค่าบางชั่วโมงไม่ตรงกับไฟล์ที่ดึงล่าสุด (ไม่มี error) | batch ใหม่มี `(station_id, ts)` ซ้ำ และ DuckDB 1.5 เก็บแถวที่มาก่อนโดยไม่แจ้งเตือน ตรวจว่ามีบรรทัด `QUALIFY ROW_NUMBER() ... = 1` |
| `name_th` หรือ `pm25` เป็น `NULL` ทั้งคอลัมน์ | ชื่อ key ใน `STATION_KEYS` / `POLLUTANT_KEYS` ไม่ตรงกับข้อมูลจริง กลับไปดูตารางสัปดาห์ที่ 3 |
| `region` เป็น `NULL` บางสถานี | ชื่อจังหวัดสะกดไม่ตรง (เช่น `"กรุงเทพฯ"` กับ `"กรุงเทพมหานคร"`) หรือ `areaTH` ไม่มีจุลภาค แก้ CSV หรือปรับการตัดข้อความ |
| `station_id` "02t" กลายเป็นตัวเลขหรือหาย 0 นำหน้า | อ่าน CSV โดยไม่กำหนดชนิด ใช้ `dtype={"station_id": str}` |
| ไฟล์ `.duckdb` ใหญ่ผิดปกติหลังรันหลายครั้ง | ปกติของการ upsert ซ้ำ ลองรัน `CHECKPOINT` หรือสร้างฐานข้อมูลใหม่จาก raw (ข้อดีของการเก็บ raw) |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 5)

1. ให้ `fetch_air4thai.py` สะสมข้อมูลต่อ แล้วรัน `load_duckdb.py` หลังดึงทุกครั้ง
2. อ่านบทความ Wickham, H. (2014). *Tidy Data* ส่วนที่ 1–3 และคิดว่าตาราง `measurements` เป็น tidy หรือไม่
3. ทบทวน pandas: `groupby`, `merge`, `pd.to_datetime` จาก *Python for Data Analysis* บทที่ 8 และ 10
4. ทดลอง `con.sql("SELECT ...").df()` กับคำถามข้อใดข้อหนึ่งใน `questions.md`
