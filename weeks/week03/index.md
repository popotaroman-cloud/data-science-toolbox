---
title: "สัปดาห์ที่ 3: การได้มาซึ่งข้อมูลจาก API และเว็บไซต์"
---

> **CLO:** CLO2 · **เครื่องมือ:** requests (หลัก), BeautifulSoup (เสริม)
> **ผลงานที่เพิ่มในระบบ:** `src/fetch_air4thai.py` ที่บันทึก JSON ดิบพร้อม timestamp ลง `data/raw/`
>
> **อ่านประกอบในหนังสือ:** บทที่ 5 [การได้มาซึ่งข้อมูลจาก API และเว็บไซต์](../../book/chapters/05-data-acquisition.html) — อ่านเสริม: [หัวข้อ 16.1 พ.ร.บ.คุ้มครองข้อมูลส่วนบุคคล](../../book/chapters/16-synthetic-privacy.html#sec-ch16-pdpa) · [ภาคผนวก ง ข้อมูล Air4Thai](../../book/appendices/d-air4thai-open-data.html)

## วัตถุประสงค์การเรียนรู้

เมื่อจบสัปดาห์นี้ ผู้เรียนสามารถ

1. อธิบายองค์ประกอบของ HTTP request/response (method, URL, status code, header, body) ได้
2. อ่านโครงสร้าง JSON และตรวจ key ของ response จริงก่อนเขียนโค้ดประมวลผล
3. เขียน script ดึงข้อมูลด้วย requests ที่มี timeout, retry และ logging
4. ดึงข้อมูลอย่างสุภาพ: เคารพ rate limit, `robots.txt` และเงื่อนไขการใช้งาน
5. เก็บความลับ (API key) ใน `.env` ไม่ให้หลุดเข้า Git
6. อธิบายได้ว่าทำไมต้องเก็บข้อมูลดิบ (raw) ไว้ก่อนแปลงรูป

---

## 1. จากคำถามสู่ข้อมูลที่ต้องเก็บ

สัปดาห์ที่ 2 ผู้เรียนเขียนรายการ "ข้อมูลที่ต้องเก็บ" ท้าย `questions.md` แล้ว สัปดาห์นี้เปลี่ยนรายการนั้นเป็นโค้ด เช่น Q1 (วันเกินมาตรฐานตามภาค) ต้องการ

| สิ่งที่คำถามต้องการ | แหล่งใน Air4Thai |
|---|---|
| PM2.5 รายชั่วโมงของทุกสถานี | ค่าล่าสุดจาก `getNewAQI_JSON.php` (ดึงซ้ำทุกชั่วโมง) + ข้อมูลย้อนหลัง |
| รหัส ชื่อ พิกัด และพื้นที่ของสถานี | อยู่ใน response เดียวกัน |
| ภาคของสถานี | ไม่มีใน response ต้องสร้างตาราง mapping จังหวัด → ภาค เอง (สัปดาห์ที่ 4) |

> **ข้อมูลย้อนหลัง:** Air4Thai มีบริการข้อมูลย้อนหลังด้วย แต่ endpoint และพารามิเตอร์เปลี่ยนไปตามเวลา **ตรวจสอบ endpoint ล่าสุดจากเว็บไซต์ Air4Thai ก่อนใช้** ระหว่างนี้ใช้ไฟล์ตัวอย่างจากผู้สอนเป็นข้อมูลย้อนหลัง และใช้ script สัปดาห์นี้สะสมข้อมูลปัจจุบันไปเรื่อย ๆ

## 2. HTTP พื้นฐาน

ทุกครั้งที่ browser หรือ Python ขอข้อมูลจากเว็บ จะเกิด **request** และ **response** หนึ่งคู่

```text
Client (Python)                                Server (air4thai.pcd.go.th)
   │  GET /services/getNewAQI_JSON.php  ──────────►
   │  Header: User-Agent, Accept
   │                                    ◄──────────  200 OK
   │                                                Header: Content-Type: application/json
   │                                                Body:   {"stations": [...]}
```

| องค์ประกอบ | ความหมาย | ตัวอย่าง |
|---|---|---|
| **method** | การกระทำ | `GET` ขอข้อมูล · `POST` ส่งข้อมูล |
| **URL** | ที่อยู่ + พารามิเตอร์ (query string) | `https://example.org/api?station=02t&date=2026-10-01` |
| **header** | ข้อมูลกำกับ | `User-Agent`, `Content-Type`, `Authorization` |
| **status code** | ผลลัพธ์ | 200 สำเร็จ · 404 ไม่พบ · 429 ขอถี่เกินไป · 5xx server มีปัญหา |
| **body** | เนื้อหา | JSON, HTML, CSV |

| กลุ่ม status code | ความหมาย | script ควรทำอะไร |
|---|---|---|
| 2xx | สำเร็จ | ประมวลผลต่อ |
| 4xx | ฝั่งเราผิด (URL ผิด ไม่มีสิทธิ์ ขอถี่เกิน) | หยุด แก้โค้ด ยกเว้น 429 ให้รอแล้วลองใหม่ |
| 5xx | server ผิดพลาดชั่วคราว | รอแล้วลองใหม่ (retry) |

### ใช้ requests

```python
import requests

URL = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
r = requests.get(URL, timeout=30)

r.status_code                     # 200
r.headers.get("Content-Type")     # ชนิดของ body
r.text[:200]                      # body เป็นข้อความ
data = r.json()                   # แปลง body เป็น dict/list ของ Python
```

พารามิเตอร์ใน URL ให้ส่งผ่าน `params=` ไม่ต้องต่อ string เอง requests จะ encode ให้ถูกต้อง

```python
r = requests.get("https://example.org/api", params={"station": "02t", "date": "2026-10-01"}, timeout=30)
r.url      # https://example.org/api?station=02t&date=2026-10-01
```

## 3. JSON และการตรวจ key

**JSON** ประกอบด้วย object (`{}` → `dict`), array (`[]` → `list`), string, number, `true/false`, `null` (→ `None`) และซ้อนกันได้หลายชั้น

### ตรวจโครงสร้างก่อนเชื่อเอกสาร

เอกสารนี้ หรือคำตอบจาก AI อาจบอกชื่อ key ผิด หรือ key อาจเปลี่ยนไปแล้ว **ให้ดูจาก response จริงเสมอ**

```python
data = r.json()
type(data)                        # dict
list(data.keys())                 # key ระดับบนสุด
st = data["stations"]
len(st), type(st[0])              # จำนวนสถานี, dict
list(st[0].keys())                # key ของแต่ละสถานี
```

ฟังก์ชันช่วยพิมพ์โครงสร้างซ้อนชั้น

```python
def show_keys(obj, prefix="", depth=3):
    """พิมพ์ path ของ key และชนิดค่า ไม่เกิน depth ชั้น"""
    if depth == 0:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            print(f"{prefix}{k}: {type(v).__name__}")
            show_keys(v, prefix + "  ", depth - 1)
    elif isinstance(obj, list) and obj:
        show_keys(obj[0], prefix + "[0] ", depth - 1)

show_keys(data["stations"][0])
```

ณ เวลาที่เขียนเอกสาร (ต.ค. 2569) แต่ละสถานีมี key `stationID`, `nameTH`, `nameEN`, `areaTH`, `areaEN`, `stationType`, `lat`, `long`, `forecast` และ `AQILast` ซึ่งซ้อน `date` (เช่น `"2026-10-23"`), `time` (เช่น `"03:00"`) และค่ามลพิษ `PM25`, `PM10`, `O3`, `CO`, `NO2`, `SO2` ไว้อีกชั้น โดยแต่ละชนิดมี `value` (ความเข้มข้น), `aqi` และ `color_id` **ให้ตรวจกับ response จริงก่อนใช้** เพราะโครงสร้างเปลี่ยนได้ และสังเกตว่า

- ตัวเลขทั้งหมดถูกส่งมาเป็น string เช่น `"8.0506237"`, `"9.9"`
- ค่าหายถูกแทนด้วย `"-1"` ไม่ใช่ `null` (ถ้าไม่แปลง `AVG()` จะนำ -1 ไปเฉลี่ยด้วย)
- มีทั้ง `value` (ความเข้มข้น µg/m³) และ `aqi` (ดัชนี) คำถามของเราใช้ `value`
- `areaTH` มีจังหวัดอยู่หลังเครื่องหมายจุลภาคตัวสุดท้าย เช่น `"ต.ปากน้ำ อ.เมือง, กระบี่"` และกรุงเทพฯ เขียนว่า `"กรุงเทพฯ"`

> **SSL:** URL `http://` ถูก redirect ไป `https://` และ (ณ ต.ค. 2569) server ส่ง certificate chain ไม่ครบ requests จึงอาจแจ้ง `SSLError: CERTIFICATE_VERIFY_FAILED` วิธีแก้ที่ปลอดภัยคือให้ Python ใช้ certificate store ของระบบปฏิบัติการด้วย `truststore` (`import truststore; truststore.inject_into_ssl()`) ห้ามแก้ด้วย `verify=False`

### ทำไมเก็บข้อมูลดิบไว้ก่อน

| เก็บ raw JSON | แปลงทันทีแล้วเก็บแค่ตาราง |
|---|---|
| ถ้าพบภายหลังว่าแปลงผิด ประมวลผลใหม่ได้ | ข้อมูลที่ทิ้งไปเอาคืนไม่ได้ (ค่าปัจจุบันของเมื่อวานดึงซ้ำไม่ได้) |
| ตรวจย้อนได้ว่า server ส่งอะไรมาจริง | ไม่รู้ว่าความผิดพลาดมาจาก server หรือโค้ดเรา |
| ใช้พื้นที่มากกว่า | ประหยัดพื้นที่ |

หลักการ: **ดึง (สัปดาห์ที่ 3) แยกจาก โหลด/แปลง (สัปดาห์ที่ 4)** script ดึงข้อมูลทำหน้าที่เดียวคือบันทึก response ให้ครบและถูกต้อง ชื่อไฟล์มี timestamp เช่น `data/raw/air4thai_20261023T140500.json` เพื่อไม่ทับไฟล์เดิมและรู้ว่าดึงเมื่อไร

## 4. ดึงข้อมูลอย่างสุภาพ (polite scraping)

server ของหน่วยงานรัฐให้บริการทุกคน ถ้า script ของเรายิงถี่เกินไป อาจทำให้คนอื่นใช้ไม่ได้ หรือเราถูกบล็อก

| หลักปฏิบัติ | ทำอย่างไร |
|---|---|
| **เคารพความถี่การอัปเดต** | Air4Thai อัปเดตรายชั่วโมง ดึงชั่วโมงละครั้งพอ ไม่ต้องดึงทุกนาที |
| **เว้นระยะเมื่อดึงหลายหน้า** | `time.sleep(1)` ถึง `time.sleep(5)` ระหว่าง request |
| **ระบุตัวตน** | ตั้ง header `User-Agent` บอกชื่อโครงการและช่องทางติดต่อ |
| **ตรวจ `robots.txt`** | ดูว่าเว็บไซต์อนุญาตให้โปรแกรมเข้าถึง path ใด |
| **อ่านเงื่อนไขการใช้งาน** | ข้อมูลเปิดหรือไม่ อ้างอิงอย่างไร นำไปเผยแพร่ต่อได้หรือไม่ |
| **ใช้ API ก่อน scrape** | API ออกแบบมาให้โปรแกรมใช้ เสถียรกว่าการแกะ HTML |

```python
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url("http://air4thai.pcd.go.th/robots.txt")
rp.read()
rp.can_fetch("pm25-explorer", URL)    # True = อนุญาต (ถ้าไม่มีไฟล์ robots.txt จะได้ True)
```

> `robots.txt` เป็นข้อตกลง ไม่ใช่กลไกป้องกัน การที่โค้ดเข้าถึงได้ไม่ได้แปลว่าได้รับอนุญาต เรื่องนี้เกี่ยวกับ CLO6 ด้วย

## 5. Timeout, retry และ logging

### Timeout

ถ้าไม่ใส่ `timeout` requests จะรอได้ไม่สิ้นสุด script ที่ตั้งเวลารันทุกชั่วโมงอาจค้างซ้อนกันหลายตัว

```python
r = requests.get(URL, timeout=(10, 60))   # (เวลารอเชื่อมต่อ, เวลารออ่านข้อมูล) หน่วยวินาที
```

### Retry แบบรอนานขึ้นเรื่อย ๆ (backoff)

ข้อผิดพลาดชั่วคราว (เครือข่ายหลุด, 5xx, 429) มักหายเองถ้ารอสักครู่ ส่วนข้อผิดพลาดถาวร (404, URL ผิด) ลองซ้ำก็ไม่หาย

```python
import time

RETRY_STATUS = {429, 500, 502, 503, 504}

def get_with_retry(url, retries=3, wait=5):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=(10, 60))
        except (requests.ConnectionError, requests.Timeout):
            pass                          # เครือข่ายมีปัญหา → ลองใหม่
        else:
            if r.status_code not in RETRY_STATUS:
                r.raise_for_status()      # 404 ฯลฯ → raise ทันที ไม่ลองซ้ำ
                return r
        if attempt < retries:
            time.sleep(wait * attempt)    # รอ 5, 10, ... วินาที
    raise RuntimeError(f"ล้มเหลวครบ {retries} ครั้ง")
```

> **เสริม:** requests รองรับ retry ในตัวผ่าน `HTTPAdapter(max_retries=Retry(...))` จาก `urllib3` ใช้ได้เมื่อเข้าใจหลักการข้างบนแล้ว

### Logging แทน print

script ที่รันอัตโนมัติไม่มีใครนั่งดูหน้าจอ ต้องเขียนบันทึกลงไฟล์ เพื่อย้อนดูได้ว่าแต่ละรอบสำเร็จหรือล้มเหลวเพราะอะไร

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("data/raw/fetch.log", encoding="utf-8")],
)
log = logging.getLogger("fetch")

log.info("ดึงข้อมูลสำเร็จ %d สถานี", 180)
log.warning("ครั้งที่ %d ล้มเหลว: %s", 1, "timeout")
```

| ระดับ | ใช้เมื่อ |
|---|---|
| `INFO` | เหตุการณ์ปกติ เช่น บันทึกไฟล์แล้ว |
| `WARNING` | ผิดปกติแต่ยังทำงานต่อได้ เช่น retry |
| `ERROR` | ทำงานไม่สำเร็จ |

## 6. ความลับใน `.env`

Air4Thai ไม่ต้องใช้ API key แต่แหล่งข้อมูลอื่นหลายแห่งต้องใช้ ห้ามเขียน key ลงในโค้ด เพราะเมื่อ push แล้ว key จะอยู่ในประวัติ Git ตลอดไป (ดูสัปดาห์ที่ 1)

```text
# .env  (อยู่ใน .gitignore แล้วตั้งแต่สัปดาห์ที่ 1 ห้าม commit)
API_KEY=xxxxxxxxxxxxxxxx
```

```text
# .env.example  (commit ได้ บอกคนอื่นว่าต้องตั้งค่าอะไร)
API_KEY=
```

อ่านค่าใน Python ด้วย `python-dotenv` (ติดตั้งเพิ่ม: `conda install -c conda-forge python-dotenv`)

```python
import os
from dotenv import load_dotenv

load_dotenv()                       # อ่าน .env ในโฟลเดอร์ปัจจุบันหรือโฟลเดอร์แม่
api_key = os.environ.get("API_KEY")
if not api_key:
    raise SystemExit("ไม่พบ API_KEY ใน .env")
```

ห้าม `log` หรือ `print` ค่า key และระวัง URL ที่มี key ใน query string เพราะอาจถูกบันทึกลง log

## 7. (เสริม) ดึงข้อมูลจากหน้าเว็บด้วย BeautifulSoup

ถ้าข้อมูลที่ต้องการไม่มี API เช่น ตารางรายชื่อสถานีบนหน้าเว็บ ใช้ BeautifulSoup แกะ HTML ได้ แต่หน้าเว็บเปลี่ยนรูปแบบบ่อย ทำให้โค้ดเสียง่ายกว่า API

```python
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "pm25-explorer/0.1 (student project)"}
page_url = "https://example.org/stations.html"      # แทนด้วย URL ของหน้าที่ต้องการ
html = requests.get(page_url, headers=HEADERS, timeout=30).text
soup = BeautifulSoup(html, "html.parser")

rows = []
for tr in soup.select("table tr"):
    cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
    if cells:
        rows.append(cells)
rows[:3]          # ตรวจว่าได้หัวตารางและข้อมูลถูกต้อง
```

ตรวจ `robots.txt` และเงื่อนไขการใช้งานของหน้านั้นก่อน และเก็บ HTML ดิบไว้ใน `data/raw/` ตามหลักเดียวกับ JSON

## 8. โครงสร้างของ `src/fetch_air4thai.py`

```text
1. ตั้งค่า: URL, โฟลเดอร์ปลายทาง, User-Agent, logging
2. ดึงข้อมูลด้วย timeout + retry
3. ตรวจว่า response เป็น JSON และมีรายการสถานี (ไม่ว่าง)
4. บันทึก body ดิบลง data/raw/air4thai_<YYYYMMDDTHHMMSS>.json
5. log จำนวนสถานี ชื่อไฟล์ และจบด้วย exit code 0 (สำเร็จ) หรือ 1 (ล้มเหลว)
```

script นี้ต้อง **รันซ้ำได้** ทุกครั้งที่รันจะได้ไฟล์ใหม่หนึ่งไฟล์ และไม่ทับไฟล์เดิม โค้ดเต็มอยู่ในคู่มือปฏิบัติการ

## สรุป

- HTTP คือ request/response ดู status code และ Content-Type ก่อนประมวลผล body
- ตรวจ key ของ JSON จริงทุกครั้ง อย่าเชื่อเอกสารหรือ AI
- เก็บ raw response พร้อม timestamp แยกจากขั้นแปลงรูป
- ดึงอย่างสุภาพ: ความถี่เหมาะสม ระบุ User-Agent เคารพ `robots.txt` และเงื่อนไขการใช้งาน
- ใส่ timeout ทุกครั้ง retry เฉพาะข้อผิดพลาดชั่วคราว และใช้ logging
- ความลับอยู่ใน `.env` ที่ไม่ถูก commit

## คำถามทบทวน

1. status code 404, 429 และ 503 ต่างกันอย่างไร script ควรตอบสนองต่อแต่ละแบบอย่างไร
2. ทำไม script ที่ไม่มี `timeout` จึงเป็นปัญหาเมื่อตั้งเวลารันทุกชั่วโมง
3. ถ้าวันหนึ่ง Air4Thai เปลี่ยนชื่อ key จาก `stations` เป็นชื่ออื่น การเก็บ raw JSON ช่วยอะไร
4. การดึงข้อมูลทุก 1 นาทีจาก endpoint ที่อัปเดตรายชั่วโมงมีผลเสียอะไรบ้าง
5. ทำไมไม่ควรเขียน API key ไว้ใน notebook แม้จะลบออกก่อน commit

## อ่านเพิ่มเติม

- เอกสาร requests: Quickstart และ Advanced Usage (Timeouts) — <https://requests.readthedocs.io/>
- MDN Web Docs: *An overview of HTTP* และ *HTTP response status codes* — <https://developer.mozilla.org/>
- เอกสาร Beautiful Soup — <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>
- เอกสาร Python: `logging` HOWTO และ `urllib.robotparser`
- Air4Thai — <http://air4thai.pcd.go.th>

➡️ [คู่มือปฏิบัติการสัปดาห์ที่ 3](lab.md)
