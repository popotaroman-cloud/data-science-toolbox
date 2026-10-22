---
title: "สัปดาห์ที่ 14: สื่อสารข้อค้นพบและ reproducibility"
---

> **CLO:** CLO5 · **เครื่องมือหลัก:** Quarto, Streamlit, DuckDB (read-only + cache) · **เครื่องมือเสริม:** Power BI / Looker Studio
> **ผลงานที่เพิ่มในระบบ:** data story report `report/report.qmd` (15%) + แดชบอร์ด `app/app.py` แบบ drill-down 4 ระดับ (ประเทศ → ภาค → จังหวัด → สถานี) + ขั้นตอนรันซ้ำได้จาก fresh clone

## วัตถุประสงค์การเรียนรู้

เมื่อจบสัปดาห์นี้ ผู้เรียนสามารถ

1. เรียบเรียงข้อค้นพบเป็น data story ที่ตั้งต้นจากคำถามใน `questions.md` และบอกข้อค้นพบก่อนรายละเอียด
2. เขียนรายงาน Quarto ที่มี YAML header, code chunk และกราฟ Plotly แล้ว render เป็น HTML ได้
3. สร้างแดชบอร์ด Streamlit ที่เปิด DuckDB แบบ read-only, ใช้ cache อย่างถูกต้อง และ drill-down ด้วย `session_state`
4. ทำให้โครงการรันซ้ำได้จาก fresh clone ด้วยไฟล์สภาพแวดล้อม script รัน และ path แบบ relative

---

## 1. Data storytelling: จาก notebook สู่เรื่องเล่า

สัปดาห์ที่ 9–13 ผู้เรียนมีกราฟหลายสิบรูปใน notebook แต่ผู้อ่านรายงานไม่ต้องการเห็น *ทุกอย่างที่เราทำ* เขาต้องการรู้ *สิ่งที่เราพบ* และ *เชื่อได้แค่ไหน*

| Notebook (สำรวจ) | Report (สื่อสาร) |
|---|---|
| เรียงตามลำดับที่เราทำ | เรียงตามคำถามของผู้อ่าน |
| มีทุกกราฟ รวมถึงทางตัน | เลือกเฉพาะกราฟที่ตอบคำถาม |
| ผู้อ่านคือตัวเราเอง | ผู้อ่านคือคนที่ไม่ได้อยู่ในห้อง |
| โค้ดเด่น | ข้อค้นพบเด่น โค้ดซ่อนไว้ |

### โครงสร้างที่แนะนำ

```text
1. สรุปสำหรับผู้บริหาร (3–5 bullet: ข้อค้นพบหลักของแต่ละคำถาม)
2. ข้อมูลและวิธีการ (แหล่งข้อมูล ช่วงเวลา จำนวนสถานี การทำความสะอาด — สั้น ๆ)
3. คำถามที่ 1 → ข้อค้นพบ → หลักฐาน (กราฟ/สถิติ) → ความมั่นใจ
4. คำถามที่ 2 → ...
5. ข้อจำกัด
6. ข้อเสนอแนะ / คำถามต่อไป
ภาคผนวก: data dictionary, การใช้ AI
```

### หลักสามข้อ

1. **ข้อค้นพบมาก่อน (finding first):** หัวข้อของแต่ละส่วนเป็นประโยคที่บอกผล เช่น *"ภาคเหนือมีวันเกินมาตรฐานมากกว่าภาคอื่นราว 3 เท่า โดยกระจุกในเดือน มี.ค.–เม.ย."* แทน *"ผลการวิเคราะห์รายภาค"* ชื่อกราฟก็ควรเป็นประโยคข้อค้นพบเช่นกัน
2. **เลือกกราฟอย่างตั้งใจ:** หนึ่งกราฟหนึ่งประเด็น ใช้หลักจากสัปดาห์ที่ 9 (เปรียบเทียบ → bar, แนวโน้ม → line, ความสัมพันธ์ → scatter, พื้นที่ → map) ใส่เส้นมาตรฐาน 37.5 µg/m³ (และ WHO 15 µg/m³ ถ้าเกี่ยวข้อง) เพื่อให้ตัวเลขมีบริบท
3. **บอกข้อจำกัดอย่างตรงไปตรงมา:** เช่น สถานีกระจุกในเมือง, ข้อมูลขาดหายช่วงใด (สัปดาห์ที่ 7), outlier ที่ยังไม่แน่ใจ (สัปดาห์ที่ 12), MAUP (สัปดาห์ที่ 13), ความสัมพันธ์ไม่ใช่เหตุและผล (สัปดาห์ที่ 11)

## 2. Quarto: รายงานที่สร้างจากโค้ด

**Quarto** แปลงไฟล์ `.qmd` (Markdown + code chunk) เป็น HTML, PDF หรือ Word โดยรันโค้ดจริงทุกครั้งที่ render ตัวเลขในรายงานจึงตรงกับข้อมูลเสมอ ไม่ต้องคัดลอกกราฟไปวาง

### YAML header

```yaml
---
title: "คุณภาพอากาศ PM2.5 ของประเทศไทย: ใคร เมื่อไร และที่ไหน"
author: "ชื่อ นามสกุล (รหัสนักศึกษา)"
date: today
lang: th
format:
  html:
    toc: true
    code-fold: true
    embed-resources: true
execute:
  echo: false
  warning: false
jupyter: python3
---
```

| ตัวเลือก | ความหมาย |
|---|---|
| `execute: echo: false` | ซ่อนโค้ดทั้งรายงาน แสดงเฉพาะผล (เหมาะกับผู้อ่านทั่วไป) |
| `code-fold: true` | ถ้าเปิด echo ให้โค้ดพับไว้ กดดูได้ |
| `embed-resources: true` | รวม CSS/JS/รูป (รวม Plotly) ไว้ในไฟล์ HTML ไฟล์เดียว ส่งต่อได้ง่าย |
| `jupyter: python3` | ใช้ kernel Python ควรรันใน environment ของโครงการ |

### Code chunk

````markdown
```{{python}}
#| label: fig-region
#| fig-cap: "ภาคเหนือมีสัดส่วนวันเกินมาตรฐานสูงที่สุด"
import duckdb, plotly.express as px
con = duckdb.connect("../data/pm25.duckdb", read_only=True)
df = con.sql("SELECT ... FROM daily_pm25_clean ...").df()
fig = px.bar(df, x="region", y="share_over_std")
fig
```
````

- ตัวเลือกของ chunk เขียนด้วย `#|` บรรทัดแรก ๆ เช่น `echo: true` เพื่อแสดงโค้ดเฉพาะ chunk นั้น
- **กราฟ Plotly ฝังได้ทันที** เพียงให้ object `fig` เป็นค่าสุดท้ายของ chunk ในรายงาน HTML กราฟยัง interactive อยู่
- ตัวเลขในประโยคใช้ inline code ได้ เช่น `` `{{python}} n_stations` `` (Quarto 1.4 ขึ้นไป) ตัวเลขในข้อความจึงไม่ล้าสมัย
- Quarto รันโค้ดโดยใช้โฟลเดอร์ของไฟล์ `.qmd` เป็น working directory ไฟล์ `report/report.qmd` จึงอ้าง `../data/pm25.duckdb`

```bash
quarto render report/report.qmd      # ได้ report/report.html
quarto preview report/report.qmd     # เปิด browser และ render ใหม่เมื่อบันทึก
```

> **ทางเลือกที่แนะนำ:** ย้ายฟังก์ชัน query ที่ใช้ทั้งในรายงานและแดชบอร์ดไปไว้ใน `src/queries.py` แล้ว import มาใช้ทั้งสองที่ เพื่อให้ตัวเลขในรายงานและแดชบอร์ดตรงกัน

## 3. Streamlit: แดชบอร์ดจาก Python ล้วน

**Streamlit** รัน script ทั้งไฟล์ใหม่ตั้งแต่บรรทัดแรก *ทุกครั้ง* ที่ผู้ใช้ขยับ widget แนวคิดนี้ง่าย แต่ทำให้ต้องเข้าใจ cache และ `session_state`

```bash
streamlit run app/app.py
```

### Widget พื้นฐาน

| Widget | ใช้ทำอะไร |
|---|---|
| `st.selectbox`, `st.multiselect` | เลือกภาค จังหวัด สถานี |
| `st.date_input` | เลือกช่วงวันที่ (ส่ง tuple 2 ค่าเมื่อเลือกเป็นช่วง) |
| `st.slider`, `st.radio` | เลือกเกณฑ์ เช่น มาตรฐานไทย / WHO |
| `st.metric` | แสดงตัวเลขสรุป (KPI) |
| `st.plotly_chart(fig)` | แสดงกราฟ Plotly (ค่าเริ่มต้นขยายเต็มความกว้าง) |
| `st.sidebar.*`, `st.columns`, `st.tabs` | จัดวาง layout |

### เปิด DuckDB แบบ read-only และใช้ cache

```python
from pathlib import Path
import duckdb, streamlit as st

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "pm25.duckdb"

@st.cache_resource                       # สร้าง connection ครั้งเดียว ใช้ร่วมกันทุก session
def get_con():
    return duckdb.connect(str(DB_PATH), read_only=True)

@st.cache_data(ttl=600)                  # cache ผล query (DataFrame) 10 นาที
def query(sql: str, params: tuple = ()):
    return get_con().cursor().execute(sql, list(params)).df()
```

| | `st.cache_resource` | `st.cache_data` |
|---|---|---|
| เก็บอะไร | object ที่ใช้ร่วมกัน เช่น connection, โมเดล | ผลลัพธ์ที่ serialize ได้ เช่น DataFrame |
| ได้ค่าแบบใด | object ตัวเดิม (shared) | สำเนาใหม่ทุกครั้ง แก้ไขได้ไม่กระทบ cache |
| key ของ cache | argument ของฟังก์ชัน | argument ของฟังก์ชัน (`sql`, `params`) |

เหตุผลของการออกแบบ

- **`read_only=True`** แดชบอร์ดมีหน้าที่อ่านอย่างเดียว ป้องกันการเขียนทับข้อมูลโดยไม่ตั้งใจ และหลาย process อ่านไฟล์เดียวกันพร้อมกันได้ (แต่ขณะที่ app เปิดอยู่ script ที่ต้อง *เขียน* ลงไฟล์จะเปิดไม่ได้ ต้องปิด app ก่อนรัน pipeline)
- **`.cursor()`** Streamlit รันแต่ละ session ใน thread ต่างกัน connection ของ DuckDB ไม่ควรใช้ข้าม thread โดยตรง cursor สร้าง connection ย่อยที่ปลอดภัยกว่า
- **ใช้ `?` parameter** แทนการต่อ string ใน SQL เพื่อป้องกัน SQL injection และให้ cache key ชัดเจน

### Drill-down ด้วย `session_state`

`st.session_state` เป็น dictionary ที่อยู่รอดข้ามการ rerun ของ session เดียวกัน จึงใช้จำว่าผู้ใช้อยู่ระดับใดของลำดับชั้น ภาค → จังหวัด → สถานี (ลำดับชั้นเดียวกับ treemap สัปดาห์ที่ 13)

```python
ss = st.session_state
for k in ("region", "province", "station"):
    ss.setdefault(k, None)

def drill(level, widget_key):           # callback: รันก่อน script รอบใหม่
    ss[level] = ss[widget_key]
    ss[widget_key] = None

def go_to(depth):                       # 0 = ประเทศ, 1 = ภาค, 2 = จังหวัด
    for k in ("region", "province", "station")[depth:]:
        ss[k] = None
```

| ระดับ | สถานะ | แสดงอะไร (ตัวอย่าง) |
|---|---|---|
| 1 ประเทศ | ทุกค่าเป็น `None` | KPI ทั้งประเทศ, bar รายภาค, แผนที่สถานี |
| 2 ภาค | `region` มีค่า | bar รายจังหวัดในภาคนั้น, line รายเดือน |
| 3 จังหวัด | `province` มีค่า | สถานีในจังหวัด, time series เทียบสถานี |
| 4 สถานี | `station` มีค่า | time series รายวัน, วันเกินมาตรฐาน, outlier flags, cluster |

โค้ดเต็มอยู่ในคู่มือปฏิบัติการ (เสริม) Streamlit ≥ 1.35 รองรับ `st.plotly_chart(fig, on_select="rerun")` ให้คลิกที่แท่งกราฟเพื่อ drill-down ได้ แต่ให้ทำแบบ selectbox ให้ทำงานได้ก่อน

## 4. Reproducibility: คนอื่นรันได้ไหม

**Reproducibility** หมายถึงคนอื่น (หรือเราในอีก 6 เดือน) ได้ผลเดียวกันจากโค้ดและข้อมูลเดียวกัน ในวันนำเสนอสัปดาห์ที่ 15 เพื่อนจะ **clone repo ใหม่แล้วรันตาม README** ถ้ารันไม่ได้ถือว่าระบบยังไม่เสร็จ

| องค์ประกอบ | สิ่งที่ต้องมี |
|---|---|
| สภาพแวดล้อม | `environment.yml` (หรือ `pyproject.toml` + `uv.lock`) ที่มีไลบรารีครบตามที่ import จริง ระบุเวอร์ชันหลัก |
| ขั้นตอนรัน | script เดียว เช่น `run_all.py` หรือ `Makefile` หรืออย่างน้อยขั้นตอนใน README ที่คัดลอกไปรันได้ทันที |
| path | ไม่มี path แบบ absolute เช่น `C:\Users\me\...` ใช้ `Path(__file__).resolve().parents[1]` หรือ path relative จาก root |
| ข้อมูล | ไม่ commit `data/` แต่บอกวิธีสร้างข้อมูลใหม่ (รัน pipeline) และทางเลือกเมื่อ API ล่ม (ไฟล์ตัวอย่างจากผู้สอน) |
| ความลับ | อ่านจาก `.env` และมี `.env.example` ที่ไม่มีค่าจริง |
| ความสุ่ม | ตั้ง `random_state` / `Faker.seed` ทุกที่ |
| เอกสาร | README บอก: โครงการนี้คืออะไร ติดตั้ง รัน ผลลัพธ์อยู่ที่ไหน ข้อจำกัด |

### Fresh-clone test

```bash
cd /tmp                                   # หรือโฟลเดอร์ว่างใดก็ได้
git clone https://github.com/<username>/pm25-explorer.git
cd pm25-explorer
conda env create -f environment.yml -n pm25-test
conda activate pm25-test
python run_all.py                         # สร้าง data/pm25.duckdb ใหม่จากต้นทาง
quarto render report/report.qmd
streamlit run app/app.py
```

ถ้าขั้นใดพัง ให้แก้ที่ repo ไม่ใช่แก้บนเครื่อง จนรันผ่านทั้งหมด ข้อผิดพลาดที่พบบ่อยคือ ลืมเพิ่มไลบรารีใน `environment.yml`, path absolute, ไฟล์ที่มีเฉพาะบนเครื่องเรา และลำดับการรัน script

## 5. Power BI / Looker Studio (เสริม)

เครื่องมือ BI แบบลากวางสร้างแดชบอร์ดได้เร็ว และองค์กรจำนวนมากใช้อยู่ ลองส่งออกข้อมูลไปเปรียบเทียบได้

```python
con.execute("COPY (SELECT * FROM daily_pm25_clean JOIN stations USING (station_id)) "
            "TO 'outputs/daily_pm25_clean.csv' (HEADER)")
```

| | Streamlit + DuckDB | Power BI / Looker Studio |
|---|---|---|
| สร้างแดชบอร์ดแรก | ต้องเขียนโค้ด | เร็วมาก ลากวาง |
| version control / code review | ทำได้เต็มที่ด้วย Git | จำกัด (ไฟล์ binary หรือบนคลาวด์) |
| ทำซ้ำได้ (reproducible) | สูง ถ้าทำตามหัวข้อ 4 | ขึ้นกับการตั้งค่าบนแพลตฟอร์ม |
| ปรับแต่ง/วิเคราะห์ขั้นสูง | ไม่จำกัด (Python ทั้งหมด) | จำกัดตามฟีเจอร์ของเครื่องมือ |
| ค่าใช้จ่าย / บัญชี | ฟรี | อาจต้องมีบัญชีหรือ license |

## 6. เกณฑ์ประเมิน data story report (15%)

| เกณฑ์ | คะแนน | ดีเยี่ยม | ต้องปรับปรุง |
|---|---|---|---|
| โครงเรื่องตามคำถาม | 3 | ทุกส่วนผูกกับคำถามใน `questions.md` มีบทสรุปข้อค้นพบตอนต้น | เรียงตามลำดับการทำงาน ไม่ชัดว่าตอบคำถามใด |
| ข้อค้นพบและหลักฐาน | 4 | หัวข้อ/ชื่อกราฟเป็นประโยคข้อค้นพบ มีหลักฐานทั้งภาพและสถิติ ใช้ภาษาตามระดับความมั่นใจ | บรรยายกราฟโดยไม่สรุป หรือสรุปเกินหลักฐาน (เช่น อ้างเหตุและผล) |
| การเลือกและออกแบบกราฟ | 3 | ประเภทกราฟเหมาะกับประเด็น มีหน่วย เส้นมาตรฐาน และป้ายภาษาไทยอ่านง่าย | กราฟซ้ำซ้อน ไม่มีหน่วย หรืออ่านยาก |
| ข้อจำกัดและจริยธรรม | 2 | ระบุข้อจำกัดของข้อมูลและวิธีการ ผลต่อข้อสรุป และประเด็น PDPA ที่เกี่ยวข้อง | ไม่มีหรือมีแบบผิวเผิน |
| Reproducibility | 2 | `quarto render` จาก fresh clone ผ่าน ไม่มี path absolute ตัวเลขในข้อความมาจากโค้ด | render ไม่ผ่านหรือมีตัวเลขพิมพ์เอง |
| ความชัดเจนของภาษาและการอ้างอิง | 1 | กระชับ อ้างแหล่งข้อมูลและสัญญาอนุญาตครบ มีภาคผนวกการใช้ AI | อ้างอิงไม่ครบ |
| **รวม** | **15** | | |

## สรุป

- Data story เรียงตามคำถาม บอกข้อค้นพบก่อน เลือกกราฟอย่างตั้งใจ และบอกข้อจำกัด
- Quarto สร้างรายงานจากโค้ดจริง: YAML header, chunk options `#|`, `echo: false`, ฝัง Plotly ได้ และ render เป็น HTML
- Streamlit รัน script ใหม่ทุกครั้งที่มีการโต้ตอบ: ใช้ `cache_resource` กับ connection แบบ `read_only=True`, `cache_data` กับผล query และ `session_state` กับระดับ drill-down
- Reproducibility พิสูจน์ด้วย fresh-clone test: environment file + script รัน + path relative + README

## คำถามทบทวน

1. หัวข้อ "ผลการวิเคราะห์ตามฤดูกาล" ควรเขียนใหม่ให้เป็น finding first อย่างไร
2. ถ้าใช้ `st.cache_data` กับฟังก์ชันที่คืน DuckDB connection จะเกิดปัญหาอะไร
3. ทำไมแดชบอร์ดจึงควรเปิด DuckDB แบบ `read_only=True` และผลข้างเคียงต่อการรัน pipeline คืออะไร
4. ถ้าไม่ใช้ `session_state` ระดับ drill-down จะหายไปเมื่อใด เพราะอะไร
5. ยกตัวอย่าง 3 สิ่งที่ทำให้โครงการ "รันได้บนเครื่องผม" แต่ไม่ผ่าน fresh-clone test

## อ่านเพิ่มเติม

- Knaflic, C. N. (2015). *Storytelling with Data*. Wiley.
- Quarto Guide: *Computations: Using Python*, *HTML Basics*, *Execution Options* — <https://quarto.org/docs/guide/>
- Streamlit Docs: *Caching overview*, *Session State* — <https://docs.streamlit.io/>
- DuckDB Docs: *Python API — Multiple Python Threads* และ *Concurrency*
- The Turing Way: *Guide for Reproducible Research* — <https://book.the-turing-way.org/>

➡️ [คู่มือปฏิบัติการสัปดาห์ที่ 14](lab.md)
