---
title: "ปฏิบัติการสัปดาห์ที่ 10: กราฟ interactive ด้วย Plotly และการรับมือข้อมูลใหญ่"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO4
> **ผลงานที่ต้องส่ง:** `src/charts.py` + `notebooks/10_interactive_viz.ipynb` ที่มีกราฟ Plotly อย่างน้อย 3 ภาพ (time series + hover + range slider, facet, animation รายเดือน) และไฟล์ HTML อย่างน้อย 1 ไฟล์ใน `reports/` พร้อม pull request ที่เพื่อน review แล้ว

## สิ่งที่ต้องเตรียม

- งานสัปดาห์ที่ 9 merge แล้ว: `src/viz_style.py`, `notebooks/09_static_viz.ipynb` และโฟลเดอร์ `reports/figures/`
- `data/pm25.duckdb` ที่มี `stations`, `measurements`, `daily_pm25_clean` (หรือไฟล์ตัวอย่างจากผู้สอนใน `data/sample/`)
- จำนวนแถวของ `measurements` ที่นับไว้จากงานศึกษาด้วยตนเองสัปดาห์ที่ 9
- ทดสอบไลบรารี: `python -c "import plotly; print(plotly.__version__)"` และ (เสริม) `python -c "import datashader, pygwalker"`

---

## ขั้นที่ 1: สร้าง branch

```bash
git switch main
git pull
git switch -c week10-interactive-viz
```

## ขั้นที่ 2: เปิด notebook และเตรียมตารางสรุปด้วย DuckDB

สร้าง `notebooks/10_interactive_viz.ipynb`

```python
import os, sys
if os.path.basename(os.getcwd()) == "notebooks":
    os.chdir("..")
sys.path.append("src")

import duckdb, pandas as pd
import plotly.express as px
import plotly.graph_objects as go

con = duckdb.connect("data/pm25.duckdb", read_only=True)
con.sql("SELECT count(*) AS n_rows, count(DISTINCT station_id) AS n_stations FROM measurements").df()
```

สร้างตารางสรุประดับภาค-วัน (ให้ DuckDB ทำงานหนัก)

```python
region_daily = con.sql("""
    SELECT s.region, d.date,
           median(d.pm25_mean) AS pm25_median,
           max(d.pm25_max)     AS pm25_peak,
           count(*)            AS n_stations
    FROM daily_pm25_clean AS d JOIN stations AS s USING (station_id)
    GROUP BY ALL
    ORDER BY s.region, d.date
""").df()
region_daily["date"] = pd.to_datetime(region_daily["date"])
region_daily.shape    # ประมาณ (จำนวนภาค × จำนวนวัน, 5)
```

## ขั้นที่ 3: สร้าง `src/charts.py`

```python
"""ฟังก์ชันสร้างกราฟ Plotly: รับ DataFrame ที่สรุปแล้ว คืน Figure (ใช้ซ้ำใน Streamlit สัปดาห์ที่ 14)"""
import plotly.express as px

THAI_STD = 37.5
FONT = "Sarabun, Tahoma, sans-serif"
LABELS = {"pm25_median": "มัธยฐาน PM2.5 (µg/m³)", "date": "วันที่", "region": "ภาค",
          "n_stations": "จำนวนสถานี", "month": "เดือน", "pm25_peak": "ค่าสูงสุดรายชั่วโมง"}


def _style(fig):
    fig.update_layout(font_family=FONT, legend_title_text="")
    return fig


def region_timeseries(df):
    """df: region, date, pm25_median, n_stations, pm25_peak"""
    fig = px.line(df, x="date", y="pm25_median", color="region", labels=LABELS,
                  hover_data={"n_stations": True, "pm25_peak": ":.0f", "pm25_median": ":.1f"})
    fig.add_hline(y=THAI_STD, line_dash="dash", line_color="black",
                  annotation_text="มาตรฐานไทย 37.5", annotation_position="top left")
    fig.update_xaxes(rangeslider_visible=True)
    return _style(fig)


def monthly_box(df):
    """df: region, month, pm25_median"""
    fig = px.box(df, x="month", y="pm25_median", facet_col="region", facet_col_wrap=3, labels=LABELS)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.add_hline(y=THAI_STD, line_dash="dash", line_color="black")
    return _style(fig)


def monthly_animation(df):
    """df: region, month, pm25_median (หนึ่งแถวต่อภาคต่อเดือน)"""
    fig = px.bar(df, x="region", y="pm25_median", animation_frame="month", labels=LABELS,
                 range_y=[0, df["pm25_median"].max() * 1.1])
    fig.add_hline(y=THAI_STD, line_dash="dash", line_color="black")
    return _style(fig)
```

## ขั้นที่ 4: Time series พร้อม hover และ range slider

```python
import importlib, charts
importlib.reload(charts)          # โหลดใหม่ทุกครั้งที่แก้ charts.py

fig = charts.region_timeseries(region_daily)
fig.show()
fig.write_html("reports/10_region_timeseries.html", include_plotlyjs="cdn")
```

ทดลองบนกราฟแล้วจดใน Markdown cell

1. ลาก range slider ไปที่ฤดูแล้งปีใดปีหนึ่ง ภาคใดเกิน 37.5 นานที่สุด
2. hover ที่จุดสูงสุด ค่า `n_stations` วันนั้นเป็นเท่าไร น่าเชื่อถือแค่ไหน
3. คลิก legend ซ่อนบางภาค แล้วถามตัวเองว่า *สถานะเริ่มต้น* ของกราฟตอบคำถามได้ครบหรือยัง

## ขั้นที่ 5: Facet และ animation ตามเดือน

```python
region_daily["month"] = region_daily["date"].dt.month
charts.monthly_box(region_daily).show()

monthly = (region_daily.groupby(["region", "month"], as_index=False)["pm25_median"].median())
fig = charts.monthly_animation(monthly)
fig.show()
fig.write_html("reports/10_monthly_animation.html", include_plotlyjs="cdn")
```

เขียน 2–3 บรรทัดว่า facet กับ animation อย่างไหนตอบคำถาม "ฤดูไหน ภาคไหน PM2.5 สูงสุด" ได้ดีกว่า

## ขั้นที่ 6: ข้อมูลรายชั่วโมงขนาดใหญ่ (สรุปก่อนวาด)

**6.1 สรุปใน DuckDB:** มัธยฐานรายชั่วโมงของวันตามเดือน ของภาคที่สนใจ

```python
REGION = region_daily["region"].iloc[0]     # เปลี่ยนเป็นภาคตามคำถามของตนเอง
hm = con.execute("""
    SELECT month(m.ts) AS month, hour(m.ts) AS hour, median(m.pm25) AS pm25_median
    FROM measurements AS m JOIN stations AS s USING (station_id)
    WHERE m.pm25 IS NOT NULL AND s.region = ?
    GROUP BY ALL
""", [REGION]).df()
pivot = hm.pivot(index="month", columns="hour", values="pm25_median")
px.imshow(pivot, color_continuous_scale="Viridis", aspect="auto",
          labels={"x": "ชั่วโมง", "y": "เดือน", "color": "µg/m³"}, title=f"PM2.5 ตามชั่วโมงและเดือน: {REGION}")
```

**6.2 สุ่มตัวอย่างแบบทำซ้ำได้** แล้ววาด scatter ด้วย WebGL

```python
sample = con.sql("""
    SELECT pm25, pm10 FROM measurements
    WHERE pm25 IS NOT NULL AND pm10 IS NOT NULL
    USING SAMPLE 1% (bernoulli, 42)
""").df()
print(len(sample))
px.scatter(sample, x="pm10", y="pm25", opacity=0.15, render_mode="webgl",
           labels={"pm10": "PM10 (µg/m³)", "pm25": "PM2.5 (µg/m³)"})
```

## ขั้นที่ 7: (เสริม) Datashader กับทุกค่ารายชั่วโมง

```python
import datashader as ds, datashader.transfer_functions as tf

hourly = con.sql("SELECT ts, pm25 FROM measurements WHERE pm25 IS NOT NULL").df()
hourly["t"] = hourly["ts"].astype("int64")
canvas = ds.Canvas(plot_width=900, plot_height=300, y_range=(0, 300))
img = tf.shade(canvas.points(hourly, x="t", y="pm25", agg=ds.count()), how="log")
tf.set_background(img, "white")
```

เทียบกับการวาดข้อมูลเดียวกันด้วย `px.scatter` (ห้ามรัน ถ้าเกินหนึ่งล้านแถว ให้ลองกับ `hourly.sample(50_000, random_state=42)` แทน) แล้วเขียนว่าภาพสองแบบเห็นอะไรต่างกัน

## ขั้นที่ 8: (เสริม) PyGWalker สำรวจเร็ว

```python
import pygwalker as pyg
pyg.walk(region_daily)
```

ลากวางหาความสัมพันธ์ที่น่าสนใจ 1 อย่าง แล้ว **เขียนกราฟนั้นใหม่ด้วย Plotly** ใน cell ถัดไป ลบ cell ของ PyGWalker ก่อน commit หรือ clear output เพราะ output มีขนาดใหญ่

## ขั้นที่ 9: อัปเดต `questions.md` และ commit

เพิ่มใต้คำถามที่เกี่ยวข้อง เช่น `- กราฟ interactive: reports/10_region_timeseries.html — ข้อสังเกต: …`

ก่อน commit ให้ **Restart Kernel and Run All** แล้วตรวจขนาดไฟล์ HTML (ควรไม่เกินไม่กี่ MB ถ้าใหญ่ แปลว่าส่งข้อมูลดิบเข้ากราฟ)

```bash
git status
git add src/charts.py notebooks/10_interactive_viz.ipynb reports/*.html questions.md AI_USAGE.md
git commit -m "เพิ่มกราฟ Plotly interactive (range slider, facet, animation) และฟังก์ชันใน charts.py"
git push -u origin week10-interactive-viz
```

เปิด PR บน GitHub แนบภาพหน้าจอกราฟหลักใน description ขอ review จากเพื่อน 1 คน แล้ว merge เมื่อได้ approve

## ขั้นที่ 10: review PR ของเพื่อน

ดาวน์โหลดไฟล์ HTML ของเพื่อนแล้วเปิดใน browser

- [ ] สถานะเริ่มต้นของกราฟ (ก่อน hover/zoom) ตอบคำถามที่ระบุได้
- [ ] hover แสดงข้อมูลที่ช่วยตีความ (เช่น จำนวนสถานี) และมีหน่วย
- [ ] animation ล็อกแกน y และมี facet หรือภาพนิ่งประกอบ
- [ ] ไม่มีกราฟที่ส่งข้อมูลรายชั่วโมงดิบทั้งหมดเข้า Plotly
- [ ] ฟังก์ชันใน `src/charts.py` รับ DataFrame คืน Figure และไม่ query ฐานข้อมูลเอง
- [ ] ไฟล์ HTML มีขนาดสมเหตุสมผล และไม่มี output ของ PyGWalker ค้างใน notebook

---

## Checklist ก่อนส่งงาน

- [ ] `src/charts.py` มีอย่างน้อย 3 ฟังก์ชัน และ import ได้
- [ ] notebook รัน Restart & Run All ผ่าน
- [ ] มี time series ที่มี hover + range slider + เส้น 37.5
- [ ] มีกราฟ facet และ animation รายเดือน
- [ ] มีกราฟจากข้อมูลรายชั่วโมงที่สรุปหรือสุ่มใน DuckDB อย่างน้อย 1 ภาพ
- [ ] บันทึก HTML ใน `reports/` อย่างน้อย 1 ไฟล์ และ `questions.md` อัปเดตแล้ว
- [ ] บันทึกการใช้ AI ใน `AI_USAGE.md` (ถ้ามี)
- [ ] PR ถูก review และ merge แล้ว

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| กราฟไม่แสดงใน VS Code / Jupyter (ช่องว่าง) | ติดตั้ง `nbformat` ในสภาพแวดล้อม หรือกำหนด `import plotly.io as pio; pio.renderers.default = "notebook"` (VS Code ใช้ `"vscode"`) |
| notebook ช้าหรือค้างหลังวาด | ส่งข้อมูลมากเกินไปเข้า Plotly ให้ `GROUP BY` ใน DuckDB หรือ `USING SAMPLE` ก่อน |
| ไฟล์ HTML ใหญ่หลายสิบ MB | ใช้ `include_plotlyjs="cdn"` และสรุปข้อมูลก่อนวาด |
| เปิด HTML แบบไม่มีอินเทอร์เน็ตแล้วว่างเปล่า | ไฟล์แบบ `cdn` ต้องโหลด plotly.js จากเน็ต ให้บันทึกใหม่ด้วยค่าเริ่มต้น `include_plotlyjs=True` |
| แก้ `charts.py` แล้วกราฟไม่เปลี่ยน | Python cache module ไว้ ใช้ `importlib.reload(charts)` หรือ restart kernel |
| animation แต่ละเฟรมแกน y ไม่เท่ากัน | กำหนด `range_y=[0, ค่าสูงสุด]` |
| Datashader error เกี่ยวกับ datetime | แปลงแกนเวลาเป็นตัวเลขก่อน (`ts.astype("int64")`) |
| หัว facet แสดง `region=ภาคเหนือ` | ใช้ `fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))` |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 11)

1. ทบทวนความหมายของ median, IQR, p-value และ effect size (สถิติพื้นฐานที่เคยเรียน)
2. อ่านเอกสาร `scipy.stats.mannwhitneyu` และ `statsmodels.tsa.seasonal.STL` อย่างคร่าว ๆ
3. จากกราฟสัปดาห์ 9–10 เลือกข้อสังเกต 2 ข้อที่ต้องการ *ทดสอบ* ในสัปดาห์ที่ 11 เขียนเป็นสมมติฐานใน `questions.md` พร้อมระบุว่าจะใช้ข้อมูลปีใดสำรวจ และปีใดเก็บไว้ทดสอบ (held-out)
