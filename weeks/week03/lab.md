---
title: "ปฏิบัติการสัปดาห์ที่ 3: เขียน script ดึงข้อมูลจาก Air4Thai"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO2
> **ผลงานที่ต้องส่ง:** PR ที่ merge แล้ว ประกอบด้วย `src/fetch_air4thai.py`, `notebooks/03_inspect_response.ipynb` และ `.env.example` พร้อมไฟล์ raw JSON อย่างน้อย 3 ไฟล์ในเครื่อง (ไม่ commit)

## สิ่งที่ต้องเตรียม

- repo โครงการที่มี `questions.md` จากสัปดาห์ที่ 2 (รวมรายการ "ข้อมูลที่ต้องเก็บ")
- `.gitignore` ที่มี `data/` และ `.env` (จากสัปดาห์ที่ 1)
- สภาพแวดล้อม `dstoolbox` ตรวจด้วย `python -c "import requests, bs4; print('ok')"` และติดตั้ง `truststore` เพิ่ม (`conda install -c conda-forge truststore`) เพื่อแก้ปัญหา SSL ของ server (ดูตารางแก้ปัญหา)
- อินเทอร์เน็ต ถ้าเครือข่ายห้องปฏิบัติการเข้า Air4Thai ไม่ได้ ให้ใช้ไฟล์ตัวอย่างจากผู้สอน `data/sample/air4thai_sample.json` ในขั้นที่ 2 แล้วทำขั้นที่ 3–4 ต่อ

---

## ขั้นที่ 1: สร้าง branch และโฟลเดอร์

```bash
git switch main
git pull
git switch -c week03-fetch
mkdir -p data/raw
```

> Windows (PowerShell) ใช้ `mkdir data\raw` แทน `mkdir -p data/raw`

## ขั้นที่ 2: สำรวจ response จริงใน notebook

สร้าง `notebooks/03_inspect_response.ipynb` แล้วรันทีละ cell

```python
import requests, json
import truststore; truststore.inject_into_ssl()     # แก้ SSLError จาก certificate chain ของ server

URL = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
HEADERS = {"User-Agent": "pm25-explorer/0.1 (student project)"}

r = requests.get(URL, headers=HEADERS, timeout=(10, 60))
print(r.status_code, r.headers.get("Content-Type"), len(r.content), "bytes")
data = r.json()

# ถ้าดึงไม่ได้ ใช้ไฟล์ตัวอย่างจากผู้สอน
# data = json.load(open("../data/sample/air4thai_sample.json", encoding="utf-8"))
```

```python
print(list(data.keys()))
st = data["stations"]
print(len(st), "สถานี")
print(json.dumps(st[0], ensure_ascii=False, indent=2)[:1500])   # ดูสถานีแรกแบบอ่านง่าย
```

ใช้ฟังก์ชัน `show_keys` จากเอกสารประกอบการสอนหัวข้อที่ 3 แล้วกรอกตารางนี้ใน Markdown cell **จากสิ่งที่เห็นจริง** (ตารางนี้จะใช้เขียน `load_duckdb.py` สัปดาห์ที่ 4)

| คอลัมน์ในตารางของเรา | path ของ key ใน JSON | ชนิดใน JSON | ตัวอย่างค่า |
|---|---|---|---|
| `station_id` | | | |
| `name_th` / `name_en` | | | |
| `province` (อยู่ในข้อความพื้นที่?) | | | |
| `lat` / `lon` | | | |
| `station_type` | | | |
| วันที่ + เวลาของค่าล่าสุด | | | |
| `pm25` (ความเข้มข้น ไม่ใช่ AQI) | | | |
| `pm10`, `o3`, `co`, `no2`, `so2` | | | |

ตอบเพิ่ม: ค่าหายถูกแทนด้วยอะไร และสถานีทุกสถานีมี key ครบเท่ากันหรือไม่

```python
from collections import Counter
Counter(tuple(sorted(s.keys())) for s in st).most_common(3)   # รูปแบบ key ที่พบบ่อย
```

## ขั้นที่ 3: เขียน `src/fetch_air4thai.py`

```python
"""ดึงค่าคุณภาพอากาศล่าสุดจาก Air4Thai แล้วบันทึก JSON ดิบลง data/raw/

รัน:  python src/fetch_air4thai.py
"""
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

try:                                   # ใช้ certificate store ของระบบปฏิบัติการ (ดูตารางแก้ปัญหา: SSLError)
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

URL = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
HEADERS = {"User-Agent": "pm25-explorer/0.1 (student project; your-email@ubu.ac.th)"}  # header ต้องเป็น ASCII ห้ามมีภาษาไทย
ROOT = Path(__file__).resolve().parents[1]          # root ของ repo
RAW_DIR = ROOT / "data" / "raw"
TZ = ZoneInfo("Asia/Bangkok")
RETRIES, WAIT = 3, 5
RETRY_STATUS = {429, 500, 502, 503, 504}          # ข้อผิดพลาดชั่วคราวที่ควรลองใหม่

RAW_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler(RAW_DIR / "fetch.log", encoding="utf-8")],
)
log = logging.getLogger("fetch_air4thai")


def fetch(url: str) -> requests.Response:
    """GET พร้อม timeout และ retry เฉพาะข้อผิดพลาดชั่วคราว"""
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=(10, 60))
        except (requests.ConnectionError, requests.Timeout) as e:
            reason = str(e)                         # เครือข่ายมีปัญหา → ลองใหม่
        else:
            if r.status_code not in RETRY_STATUS:
                r.raise_for_status()                # 4xx อื่น ๆ → error ถาวร ไม่ retry
                return r
            reason = f"status {r.status_code}"      # 429/5xx → ลองใหม่
        log.warning("ครั้งที่ %d/%d ล้มเหลว: %s", attempt, RETRIES, reason)
        if attempt == RETRIES:
            raise RuntimeError(f"ล้มเหลวครบ {RETRIES} ครั้ง: {reason}")
        time.sleep(WAIT * attempt)


def validate(r: requests.Response) -> int:
    """ตรวจว่า body เป็น JSON ที่มีรายการสถานี คืนจำนวนสถานี"""
    data = r.json()                                 # ไม่ใช่ JSON → ValueError
    stations = data.get("stations") if isinstance(data, dict) else None
    if not isinstance(stations, list) or not stations:
        raise ValueError(f"ไม่พบรายการสถานี key ที่ได้: {list(data)[:10]}")
    return len(stations)


def main() -> int:
    fetched_at = datetime.now(TZ)
    try:
        r = fetch(URL)
        n = validate(r)
    except Exception as e:                          # บันทึกทุกความล้มเหลวลง log
        log.error("ดึงข้อมูลไม่สำเร็จ: %s", e)
        return 1

    path = RAW_DIR / f"air4thai_{fetched_at:%Y%m%dT%H%M%S}.json"
    path.write_bytes(r.content)                     # เก็บ body ดิบตามที่ server ส่งมา
    log.info("บันทึก %s (%d สถานี, %d bytes)", path.name, n, len(r.content))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

อธิบายให้ได้ทุกบรรทัด (เพื่อนและผู้สอนจะถามใน review) โดยเฉพาะ

1. ทำไมใช้ `r.content` (bytes) แทน `json.dump(data)`
2. ทำไม 404 ไม่ retry แต่ 503 retry
3. ชื่อไฟล์ใช้เวลาของเครื่องเรา (เวลาดึง) ไม่ใช่เวลาของค่าที่วัด ต่างกันอย่างไร

ถ้า key ระดับบนสุดใน response จริงไม่ใช่ `stations` ให้แก้ใน `validate()` ตามที่พบในขั้นที่ 2

## ขั้นที่ 4: รันและทดสอบกรณีล้มเหลว

```bash
python src/fetch_air4thai.py
ls data/raw/
```

ผลที่คาด

```text
2026-10-23 14:05:01,234 INFO บันทึก air4thai_20261023T140500.json (XXX สถานี, XXXXXX bytes)
```

ทดสอบว่า script ล้มเหลวอย่างถูกต้อง: แก้ `URL` ชั่วคราวเป็น `.../getNewAQI_JSON_xxx.php` แล้วรัน ต้องเห็น `ERROR` ใน log ไม่มีไฟล์ใหม่ และ exit code เป็น 1

```bash
python src/fetch_air4thai.py; echo "exit code: $?"      # PowerShell: echo $LASTEXITCODE
```

อย่าลืมแก้ URL กลับ แล้วรันจริง **อย่างน้อย 3 ครั้ง ห่างกันอย่างน้อย 1 ชั่วโมง** (ทำต่อนอกเวลาได้) จะได้ข้อมูลหลายชั่วโมงไว้ใช้สัปดาห์ที่ 4

## ขั้นที่ 5: ตรวจ `robots.txt` และเตรียม `.env.example`

ใน notebook

```python
from urllib.robotparser import RobotFileParser
rp = RobotFileParser("http://air4thai.pcd.go.th/robots.txt")
rp.read()
rp.can_fetch(HEADERS["User-Agent"], URL)
```

บันทึกผลและเงื่อนไขการใช้ข้อมูลที่อ่านพบจากเว็บไซต์ (การอ้างอิงแหล่งที่มา) ลงใน `README.md` ของโครงการ หัวข้อ "แหล่งข้อมูล"

สร้าง `.env.example` ที่ root (Air4Thai ไม่ต้องใช้ key แต่ไฟล์นี้บอกผู้อื่นว่าโครงการมีค่าตั้งค่าอะไร)

```text
# คัดลอกเป็น .env แล้วกรอกค่า (ห้าม commit .env)
API_KEY=
```

ตรวจว่า `.env` ไม่ถูก Git ติดตาม: `git check-ignore -v .env` ต้องแสดงบรรทัดจาก `.gitignore`

## ขั้นที่ 6 (เสริม): ตั้งเวลาให้รันอัตโนมัติทุกชั่วโมง

| ระบบ | วิธี |
|---|---|
| macOS / Linux | `crontab -e` แล้วเพิ่ม `5 * * * * cd /path/to/pm25-explorer && /path/to/python src/fetch_air4thai.py` |
| Windows | Task Scheduler → Create Basic Task → Trigger รายชั่วโมง → Action: `python.exe` ของ env `dstoolbox`, argument `src\fetch_air4thai.py`, Start in: โฟลเดอร์ repo |

ใช้ path เต็มของ `python` ใน env (`python -c "import sys; print(sys.executable)"`) และตั้งให้รันนาทีที่ 5 ของทุกชั่วโมง เพื่อให้ server อัปเดตเสร็จก่อน

## ขั้นที่ 7: commit, push และเปิด pull request

```bash
git status                       # ต้องไม่เห็นไฟล์ใน data/
git add src/fetch_air4thai.py notebooks/03_inspect_response.ipynb .env.example README.md AI_USAGE.md
git commit -m "เพิ่ม script ดึงข้อมูล Air4Thai พร้อม retry และ logging"
git push -u origin week03-fetch
```

ในคำอธิบาย PR แนบผลรัน 3 ครั้ง (บรรทัด log) และตารางจับคู่ key จากขั้นที่ 2

## ขั้นที่ 8: review PR ของเพื่อน

clone หรือ checkout branch ของเพื่อนแล้ว **รัน script จริง** ก่อนให้ความเห็น

- [ ] `python src/fetch_air4thai.py` รันได้บนเครื่องเรา และได้ไฟล์ใหม่ใน `data/raw/`
- [ ] ทุก `requests.get` มี `timeout`
- [ ] retry เฉพาะข้อผิดพลาดชั่วคราว และมีการรอระหว่างครั้ง
- [ ] ชื่อไฟล์มี timestamp และไม่ทับไฟล์เดิม
- [ ] ใช้ `logging` และ log บอกได้ว่าสำเร็จหรือล้มเหลวเพราะอะไร
- [ ] ไม่มี API key, `.env` หรือไฟล์ใน `data/` ใน PR
- [ ] ตารางจับคู่ key มาจาก response จริง (ลองเปิดไฟล์ raw ของตนเองเทียบ)
- [ ] เจ้าของ PR อธิบายได้ว่าทำไมใช้ `r.content` และทำไม 404 ไม่ retry

---

## Checklist ก่อนส่งงาน

- [ ] `src/fetch_air4thai.py` รันซ้ำได้และคืน exit code 0/1 ถูกต้อง
- [ ] มีไฟล์ `data/raw/air4thai_*.json` อย่างน้อย 3 ไฟล์ (ต่างชั่วโมง) และ `data/raw/fetch.log` ในเครื่อง
- [ ] `notebooks/03_inspect_response.ipynb` มีตารางจับคู่ key ที่กรอกจากข้อมูลจริง
- [ ] `.env.example` อยู่ใน repo ส่วน `.env` ไม่อยู่
- [ ] `README.md` มีหัวข้อแหล่งข้อมูลและเงื่อนไขการใช้งาน
- [ ] บันทึกการใช้ AI ใน `AI_USAGE.md` (ถ้ามี)
- [ ] PR ถูก review และ merge แล้ว และได้ review PR ของเพื่อน

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `ZoneInfoNotFoundError: Asia/Bangkok` (Windows) | Windows ไม่มีฐานข้อมูล timezone ในตัว ติดตั้ง `tzdata` (`conda install -c conda-forge tzdata`) |
| `ConnectTimeout` / `ConnectionError` | เครือข่ายบล็อกหรือ server ไม่ตอบ ลองเครือข่ายอื่น หรือใช้ไฟล์ตัวอย่างจากผู้สอนเพื่อทำขั้นต่อไป |
| `JSONDecodeError` หรือ `ValueError` | server ส่ง HTML กลับมา ดู `r.text[:300]` อาจปิดปรับปรุงหรือ URL ผิด |
| `SSLError: CERTIFICATE_VERIFY_FAILED` | URL `http://` ถูก redirect ไป `https://` และ server ส่ง certificate chain ไม่ครบ (พบเมื่อ ต.ค. 2569) ติดตั้ง `truststore` (`conda install -c conda-forge truststore`) ซึ่ง script เรียกใช้อยู่แล้ว ได้ผลบน Windows/macOS ถ้ายังไม่ได้ (เช่น Linux/Colab) ใช้ไฟล์ตัวอย่างจากผู้สอน **ห้ามแก้ด้วย `verify=False`** เพราะปิดการตรวจตัวตนของ server |
| `FileNotFoundError` ของ `fetch.log` | ต้องสร้าง `RAW_DIR` ก่อนตั้งค่า logging (ดูลำดับใน script) |
| ภาษาไทยในไฟล์ raw อ่านเป็น `ก...` | ปกติของ JSON ที่ escape unicode ข้อมูลไม่เสีย `json.load` แล้วจะได้ภาษาไทย |
| `git status` เห็นไฟล์ใน `data/raw/` | `.gitignore` ไม่มี `data/` หรือสะกดผิด แก้แล้วรัน `git rm -r --cached data` |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 4)

1. ให้ script รันสะสมข้อมูลต่อไป (ด้วยมือหรือตั้งเวลา) ยิ่งได้หลายชั่วโมงยิ่งดี
2. ดาวน์โหลดไฟล์ตัวอย่างจากผู้สอน `data/sample/pm25_hourly_sample.csv` และ `data/sample/stations_sample.csv` ไว้ใช้สัปดาห์ที่ 4
3. ทำแบบฝึก SQL พื้นฐาน `SELECT`, `WHERE`, `GROUP BY` จาก <https://duckdb.org/docs/stable/sql/introduction>
4. คิดว่าข้อมูลจากขั้นที่ 2 ควรแยกเป็นกี่ตาราง และอะไรเป็น key ที่ทำให้หนึ่งแถวไม่ซ้ำกัน
