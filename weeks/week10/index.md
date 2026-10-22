---
title: "สัปดาห์ที่ 10: Interactive visualization และข้อมูลขนาดใหญ่"
---

> **CLO:** CLO4 · **เครื่องมือ:** Plotly (หลัก), PyGWalker และ Datashader (เสริม)
> **ผลงานที่เพิ่มในระบบ:** กราฟ interactive ด้วย Plotly (hover, range slider, facet/animation รายเดือน) ใน `notebooks/10_interactive_viz.ipynb` + ไฟล์ HTML และฟังก์ชันสร้างกราฟใน `src/charts.py`

## วัตถุประสงค์การเรียนรู้

เมื่อจบสัปดาห์นี้ ผู้เรียนสามารถ

1. ตัดสินใจได้ว่าเมื่อใด interactivity ช่วยตอบคำถาม และเมื่อใดทำให้ข้อค้นพบสำคัญถูกซ่อน
2. เลือกใช้ `plotly.express` หรือ `plotly.graph_objects` ได้เหมาะกับงาน
3. สร้างกราฟ Plotly ที่มี hover, range slider, facet และ animation พร้อมเส้นมาตรฐาน 37.5 µg/m³
4. รับมือข้อมูลรายชั่วโมงขนาดหลายล้านแถว ด้วยการสรุปใน DuckDB การสุ่มตัวอย่าง และ Datashader
5. ใช้ PyGWalker สำรวจข้อมูลแบบลากวาง โดยแยกออกจากผลงานที่ต้องส่ง
6. เขียนฟังก์ชันสร้างกราฟที่นำไปใช้ใน Streamlit ในสัปดาห์ที่ 14 ได้

---

## 1. Interactivity ช่วยเมื่อไร และซ่อนอะไรได้บ้าง

สัปดาห์ที่ 9 เราสร้างภาพนิ่งที่ผู้วาดเลือกให้แล้วว่าผู้อ่านควรเห็นอะไร กราฟ interactive ให้ผู้อ่านเลือกเองได้บางส่วน ซึ่งมีทั้งข้อดีและข้อเสีย

| interactivity ช่วย | interactivity ซ่อน |
|---|---|
| **hover** ดูค่าจริง ชื่อสถานี และวันที่ของจุดผิดปกติ โดยไม่ต้องใส่ป้ายทุกจุด | ข้อค้นพบหลักถูกซ่อนไว้หลัง hover ถ้าผู้อ่านไม่ชี้เมาส์ก็ไม่เห็น |
| **zoom / range slider** ดูเหตุการณ์สั้น ๆ ในอนุกรมเวลาหลายปี | ผู้อ่านอาจซูมเข้าไปช่วงเดียวแล้วสรุปเกินจริง |
| **legend คลิกซ่อนกลุ่ม** ลดความรกเมื่อมีหลายภาค | สถานะเริ่มต้นที่เลือกไว้มีผลต่อการตีความมาก |
| **animation** เห็นการเปลี่ยนแปลงตามเดือน | ตาคนจำภาพก่อนหน้าได้ไม่แม่น เทียบข้ามเฟรมยาก ควรมี facet หรือภาพนิ่งคู่กัน |

**หลักปฏิบัติ:** สถานะเริ่มต้นของกราฟ (ก่อนผู้ใช้แตะอะไร) ต้องตอบคำถามหลักได้แล้ว interactivity เป็นของแถมสำหรับการเจาะลึก ไม่ใช่ที่ซ่อนคำตอบ ซึ่งเป็นแนวคิดเดียวกับ *"overview first, zoom and filter, then details on demand"* ของ Shneiderman (1996) และเป็นโครงของ dashboard drill-down 3–4 ระดับในสัปดาห์ที่ 14

## 2. `plotly.express` กับ `plotly.graph_objects`

Plotly มีสองระดับ ทั้งสองสร้างออบเจกต์ `Figure` ชนิดเดียวกัน จึงผสมกันได้

| | `plotly.express` (px) | `plotly.graph_objects` (go) |
|---|---|---|
| แนวคิด | grammar of graphics: ส่ง DataFrame + ชื่อคอลัมน์ | สร้างทีละ trace และกำหนด layout เอง |
| โค้ด | สั้น หนึ่งบรรทัดได้กราฟ | ยาวกว่า ควบคุมได้ทุกจุด |
| facet / animation | มีในตัว (`facet_col`, `animation_frame`) | ต้องทำเองด้วย `make_subplots` / frames |
| ใช้เมื่อ | งานส่วนใหญ่ของรายวิชา | ต้องการกราฟพิเศษ หรือซ้อน trace หลายชนิด |

แนวทางที่แนะนำ: **เริ่มด้วย px แล้วปรับแต่งด้วยเมธอดของ Figure** (`update_layout`, `update_traces`, `add_hline`, `add_trace`)

```python
import plotly.express as px
import plotly.graph_objects as go

fig = px.line(df, x="date", y="pm25_mean", color="region")        # px สร้างโครง
fig.add_trace(go.Scatter(x=events["date"], y=events["pm25_mean"],  # go เพิ่ม trace พิเศษ
                         mode="markers", name="วันเกิดเหตุ", marker_symbol="x"))
fig.update_layout(font_family="Sarabun, Tahoma, sans-serif")
```

Plotly แสดงผลใน browser จึงแสดงอักษรไทยได้โดยไม่ต้องตั้งค่า font แบบ matplotlib แต่ควรกำหนด `font_family` ให้หน้าตาเหมือนกันทุกเครื่อง

## 3. กราฟ interactive หลักสำหรับ PM2.5

### เตรียมข้อมูลด้วย DuckDB

```python
import duckdb, pandas as pd
con = duckdb.connect("data/pm25.duckdb", read_only=True)

region_daily = con.sql("""
    SELECT s.region, d.date,
           median(d.pm25_mean) AS pm25_median,
           count(*)            AS n_stations
    FROM daily_pm25_clean AS d JOIN stations AS s USING (station_id)
    GROUP BY ALL
    ORDER BY s.region, d.date
""").df()
```

### Time series พร้อม hover และ range slider

```python
THAI_STD = 37.5
fig = px.line(region_daily, x="date", y="pm25_median", color="region",
              hover_data={"n_stations": True, "pm25_median": ":.1f"},
              labels={"pm25_median": "มัธยฐาน PM2.5 (µg/m³)", "date": "วันที่",
                      "region": "ภาค", "n_stations": "จำนวนสถานี"})
fig.add_hline(y=THAI_STD, line_dash="dash", line_color="black",
              annotation_text="มาตรฐานไทย 37.5", annotation_position="top left")
fig.update_xaxes(rangeslider_visible=True)
fig.show()
```

`hover_data` ใส่ `n_stations` ไว้เพื่อให้ผู้อ่านรู้ว่าค่ามัธยฐานแต่ละวันมาจากกี่สถานี วันที่มีสถานีน้อยควรเชื่อถือน้อยลง

### ปรับข้อความ hover ด้วย `hovertemplate`

```python
fig.update_traces(hovertemplate="%{x|%d/%m/%Y}<br>%{y:.1f} µg/m³<extra>%{fullData.name}</extra>")
```

### Facet: เทียบหลายภาคบนแกนเดียวกัน

```python
region_daily["month"] = pd.to_datetime(region_daily["date"]).dt.month
fig = px.box(region_daily, x="month", y="pm25_median", facet_col="region", facet_col_wrap=3,
             labels={"pm25_median": "PM2.5 (µg/m³)", "month": "เดือน"})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))   # ตัด "region=" ออกจากหัว facet
```

facet ใน px ใช้แกน y ร่วมกันเป็นค่าเริ่มต้น ซึ่งเป็นสิ่งที่ต้องการเมื่อเทียบระดับ

### Animation ตามเดือน

```python
monthly = con.sql("""
    SELECT s.region, month(d.date) AS month, median(d.pm25_mean) AS pm25_median
    FROM daily_pm25_clean AS d JOIN stations AS s USING (station_id)
    GROUP BY ALL ORDER BY month
""").df()
fig = px.bar(monthly, x="region", y="pm25_median", animation_frame="month",
             range_y=[0, monthly["pm25_median"].max() * 1.1])   # ล็อกแกน y ทุกเฟรม
fig.add_hline(y=THAI_STD, line_dash="dash")
```

ถ้าไม่กำหนด `range_y` แกน y อาจไม่พอดีกับทุกเฟรม และเทียบข้ามเดือนได้ยาก ควรวาง facet หรือ heatmap เดือน × ภาค คู่กับ animation เสมอ เพราะ animation อย่างเดียวเทียบข้ามเฟรมยาก

### แทนแกนคู่ด้วย subplot ที่ใช้แกน x ร่วม

```python
from plotly.subplots import make_subplots
one = con.execute("SELECT * FROM daily_pm25_clean WHERE station_id = ? ORDER BY date", ["<station_id>"]).df()  # ใส่รหัสสถานีจริง
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=["PM2.5", "จำนวนชั่วโมงที่วัดได้"])
fig.add_trace(go.Scatter(x=one["date"], y=one["pm25_mean"], name="PM2.5"), row=1, col=1)
fig.add_trace(go.Bar(x=one["date"], y=one["n_hours"], name="n_hours"), row=2, col=1)
```

### บันทึกเป็น HTML

```python
fig.write_html("reports/10_region_timeseries.html", include_plotlyjs="cdn")
```

`include_plotlyjs="cdn"` ทำให้ไฟล์เล็ก (โหลด plotly.js จากอินเทอร์เน็ต) ถ้าต้องเปิดแบบออฟไลน์ให้ใช้ค่าเริ่มต้น (`True`) ซึ่งฝัง plotly.js ลงในไฟล์ ขนาดประมาณ 3–5 MB

## 4. ข้อมูลใหญ่: คิดก่อนวาด

ประมาณขนาดของตาราง `measurements`

```text
~80 สถานี × 24 ชั่วโมง × 365 วัน × 5 ปี ≈ 3.5 ล้านแถว
```

Plotly ฝังข้อมูลทุกจุดลงใน HTML/JSON ถ้าส่ง 3.5 ล้านจุดไป browser จะช้าหรือค้าง และตาคนก็แยก 3.5 ล้านจุดบนจอกว้าง ~1,000 pixel ไม่ได้อยู่แล้ว

| กลยุทธ์ | ทำที่ไหน | ใช้เมื่อ | ข้อควรระวัง |
|---|---|---|---|
| **สรุป (aggregate) ก่อน** | DuckDB (`GROUP BY`) | แทบทุกกรณี: รายวัน รายเดือน รายภาค ชั่วโมง × เดือน | ค่าเฉลี่ยซ่อนค่าสุดขั้ว ให้เก็บ max/percentile ไว้ด้วย |
| **สุ่มตัวอย่าง (sampling)** | DuckDB `USING SAMPLE` | ดูรูปร่างความสัมพันธ์ของสองตัวแปร | ค่าหายากอาจหลุดหาย ต้องกำหนด seed ให้ทำซ้ำได้ |
| **WebGL** | Plotly `render_mode="webgl"` | หลักแสนจุด | ยังส่งข้อมูลทั้งหมดไป browser |
| **Datashader** (เสริม) | Python (ก่อนส่งไป browser) | หลักล้านจุดขึ้นไป | ได้ภาพ raster ไม่มี hover รายจุด |

### สรุปใน DuckDB: รูปแบบรายชั่วโมงตามเดือน

```python
hour_month = con.sql("""
    SELECT s.region, month(m.ts) AS month, hour(m.ts) AS hour,
           median(m.pm25) AS pm25_median, count(*) AS n
    FROM measurements AS m JOIN stations AS s USING (station_id)
    WHERE m.pm25 IS NOT NULL
    GROUP BY ALL
""").df()
len(hour_month)   # หลักพันแถว จากหลักล้าน
fig = px.density_heatmap(hour_month[hour_month["region"] == hour_month["region"].iloc[0]],
                         x="hour", y="month", z="pm25_median", histfunc="avg",
                         nbinsx=24, nbinsy=12, color_continuous_scale="Viridis")
```

### สุ่มตัวอย่างแบบทำซ้ำได้

```python
sample = con.sql("""
    SELECT pm25, pm10 FROM measurements
    USING SAMPLE 1% (bernoulli, 42)      -- 42 คือ seed
""").df()
px.scatter(sample, x="pm10", y="pm25", opacity=0.2, render_mode="webgl")
```

## 5. Datashader (เสริม): วาดหลักล้านจุด

Datashader ไม่ได้วาดจุดทีละจุด แต่ **นับจำนวนจุดที่ตกในแต่ละ pixel** แล้วแปลงจำนวนเป็นสี ผลจึงเป็นภาพความหนาแน่นที่ไม่มี overplotting

```python
import datashader as ds
import datashader.transfer_functions as tf

hourly = con.sql("SELECT ts, pm25 FROM measurements WHERE pm25 IS NOT NULL").df()
hourly["t"] = hourly["ts"].astype("int64")            # Datashader ต้องการแกนเป็นตัวเลข

canvas = ds.Canvas(plot_width=900, plot_height=300, y_range=(0, 300))
agg = canvas.points(hourly, x="t", y="pm25", agg=ds.count())
img = tf.shade(agg, how="log")                         # log ทำให้เห็นทั้งบริเวณหนาแน่นและเบาบาง
tf.set_background(img, "white")
```

ภาพที่ได้แสดงทุกค่ารายชั่วโมงของทุกสถานี จะเห็นว่าแถบความหนาแน่นยกตัวขึ้นทุกฤดูแล้ง และมีค่าสุดขั้วกระจายอยู่ด้านบน ข้อจำกัดคือไม่มี hover ถ้าต้องการรู้ว่าจุดไหนเป็นสถานีอะไร ให้กลับไป query ใน DuckDB

## 6. PyGWalker (เสริม): สำรวจแบบลากวาง

PyGWalker เปิดหน้าจอคล้าย Tableau ใน notebook ลากคอลัมน์ไปวางบนแกน สี หรือ facet ได้ทันที

```python
import pygwalker as pyg
pyg.walk(region_daily)        # ส่งตารางที่สรุปแล้ว ไม่ใช่ measurements ทั้งตาราง
```

| ใช้ PyGWalker เพื่อ | ไม่ใช้ PyGWalker เพื่อ |
|---|---|
| ลองหลาย encoding เร็ว ๆ หาว่ากราฟแบบไหนน่าสนใจ | เป็นผลงานส่ง เพราะคนอื่นทำซ้ำขั้นตอนลากวางไม่ได้ |
| สำรวจคอลัมน์ที่ยังไม่คุ้นเคย | แทนการเขียนโค้ด Plotly ที่ review ได้ |

เมื่อเจอกราฟที่ใช่แล้ว ให้ **เขียนใหม่ด้วย Plotly ในโค้ด** และ commit โค้ดนั้น นี่คือหลักเดียวกับสัปดาห์ที่ 1: งานต้องทำซ้ำได้

## 7. เตรียมกราฟสำหรับ Streamlit (ตัวอย่างล่วงหน้าสัปดาห์ที่ 14)

ใน dashboard กราฟจะถูกเรียกซ้ำทุกครั้งที่ผู้ใช้เปลี่ยนตัวเลือก จึงควรแยกเป็น **ฟังก์ชันที่รับ DataFrame แล้วคืน Figure** ไว้ใน `src/charts.py`

```python
# src/charts.py
import plotly.express as px

THAI_STD = 37.5

def region_timeseries(df):
    """df ต้องมีคอลัมน์ region, date, pm25_median"""
    fig = px.line(df, x="date", y="pm25_median", color="region",
                  labels={"pm25_median": "มัธยฐาน PM2.5 (µg/m³)", "date": "วันที่", "region": "ภาค"})
    fig.add_hline(y=THAI_STD, line_dash="dash", annotation_text="มาตรฐานไทย 37.5")
    fig.update_xaxes(rangeslider_visible=True)
    return fig
```

ใน notebook เรียก `region_timeseries(region_daily).show()` ส่วนในสัปดาห์ที่ 14 จะเรียกจาก Streamlit แบบนี้

```python
import streamlit as st
from charts import region_timeseries
st.plotly_chart(region_timeseries(region_daily))
```

ฟังก์ชันไม่ควร query DuckDB เอง ให้รับข้อมูลที่สรุปแล้วเข้ามา เพื่อให้สัปดาห์ที่ 14 ใส่ cache ที่ชั้น query ได้

## สรุป

- สถานะเริ่มต้นของกราฟ interactive ต้องตอบคำถามได้แล้ว hover/zoom/animation ใช้เจาะลึก ไม่ใช่ซ่อนคำตอบ
- ใช้ `plotly.express` เป็นหลัก แล้วปรับแต่งหรือเพิ่ม trace ด้วย `graph_objects`
- ข้อมูลรายชั่วโมงหลักล้านแถว: สรุปใน DuckDB ก่อนเสมอ สุ่มตัวอย่างพร้อม seed หรือใช้ Datashader
- PyGWalker ใช้สำรวจ ส่วนผลงานต้องเป็นโค้ดที่ทำซ้ำได้
- เขียนกราฟเป็นฟังก์ชันใน `src/charts.py` เพื่อใช้ต่อใน Streamlit

## คำถามทบทวน

1. ยกตัวอย่างกราฟ PM2.5 ที่ interactivity ช่วยตอบคำถาม และตัวอย่างที่ interactivity ทำให้ข้อค้นพบหลักถูกซ่อน
2. ทำไม animation รายเดือนจึงควรล็อก `range_y` และควรมีภาพนิ่งประกอบ
3. ถ้าต้องวาด scatter ของ PM2.5 กับ PM10 รายชั่วโมงทั้งหมด จะเลือกกลยุทธ์ใดในตารางหัวข้อ 4 เพราะอะไร
4. การสรุปเป็นค่าเฉลี่ยรายเดือนก่อนวาดอาจทำให้พลาดอะไรไป และแก้อย่างไร
5. ทำไมฟังก์ชันใน `src/charts.py` จึงไม่ควร query ฐานข้อมูลเอง

## อ่านเพิ่มเติม

- เอกสาร Plotly Express — <https://plotly.com/python/plotly-express/>
- Plotly: Time series และ range slider — <https://plotly.com/python/time-series/>
- เอกสาร Datashader — <https://datashader.org/getting_started/>
- PyGWalker — <https://github.com/Kanaries/pygwalker>
- Shneiderman, B. (1996). The Eyes Have It: A Task by Data Type Taxonomy for Information Visualizations. *IEEE Symposium on Visual Languages*.

➡️ [คู่มือปฏิบัติการสัปดาห์ที่ 10](lab.md)
