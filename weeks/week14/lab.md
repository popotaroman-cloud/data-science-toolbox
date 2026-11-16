---
title: "ปฏิบัติการสัปดาห์ที่ 14: รายงาน Quarto, แดชบอร์ด Streamlit และ fresh-clone test"
---

> **เวลา:** 2 ชั่วโมง (+ งานต่อนอกเวลา) · **CLO:** CLO5
> **ผลงานที่ต้องส่ง:** PR ที่มี `report/report.qmd`, `app/app.py`, `run_all.py` และ README ที่มีขั้นตอนรัน + ไฟล์ `report.html` ที่ render แล้วส่งในระบบส่งงาน (data story report 15%) + ผล fresh-clone test จากเพื่อน

## สิ่งที่ต้องเตรียม

- `data/pm25.duckdb` ที่มี `stations`, `measurements`, `daily_pm25_clean`, `station_clusters`, `daily_outlier_flags` (สัปดาห์ที่ 4–12)
- กราฟ Plotly ที่ดีที่สุดจากสัปดาห์ที่ 10–13 และข้อค้นพบ 1 ประโยคต่อคำถาม (งานศึกษาด้วยตนเองสัปดาห์ที่ 13)
- Quarto CLI ติดตั้งแล้ว

```bash
quarto check
python -c "import streamlit, duckdb; print(streamlit.__version__, duckdb.__version__)"
```

---

## ขั้นที่ 1: สร้าง branch และโครงเรื่อง

```bash
git switch main && git pull
git switch -c week14-report-dashboard
mkdir report
```

เพิ่มใน `.gitignore`

```text
report/report.html
report/report_files/
outputs/
```

เขียนตารางนี้ใน `questions.md` (หรือกระดาษ) ก่อนเขียนรายงาน ถ้าเติมช่อง "ข้อค้นพบ" ไม่ได้ แปลว่ายังไม่พร้อมเขียนส่วนนั้น

| คำถาม | ข้อค้นพบ (1 ประโยค) | หลักฐาน (กราฟ/สถิติ) | ความมั่นใจ / ข้อจำกัด |
|---|---|---|---|
| Q1 ... | ... | ... | ... |

## ขั้นที่ 2: เขียน `report/report.qmd`

````markdown
---
title: "คุณภาพอากาศ PM2.5 ของประเทศไทย: <ข้อค้นพบหลักสั้น ๆ>"
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

```{{python}}
#| label: setup
import duckdb, plotly.express as px
con = duckdb.connect("../data/pm25.duckdb", read_only=True)
n_st = con.execute("SELECT count(DISTINCT station_id) FROM daily_pm25_clean").fetchone()[0]
d0, d1 = con.execute("SELECT min(date), max(date) FROM daily_pm25_clean").fetchone()
```

## สรุปข้อค้นพบ

- ข้อค้นพบที่ 1 ...
- ข้อค้นพบที่ 2 ...

## ข้อมูลและวิธีการ

ข้อมูล PM2.5 รายวันจาก Air4Thai (กรมควบคุมมลพิษ) จำนวน `{{python}} n_st` สถานี
ช่วง `{{python}} str(d0)` ถึง `{{python}} str(d1)` ...

## ภาคเหนือมีวันเกินมาตรฐานมากที่สุด โดยกระจุกในเดือน มี.ค.–เม.ย.

```{{python}}
#| label: fig-region
#| fig-cap: "สัดส่วนวันที่ค่าเฉลี่ย 24 ชม. เกิน 37.5 µg/m³ แยกตามภาค"
df = con.sql("""
    SELECT s.region, avg((d.pm25_mean > 37.5)::INT) AS share_over
    FROM daily_pm25_clean d JOIN stations s USING (station_id)
    WHERE d.is_complete
    GROUP BY s.region ORDER BY share_over DESC
""").df()
fig = px.bar(df, x="region", y="share_over",
             labels={"region": "ภาค", "share_over": "สัดส่วนวันเกินมาตรฐาน"})
fig.update_yaxes(tickformat=".0%")
fig
```

สถิติสนับสนุน ... (ผลทดสอบจากสัปดาห์ที่ 11)

## ข้อจำกัด

- ...

## ภาคผนวก: การใช้ AI

สรุปจาก `AI_USAGE.md` ...
````

render และเปิดดู

```bash
quarto render report/report.qmd
```

เขียนให้ครบทุกคำถาม เลือกกราฟจาก notebook สัปดาห์ที่ 9–13 มาเฉพาะที่ตอบคำถาม เปลี่ยนชื่อหัวข้อให้เป็นประโยคข้อค้นพบ และตรวจตามเกณฑ์ 15 คะแนนในหัวข้อ 6 ของ[เอกสารประกอบการสอน](index.md)

## ขั้นที่ 3: สร้างแดชบอร์ด `app/app.py`

```python
"""PM2.5 Explorer: drill-down ประเทศ → ภาค → จังหวัด → สถานี"""
from pathlib import Path
import duckdb
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "pm25.duckdb"
STD_TH, STD_WHO = 37.5, 15
st.set_page_config(page_title="PM2.5 Explorer", layout="wide")

@st.cache_resource
def get_con():
    return duckdb.connect(str(DB_PATH), read_only=True)

@st.cache_data(ttl=600)
def query(sql, params=()):
    return get_con().cursor().execute(sql, list(params)).df()

@st.cache_data
def date_range():
    return get_con().cursor().execute("SELECT min(date), max(date) FROM daily_pm25_clean").fetchone()

# ---------- สถานะ drill-down ----------
ss = st.session_state
KEYS = ("region", "province", "station")
for k in KEYS:
    ss.setdefault(k, None)

def drill(level, widget_key):
    ss[level] = ss[widget_key]
    ss[widget_key] = None

def go_to(depth):
    for k in KEYS[depth:]:
        ss[k] = None

# ---------- ตัวกรอง ----------
dmin, dmax = date_range()
picked = st.sidebar.date_input("ช่วงวันที่", value=(dmin, dmax), min_value=dmin, max_value=dmax)
if len(picked) != 2:
    st.info("เลือกวันเริ่มต้นและวันสิ้นสุด")
    st.stop()
start, end = picked

cond, params = ["d.is_complete", "d.date BETWEEN ? AND ?"], [start, end]
for col, k in (("s.region", "region"), ("s.province", "province"), ("s.station_id", "station")):
    if ss[k] is not None:
        cond.append(f"{col} = ?")
        params.append(ss[k])
WHERE, P = " AND ".join(cond), tuple(params)
FROM = "FROM daily_pm25_clean d JOIN stations s USING (station_id)"
depth = sum(ss[k] is not None for k in KEYS)

# ---------- breadcrumb ----------
st.title("PM2.5 Explorer")
c = st.columns(4)
c[0].button("ประเทศไทย", on_click=go_to, args=(0,))
if ss.region:
    c[1].button(ss.region, on_click=go_to, args=(1,))
if ss.province:
    c[2].button(ss.province, on_click=go_to, args=(2,))
if ss.station:
    c[3].markdown(f"**{query('SELECT name_th FROM stations WHERE station_id = ?', (ss.station,)).iloc[0, 0]}**")

# ---------- KPI ----------
k = query(f"""SELECT avg(d.pm25_mean) AS mean, max(d.pm25_max) AS peak,
                     avg((d.pm25_mean > {STD_TH})::INT) AS share,
                     count(DISTINCT d.station_id) AS n_st {FROM} WHERE {WHERE}""", P).iloc[0]
m = st.columns(4)
m[0].metric("PM2.5 เฉลี่ยรายวัน (µg/m³)", f"{k['mean']:.1f}")
m[1].metric("ค่าสูงสุดรายชั่วโมง", f"{k['peak']:.0f}")
m[2].metric(f"วันเกิน {STD_TH}", f"{k['share']:.0%}")
m[3].metric("จำนวนสถานี", int(k["n_st"]))

# ---------- เนื้อหาตามระดับ ----------
left, right = st.columns(2)
trend = query(f"""SELECT date_trunc('month', d.date) AS month, avg(d.pm25_mean) AS pm25
                  {FROM} WHERE {WHERE} GROUP BY 1 ORDER BY 1""", P)
fig = px.line(trend, x="month", y="pm25", labels={"month": "เดือน", "pm25": "PM2.5 (µg/m³)"})
fig.add_hline(y=STD_TH, line_dash="dash", annotation_text="มาตรฐานไทย")
fig.add_hline(y=STD_WHO, line_dash="dot", annotation_text="WHO")
right.plotly_chart(fig)

if depth < 3:
    child, label, level = [("s.region", "ภาค", "region"), ("s.province", "จังหวัด", "province"),
                           ("s.station_id", "สถานี", "station")][depth]
    name = "any_value(s.name_th)" if level == "station" else child
    by = query(f"""SELECT {child} AS id, {name} AS name, avg(d.pm25_mean) AS pm25
                   {FROM} WHERE {WHERE} GROUP BY {child} ORDER BY pm25 DESC""", P)
    fig = px.bar(by, x="name", y="pm25", color="pm25", color_continuous_scale="YlOrRd",
                 labels={"name": label, "pm25": "PM2.5 เฉลี่ย (µg/m³)"})
    fig.add_hline(y=STD_TH, line_dash="dash")
    left.plotly_chart(fig)
    names = dict(zip(by["id"], by["name"]))
    left.selectbox(f"เลือก{label}เพื่อดูรายละเอียด", options=list(by["id"]), index=None,
                   format_func=names.get, key=f"pick_{level}",
                   on_change=drill, args=(level, f"pick_{level}"))
else:
    ts = query(f"SELECT d.date, d.pm25_mean {FROM} WHERE {WHERE} ORDER BY d.date", P)
    fig = px.line(ts, x="date", y="pm25_mean", labels={"date": "วันที่", "pm25_mean": "PM2.5 (µg/m³)"})
    fig.add_hline(y=STD_TH, line_dash="dash")
    left.plotly_chart(fig)
    flags = query("""SELECT date, pm25_mean, outlier_reason FROM daily_outlier_flags
                     WHERE station_id = ? AND date BETWEEN ? AND ? ORDER BY date""",
                  (ss.station, start, end))
    left.subheader("วันที่ถูกติดธง outlier (สัปดาห์ที่ 12)")
    left.dataframe(flags)

st.caption("ที่มา: Air4Thai กรมควบคุมมลพิษ · มาตรฐานไทย 37.5 µg/m³ (ค่าเฉลี่ย 24 ชม.) · WHO 2021: 15 µg/m³")
```

รัน

```bash
streamlit run app/app.py
```

ทดสอบ: เลือกภาค → จังหวัด → สถานี แล้วกด breadcrumb ย้อนกลับ เปลี่ยนช่วงวันที่ทุกระดับ ตัวเลขต้องเปลี่ยนตาม ถ้ามีเวลา เพิ่มแผนที่สถานีในระดับประเทศ/ภาค (`px.scatter_map` หรือ `px.scatter_mapbox` ขึ้นกับเวอร์ชัน Plotly) หรือ treemap จากสัปดาห์ที่ 13

> **อธิบายได้ทุกบรรทัด:** ถ้าใช้ AI ช่วยแก้ app ให้บันทึกใน `AI_USAGE.md` และตรวจว่าชื่อตาราง/คอลัมน์ตรงกับฐานข้อมูลจริง ในวันนำเสนอผู้สอนจะถามเรื่อง cache และ `session_state`

## ขั้นที่ 4: script รัน pipeline ทั้งหมด

สร้าง `run_all.py` ที่ root (ใช้ได้ทั้ง Windows/macOS/Linux) โดยต่อยอดจาก `src/run_pipeline.py` ของสัปดาห์ที่ 8 และเพิ่มขั้นตอนของสัปดาห์ที่ 12 ที่สร้างตาราง `station_clusters` และ `daily_outlier_flags` ถ้าแดชบอร์ดใช้ตารางเหล่านั้น

```python
"""รัน pipeline ทั้งหมดตามลำดับ: python run_all.py"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [                         # ลำดับเดียวกับ src/run_pipeline.py (สัปดาห์ที่ 8)
    "src/fetch_air4thai.py",
    "src/load_duckdb.py",
    "src/validate.py",
    "src/clean.py",
]
for step in STEPS:
    print(f"==> {step}")
    subprocess.run([sys.executable, str(ROOT / step)], check=True, cwd=ROOT)
print("เสร็จ: data/pm25.duckdb พร้อมใช้")
```

(เสริม) ผู้ที่ใช้ `make` เขียน `Makefile` แทนได้ เช่น target `data`, `report`, `app` แต่ต้องมีวิธีสำหรับ Windows ใน README ด้วย

เพิ่มใน `README.md` ของโครงการ

````markdown
## วิธีรัน
```bash
conda env create -f environment.yml && conda activate <ชื่อ env>
python run_all.py                    # ดึงข้อมูลและสร้าง data/pm25.duckdb (~xx นาที)
quarto render report/report.qmd      # รายงาน → report/report.html
streamlit run app/app.py             # แดชบอร์ด
```
ถ้า Air4Thai ใช้งานไม่ได้: วางไฟล์ตัวอย่างจากผู้สอนไว้ที่ `data/sample/` แล้ว ...
````

## ขั้นที่ 5: ตรวจ reproducibility ด้วยตนเอง

```bash
git grep -nE "[A-Za-z]:\\\\|/Users/|/home/"     # หา path absolute ที่หลงเหลือ
git grep -n "random_state\|seed"                # ตรวจว่าตั้ง seed แล้ว
```

ตรวจว่า `environment.yml` มีทุกไลบรารีที่ `import` จริง (เทียบกับ `git grep -h "^import\|^from" -- "*.py"`) ถ้าใช้ `conda env export --from-history` ให้ตรวจเพิ่มว่าแพ็กเกจที่ติดตั้งผ่าน pip (เช่น `sdv`) ไม่หายไป

## ขั้นที่ 6: Fresh-clone test แลกกับเพื่อน

จับคู่กับเพื่อน แต่ละคน clone repo ของอีกฝ่าย **ลงโฟลเดอร์ใหม่** แล้วทำตาม README เท่านั้น ห้ามเจ้าของ repo ช่วยพูด

```bash
git clone https://github.com/<เพื่อน>/pm25-explorer.git fresh-test
cd fresh-test
# ทำตามขั้นตอนใน README ทุกขั้น
```

ผู้ทดสอบเปิด issue ใน repo ของเพื่อน หัวข้อ `Fresh-clone test (สัปดาห์ที่ 14)` โดยใช้แบบฟอร์มนี้

```markdown
- [ ] สร้าง environment ได้ (ใช้เวลา ... นาที)
- [ ] `python run_all.py` ผ่าน / ใช้ไฟล์ตัวอย่างแทนเพราะ ...
- [ ] `quarto render report/report.qmd` ผ่าน
- [ ] `streamlit run app/app.py` เปิดได้ และ drill-down ครบ 4 ระดับ
- ขั้นที่ติด / error ที่พบ: ...
- ข้อเสนอแนะต่อ README: ...
```

เจ้าของ repo แก้ปัญหาตาม issue แล้วปิด issue โดยอ้างอิง commit ที่แก้

## ขั้นที่ 7 (เสริม): เปรียบเทียบกับ Power BI / Looker Studio

ส่งออกข้อมูลแล้วลองสร้างแดชบอร์ดระดับภาคในเครื่องมือ BI 1 หน้า

```python
import duckdb
con = duckdb.connect("data/pm25.duckdb", read_only=True)
con.execute("""COPY (SELECT d.*, s.name_th, s.province, s.region
                     FROM daily_pm25_clean d JOIN stations s USING (station_id))
               TO 'outputs/daily_pm25_clean.csv' (HEADER)""")
```

เขียน 3–5 บรรทัดใน `README.md` ว่าเครื่องมือใดเหมาะกับงานแบบใด

## ขั้นที่ 8: commit, push และเปิด pull request

```bash
git add report/report.qmd app/app.py run_all.py README.md questions.md .gitignore AI_USAGE.md
git commit -m "เพิ่ม data story report (Quarto), แดชบอร์ด drill-down 4 ระดับ และ run_all.py"
git push -u origin week14-report-dashboard
```

เปิด PR แล้วขอ review จากเพื่อนคนที่ทำ fresh-clone test ส่งไฟล์ `report/report.html` ที่ render แล้วในระบบส่งงานของรายวิชา

## ขั้นที่ 9: review PR ของเพื่อน

- [ ] หัวข้อในรายงานเป็นประโยคข้อค้นพบ และผูกกับคำถามใน `questions.md`
- [ ] มีส่วนข้อจำกัดที่เฉพาะเจาะจงกับข้อมูลของโครงการ
- [ ] app เปิด DuckDB ด้วย `read_only=True` ภายใน `st.cache_resource` และ query อยู่ใน `st.cache_data`
- [ ] SQL ใช้ `?` parameter กับค่าที่มาจากผู้ใช้ ไม่ต่อ string
- [ ] ไม่มี path absolute และ README มีขั้นตอนรันครบ
- [ ] ไม่ commit `report.html`, `data/` หรือ `outputs/`

---

## Checklist ก่อนส่งงาน

- [ ] `quarto render report/report.qmd` ผ่านจาก fresh clone และรายงานตอบทุกคำถามที่เลือก
- [ ] แดชบอร์ด drill-down ได้ 4 ระดับ ย้อนกลับได้ และตัวกรองวันที่ทำงานทุกระดับ
- [ ] `python run_all.py` สร้างฐานข้อมูลใหม่ได้ (หรือ README อธิบายทางเลือกเมื่อ API ล่ม)
- [ ] มี issue ผล fresh-clone test จากเพื่อน และแก้ครบแล้ว
- [ ] อัปเดต `AI_USAGE.md` และมี PR ที่เพื่อน review แล้ว
- [ ] ส่ง `report.html` ในระบบส่งงาน

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `quarto render` หา `data/pm25.duckdb` ไม่เจอ | Quarto รันใน `report/` ใช้ `../data/pm25.duckdb` |
| Quarto ใช้ Python ผิดตัว (`ModuleNotFoundError`) | activate environment ก่อน render หรือติดตั้ง kernel: `python -m ipykernel install --user --name dstoolbox` แล้วตั้ง `jupyter: dstoolbox` |
| `IOException: Could not set lock on file` ตอนรัน `run_all.py` | แดชบอร์ดหรือ notebook เปิดไฟล์อยู่ ปิด Streamlit และ kernel อื่นก่อน |
| แดชบอร์ดไม่เห็นข้อมูลใหม่หลังรัน pipeline | cache ยังเก็บผลเดิม กดเมนู ⋮ → *Clear cache* หรือรอ `ttl` |
| `StreamlitAPIException` เรื่องแก้ค่า widget | แก้ `st.session_state[key]` ของ widget ได้เฉพาะใน callback (`on_change`/`on_click`) หรือก่อนสร้าง widget |
| กด drill-down แล้วเด้งกลับระดับเดิม | ลืมล้างค่า `pick_*` ใน callback ตรวจฟังก์ชัน `drill` |
| `date_input` error ตอนเลือกช่วง | ระหว่างเลือกจะคืนค่า 1 วัน ต้องตรวจ `len(picked) == 2` |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 15)

1. ทำรายงานและแดชบอร์ดให้เสร็จ แก้ตามผล fresh-clone test
2. อ่าน [คู่มือการนำเสนอสัปดาห์ที่ 15](../week15/index.md) และเกณฑ์ 30 คะแนน
3. ร่างลำดับการนำเสนอ 10 นาที และเลือก 1 ข้อค้นพบที่จะ demo บนแดชบอร์ดสด
