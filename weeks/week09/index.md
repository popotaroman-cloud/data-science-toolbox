---
title: "สัปดาห์ที่ 9: หลักการ visualization และ grammar of graphics"
---

> **CLO:** CLO4 · **เครื่องมือ:** seaborn (หลัก), Altair (เสริม)
> **ผลงานที่เพิ่มในระบบ:** กราฟ univariate / bivariate ใน `notebooks/09_static_viz.ipynb` ที่ผูกกับคำถามใน `questions.md`
>
> **อ่านประกอบในหนังสือ:** บทที่ 11 [หลักการรับรู้และการออกแบบภาพข้อมูล](../../book/chapters/11-visual-perception.html) — อ่านเสริม: [หัวข้อ 12.1–12.2 grammar of graphics](../../book/chapters/12-interactive-viz.html#sec-ch12-grammar)

## วัตถุประสงค์การเรียนรู้

เมื่อจบสัปดาห์นี้ ผู้เรียนสามารถ

1. อธิบายองค์ประกอบของ grammar of graphics (data, encoding, mark, scale, facet, coordinate) และแยกองค์ประกอบเหล่านี้ออกจากกราฟที่เห็นได้
2. เลือกชนิดกราฟให้ตรงกับชนิดของคำถาม (distribution, comparison, relationship, time)
3. ใช้หลักการรับรู้ภาพ (position > length > angle/area) และเลือก palette สีให้ตรงกับชนิดข้อมูล รวมถึง palette ที่คนตาบอดสีอ่านได้
4. ระบุกราฟที่ชวนเข้าใจผิด เช่น แกนถูกตัด แกนคู่ และ overplotting แล้วแก้ไขได้
5. สร้างกราฟด้วย seaborn ที่แสดงป้ายภาษาไทยได้ถูกต้อง และมีเส้นมาตรฐาน PM2.5 ของไทย 37.5 µg/m³

---

## 1. จาก pipeline สู่กราฟ: เริ่มจากคำถามเสมอ

ถึงสัปดาห์ที่ 8 ระบบของเรามี `data/pm25.duckdb` ที่มีตาราง `stations`, `measurements` และ view `daily_pm25_clean` ที่ผ่านการตรวจด้วย pandera แล้ว ช่วงสัปดาห์ 9–13 เป็นช่วง **ใช้ข้อมูลตอบคำถาม** ที่ตั้งไว้ใน `questions.md` ตั้งแต่สัปดาห์ที่ 2

```text
questions.md  →  เลือกชนิดกราฟ  →  query จาก DuckDB  →  กราฟ  →  ข้อสังเกต (ไม่ใช่ข้อสรุป)
```

กราฟทุกภาพในสัปดาห์นี้ต้องตอบได้ว่า "ภาพนี้ตอบคำถามข้อไหน" ถ้าตอบไม่ได้ แปลว่ากำลังวาดเพราะวาดได้ ไม่ใช่เพราะต้องรู้

> **ข้อควรจำ:** กราฟจาก EDA ยังเป็น *เบาะแส* การยืนยันด้วยสถิติอยู่ในสัปดาห์ที่ 11

## 2. Grammar of graphics

Leland Wilkinson (1999) เสนอว่ากราฟทุกชนิดประกอบจาก **ชั้นของไวยากรณ์** ชุดเดียวกัน แทนที่จะจำชื่อกราฟเป็นร้อยชนิด ให้คิดว่ากำลังจับคู่ *คอลัมน์ของข้อมูล* กับ *คุณสมบัติทางภาพ* อย่างไร Hadley Wickham นำแนวคิดนี้ไปทำเป็น ggplot2 และไลบรารี Python หลายตัวก็ใช้แนวคิดเดียวกัน

| องค์ประกอบ | ความหมาย | ตัวอย่างจาก PM2.5 |
|---|---|---|
| **data** | ตารางข้อมูล หนึ่งแถวต่อหนึ่งหน่วยสังเกต (tidy) | `daily_pm25_clean` หนึ่งแถว = หนึ่งสถานีต่อหนึ่งวัน |
| **aesthetics / encoding** | การจับคู่คอลัมน์กับช่องทางภาพ (x, y, color, size, shape) | x = `date`, y = `pm25_mean`, color = `region` |
| **geom / mark** | รูปทรงที่ใช้วาด | จุด เส้น แท่ง กล่อง |
| **scale** | วิธีแปลงค่าข้อมูลเป็นตำแหน่งหรือสี | แกน y แบบ log, palette สีของภาค |
| **facet** | แบ่งเป็นกราฟย่อยหลายช่องตามตัวแปร | หนึ่งช่องต่อหนึ่งภาค |
| **coordinate** | ระบบพิกัด | Cartesian (ปกติ), polar (กราฟวงกลม), พิกัดแผนที่ (สัปดาห์ที่ 13) |
| (statistic) | การคำนวณก่อนวาด | bin ของ histogram, ค่ามัธยฐานในกล่อง |

ประโยชน์ของการคิดแบบนี้คือ เปลี่ยนกราฟได้ด้วยการเปลี่ยนองค์ประกอบเดียว เช่น จาก scatter เป็น line ก็แค่เปลี่ยน mark หรือจากกราฟเดียวเป็นหลายช่องก็แค่เพิ่ม facet

seaborn มี interface `seaborn.objects` (ตั้งแต่ 0.12) ที่เขียนตามไวยากรณ์นี้ตรง ๆ (`daily_region` คือตารางมัธยฐาน PM2.5 รายวันต่อภาค ซึ่งสร้างได้จาก `daily` ในหัวข้อที่ 7 ด้วย `daily.groupby(["region", "date"], as_index=False)["pm25_mean"].median().rename(columns={"pm25_mean": "pm25_median"})`)

```python
import seaborn.objects as so

(
    so.Plot(daily_region, x="date", y="pm25_median", color="region")  # data + encoding
    .add(so.Line())                                                    # mark
    .scale(y="log")                                                    # scale
    .facet(col="region", wrap=3)                                       # facet
)
```

Altair (เสริม) ใช้ไวยากรณ์เดียวกันผ่าน Vega-Lite และระบุชนิดข้อมูลไว้หลังชื่อคอลัมน์ (`:Q` quantitative, `:N` nominal, `:O` ordinal, `:T` temporal)

```python
import altair as alt

# Altair ปฏิเสธข้อมูลเกิน 5,000 แถว (MaxRowsError) ข้อมูลรายวันสี่ภาคสี่ปีมีราว 5,800 แถว
# จึงสรุปเป็นรายเดือนก่อนวาด (หนังสือบทที่ 12)
monthly_region = (daily_region.assign(month=daily_region["date"].dt.to_period("M").dt.to_timestamp())
                  .groupby(["region", "month"], as_index=False)["pm25_median"].median())
alt.Chart(monthly_region).mark_line().encode(
    x="month:T", y="pm25_median:Q", color="region:N"
).facet(column="region:N")
```

## 3. เลือกกราฟจากชนิดของคำถาม

คำถามใน `questions.md` ส่วนใหญ่จัดอยู่ใน 4 กลุ่มนี้ เลือกกลุ่มก่อน แล้วค่อยเลือกกราฟ

| ชนิดคำถาม | ตัวอย่างคำถาม PM2.5 | กราฟที่เหมาะ (seaborn) | หลีกเลี่ยง |
|---|---|---|---|
| **distribution** (ค่ากระจายอย่างไร) | ค่าเฉลี่ยรายวันส่วนใหญ่อยู่ช่วงไหน เกินมาตรฐานบ่อยแค่ไหน | `histplot`, `ecdfplot`, `kdeplot` | แท่งค่าเฉลี่ยอย่างเดียว |
| **comparison** (กลุ่มต่างกันไหม) | ภาคเหนือสูงกว่ากรุงเทพฯ ในฤดูแล้งหรือไม่ | `boxplot`, `violinplot`, `stripplot`, `barplot` (เมื่อเทียบจำนวน/สัดส่วน) | pie chart หลายชิ้น |
| **relationship** (สองตัวแปรสัมพันธ์กันไหม) | วันที่ค่าเฉลี่ยสูง ค่าสูงสุดรายชั่วโมงสูงตามหรือไม่ | `scatterplot`, `regplot`, `histplot` 2 มิติ | scatter หลายแสนจุดแบบทึบ |
| **time** (เปลี่ยนตามเวลาอย่างไร) | PM2.5 มีรูปแบบรายเดือนหรือแนวโน้มรายปีไหม | `lineplot`, heatmap เดือน × ปี | แท่งเรียงวันละแท่ง |

ข้อสังเกต: ใน seaborn มีฟังก์ชันระดับ figure (`displot`, `catplot`, `relplot`) ที่รับ `col=` / `row=` เพื่อทำ facet ได้ทันที ส่วนฟังก์ชันระดับ axes (`histplot`, `boxplot`, `lineplot`) วาดลงใน `ax` เดียว เหมาะกับการจัดหลายกราฟเอง

## 4. การรับรู้ภาพ: ตาคนอ่านอะไรได้แม่น

Cleveland & McGill (1984) ทดลองว่าคนประมาณค่าจากช่องทางภาพแบบไหนได้แม่นที่สุด ผลโดยสรุปคือ

```text
แม่นที่สุด                                                        แม่นน้อยที่สุด
ตำแหน่งบนแกนร่วม > ตำแหน่งบนแกนไม่ร่วม > ความยาว > มุม/ความชัน > พื้นที่ > ปริมาตร, ความเข้มสี
```

ผลในทางปฏิบัติ

- ค่าที่ต้องเทียบกันให้แม่น ให้วางบน **ตำแหน่ง** (แกน x/y ร่วมกัน) ไม่ใช่ขนาดหรือสี
- pie chart ใช้ *มุม* จึงเทียบได้ยากกว่า bar chart ที่ใช้ *ความยาว*
- สีเหมาะกับการ *แยกกลุ่ม* หรือแสดงภาพรวมคร่าว ๆ (เช่น heatmap) ไม่เหมาะกับการอ่านค่าละเอียด

### แกนที่ซื่อสัตย์ (honest axes)

| กฎ | เหตุผล |
|---|---|
| bar chart ต้องเริ่มที่ 0 | ความยาวของแท่งคือค่า ถ้าตัดแกน ความยาวจะโกหก |
| line chart / scatter ไม่จำเป็นต้องเริ่มที่ 0 | อ่านจากตำแหน่ง แต่ต้องติดป้ายแกนให้ชัด |
| กราฟที่ต้องเทียบกันให้ใช้ scale เดียวกัน | facet ใน seaborn ใช้ `sharey=True` เป็นค่าเริ่มต้น อย่าปิดโดยไม่บอกผู้อ่าน |
| ใช้ log scale ได้ แต่ต้องเขียนกำกับ | PM2.5 เบ้ขวา log ช่วยให้เห็นช่วงค่าต่ำ แต่ผู้อ่านทั่วไปอาจอ่านผิด |
| ระบุหน่วยเสมอ | "PM2.5 (µg/m³)" ไม่ใช่ "pm25_mean" |

### สีตามชนิดข้อมูล

| ชนิดข้อมูล | palette | ตัวอย่าง PM2.5 | ใน seaborn |
|---|---|---|---|
| **categorical** (กลุ่มไม่มีลำดับ) | สีต่างกันชัด ความสว่างใกล้กัน | ภาค, ประเภทสถานี | `"colorblind"`, `"tab10"` |
| **sequential** (ต่ำ → สูง) | สีเดียวไล่ความเข้ม | ค่า PM2.5 ใน heatmap | `"viridis"`, `"rocket"`, `"mako"` |
| **diverging** (ต่ำกว่า/สูงกว่าจุดกลาง) | สองสีออกจากจุดกลาง | ส่วนต่างจากมาตรฐาน 37.5 | `"RdBu_r"`, `"vlag"` |

**colorblind-safe:** ประมาณ 8% ของผู้ชายมีภาวะบกพร่องการเห็นสีแดง-เขียว ให้หลีกเลี่ยงการใช้คู่แดง-เขียวเป็นตัวแยกกลุ่มหลัก ใช้ `sns.color_palette("colorblind")` หรือ palette ตระกูล viridis ซึ่งยังอ่านได้เมื่อพิมพ์ขาวดำ และอย่าใช้กลุ่มเกิน 6–8 สีในกราฟเดียว ถ้ากลุ่มมากกว่านั้นให้ใช้ facet แทน

> **ระวัง:** "rainbow"/"jet" เป็น palette ที่ไม่ควรใช้กับข้อมูลต่อเนื่อง เพราะความสว่างไม่ไล่ตามค่า ทำให้เกิดขอบปลอมในภาพ

## 5. กราฟที่ชวนเข้าใจผิดและวิธีแก้

| ปัญหา | ตัวอย่างกับ PM2.5 | วิธีแก้ |
|---|---|---|
| **แท่งถูกตัดแกน (truncated bars)** | แกน y เริ่มที่ 30 ทำให้เชียงใหม่ (45) ดูสูงกว่ากรุงเทพฯ (35) สามเท่า | เริ่มแกนที่ 0 หรือเปลี่ยนเป็น dot plot |
| **แกนคู่ (dual axes)** | PM2.5 แกนซ้าย จุดความร้อน (hotspot) แกนขวา เส้นทับกันพอดีเพราะผู้วาดเลือกช่วงแกนเอง | วาดสองกราฟซ้อนแนวตั้งที่ใช้แกน x ร่วม หรือ scatter สองตัวแปรตรง ๆ |
| **overplotting** | scatter 80 สถานี × หลายปี เป็นก้อนดำ มองไม่เห็นความหนาแน่น | `alpha` ต่ำ, จุดเล็ก, `histplot(x=, y=)` 2 มิติ, สุ่มตัวอย่าง หรือสรุปก่อนวาด (สัปดาห์ที่ 10 ใช้ Datashader) |
| **ค่าเฉลี่ยซ่อนการกระจาย** | bar chart ค่าเฉลี่ยรายภาค ไม่เห็นว่ามีวันที่สูงมาก | box/violin/strip plot หรือแสดง ECDF |
| **เลือกช่วงเวลาให้เข้าข้าง** | แสดงเฉพาะเดือนมีนาคม แล้วสรุปทั้งปี | แสดงช่วงเวลาทั้งหมดก่อน แล้วค่อยซูม พร้อมบอกเหตุผล |
| **ไม่บอกจำนวนตัวอย่าง** | จังหวัดที่มีสถานีเดียวถูกเทียบกับกรุงเทพฯ ที่มีหลายสิบสถานี | ใส่ n ในป้ายหรือคำบรรยาย |

## 6. ตั้งค่า font ภาษาไทยสำหรับ matplotlib/seaborn

font เริ่มต้นของ matplotlib (DejaVu Sans) ไม่มีอักษรไทย ป้ายภาษาไทยจะกลายเป็นสี่เหลี่ยม (□□□) ต้องสั่งให้ใช้ font ที่มีอักษรไทยก่อนวาด

```python
import matplotlib.pyplot as plt
from matplotlib import font_manager
import seaborn as sns

# ดูว่าเครื่องนี้มี font ไทยอะไรบ้าง
thai_fonts = sorted({f.name for f in font_manager.fontManager.ttflist
                     if any(k in f.name for k in ["Tahoma", "Sarabun", "Leelawadee", "Loma", "Garuda", "Noto Sans Thai"])})
print(thai_fonts)

sns.set_theme(style="whitegrid", palette="colorblind", font="Tahoma")   # เปลี่ยนเป็นชื่อที่มีในเครื่อง
plt.rcParams["axes.unicode_minus"] = False   # ให้เครื่องหมายลบแสดงถูกต้อง
```

| ระบบ | font ที่มักมีอยู่แล้ว | ถ้าไม่มี |
|---|---|---|
| Windows | Tahoma, Leelawadee UI | — |
| macOS | Thonburi, Ayuthaya, Tahoma | — |
| Linux / Colab | ไม่มีเป็นค่าเริ่มต้น | ดาวน์โหลด Sarabun จาก Google Fonts แล้วใช้ `font_manager.fontManager.addfont("path/Sarabun-Regular.ttf")` |

ให้เก็บโค้ดส่วนนี้ไว้ใน `src/viz_style.py` แล้ว import ในทุก notebook เพื่อให้กราฟทุกภาพในโครงการหน้าตาเหมือนกัน (ทำในปฏิบัติการ)

## 7. seaborn ในทางปฏิบัติกับข้อมูล PM2.5

### โหลดข้อมูล

```python
import duckdb
import pandas as pd

con = duckdb.connect("data/pm25.duckdb", read_only=True)
daily = con.sql("""
    SELECT d.station_id, d.date, d.pm25_mean, d.pm25_max, d.n_hours,
           s.name_th, s.province, s.region
    FROM daily_pm25_clean AS d
    JOIN stations AS s USING (station_id)
    WHERE d.is_complete
""").df()
daily["date"] = pd.to_datetime(daily["date"])
daily["month"] = daily["date"].dt.month
daily.shape   # ประมาณ (จำนวนสถานี × จำนวนวัน, 9)
```

ให้ DuckDB ทำงาน join และกรองข้อมูล ส่วน pandas/seaborn รับเฉพาะตารางที่พร้อมวาด แนวทางนี้สำคัญมากในสัปดาห์ที่ 10 เมื่อข้อมูลใหญ่ขึ้น

### Univariate: การกระจายของค่าเฉลี่ยรายวัน

```python
THAI_STD, WHO_GUIDE = 37.5, 15

fig, ax = plt.subplots(figsize=(8, 4))
sns.histplot(data=daily, x="pm25_mean", bins=60, log_scale=True, ax=ax)
ax.axvline(THAI_STD, color="black", linestyle="--")
ax.text(THAI_STD, ax.get_ylim()[1] * 0.9, " มาตรฐานไทย 37.5", va="top")
ax.axvline(WHO_GUIDE, color="gray", linestyle=":")
ax.text(WHO_GUIDE, ax.get_ylim()[1] * 0.8, " WHO 15", va="top", color="gray")
ax.set(xlabel="PM2.5 เฉลี่ย 24 ชม. (µg/m³, log scale)", ylabel="จำนวนสถานี-วัน",
       title="ค่าเฉลี่ยรายวันส่วนใหญ่ต่ำกว่ามาตรฐาน แต่หางขวายาวมาก")
```

ข้อสังเกตที่ควรเห็น: PM2.5 **เบ้ขวา** (right-skewed) ค่าส่วนใหญ่ต่ำ แต่มีวันที่สูงมาก ถ้าไม่ใช้ log scale แท่งด้านซ้ายจะอัดกันจนอ่านไม่ออก สัปดาห์ที่ 11 จะใช้ข้อเท็จจริงนี้เลือกสถิติที่เหมาะสม

> **มาตรฐาน:** ค่าเฉลี่ย 24 ชั่วโมงของ PM2.5 ตามมาตรฐานไทย (มีผลปี 2566) คือ 37.5 µg/m³ ส่วนแนวทางของ WHO (2021) คือ 15 µg/m³ เส้นอ้างอิงทำให้ผู้อ่านตีความ "สูง/ต่ำ" ได้โดยไม่ต้องเดา

### Comparison: เทียบภาคต่าง ๆ

```python
order = daily.groupby("region")["pm25_mean"].median().sort_values().index
ax = sns.boxplot(data=daily, x="pm25_mean", y="region", order=order,
                 showfliers=False, color="lightsteelblue")
ax.axvline(THAI_STD, color="black", linestyle="--")
ax.set(xlabel="PM2.5 เฉลี่ย 24 ชม. (µg/m³)", ylabel="")
```

เรียงกลุ่มตามมัธยฐาน (ไม่ใช่ตามตัวอักษร) ทำให้อ่านลำดับได้ทันที และวางชื่อภาคบนแกน y เพื่อให้ป้ายภาษาไทยไม่ซ้อนกัน

### Time: รูปแบบตามฤดูกาล

```python
ax = sns.lineplot(data=daily, x="month", y="pm25_mean", hue="region",
                  estimator="median", errorbar=("pi", 50))   # แถบ = ช่วงระหว่าง Q1–Q3
ax.axhline(THAI_STD, color="black", linestyle="--")
ax.set(xlabel="เดือน", ylabel="มัธยฐาน PM2.5 (µg/m³)", xticks=range(1, 13))
```

`errorbar=("pi", 50)` แสดงช่วง percentile 25–75 ซึ่งบอกความผันแปรของข้อมูลจริง ต่างจาก `("ci", 95)` ที่บอกความไม่แน่นอนของค่าประมาณ ต้องเขียนกำกับให้ผู้อ่านรู้ว่าแถบหมายถึงอะไร

### Relationship: ค่าเฉลี่ยกับค่าสูงสุดรายวัน

```python
ax = sns.histplot(data=daily, x="pm25_mean", y="pm25_max", bins=80,
                  log_scale=True, cmap="mako")   # 2D histogram แทน scatter ที่ทับกัน
ax.set(xlabel="ค่าเฉลี่ย 24 ชม. (µg/m³)", ylabel="ค่าสูงสุดรายชั่วโมง (µg/m³)")
```

บันทึกภาพด้วย `fig.savefig("reports/figures/09_hist_pm25.png", dpi=150, bbox_inches="tight")` เพื่อใช้ต่อในรายงาน Quarto สัปดาห์ที่ 14

## 8. Altair (เสริม)

Altair เหมาะกับคนที่อยากเขียนตามไวยากรณ์ให้ชัด และได้ tooltip พื้นฐานมาฟรี แต่มีข้อจำกัดว่าข้อมูลถูกฝังลงในกราฟ จึงเตือนเมื่อเกิน 5,000 แถว ให้ **สรุปข้อมูลก่อน** เสมอ

```python
monthly = (daily.groupby(["region", "month"], as_index=False)["pm25_mean"].median())
line = alt.Chart(monthly).mark_line(point=True).encode(
    x=alt.X("month:O", title="เดือน"),
    y=alt.Y("pm25_mean:Q", title="มัธยฐาน PM2.5 (µg/m³)"),
    color=alt.Color("region:N", title="ภาค"),
)
rule = alt.Chart(pd.DataFrame({"y": [37.5]})).mark_rule(strokeDash=[4, 4]).encode(y="y:Q")
line + rule      # การซ้อนชั้น (layer) คือหลักของ grammar of graphics
```

| | seaborn | Altair |
|---|---|---|
| พื้นฐาน | matplotlib (ภาพนิ่ง) | Vega-Lite (เว็บ) |
| จุดเด่น | กราฟสถิติสำเร็จรูป ปรับแต่งด้วย matplotlib ได้ทุกจุด | ไวยากรณ์ชัด ซ้อนชั้นและ tooltip ง่าย |
| ข้อจำกัด | ไม่ interactive | ข้อมูลใหญ่ต้องสรุปก่อน |
| ใช้ในรายวิชา | **หลัก** | เสริม |

## สรุป

- เริ่มจากคำถามใน `questions.md` แล้วค่อยเลือกกราฟ กราฟทุกภาพต้องบอกได้ว่าตอบคำถามข้อใด
- grammar of graphics มองกราฟเป็น data + encoding + mark + scale + facet + coordinate
- ใช้ตำแหน่งสำหรับค่าที่ต้องเทียบแม่น ใช้สีให้ตรงชนิดข้อมูล และเลือก palette ที่คนตาบอดสีอ่านได้
- bar ต้องเริ่มที่ 0 หลีกเลี่ยงแกนคู่ และแก้ overplotting ด้วย alpha, 2D histogram หรือการสรุปข้อมูล
- ตั้ง font ไทยก่อนวาด และใส่เส้นมาตรฐาน 37.5 µg/m³ เป็นเส้นอ้างอิง

## คำถามทบทวน

1. แยกองค์ประกอบ grammar of graphics ของกราฟ "มัธยฐาน PM2.5 รายเดือน แยกสีตามภาค" ว่าแต่ละองค์ประกอบคืออะไร
2. ทำไม bar chart ต้องเริ่มที่ 0 แต่ line chart ไม่จำเป็น
3. ถ้าต้องการแสดงส่วนต่างของ PM2.5 จากมาตรฐาน 37.5 บน heatmap ควรใช้ palette ชนิดใด เพราะอะไร
4. ยกตัวอย่างว่าแกนคู่ทำให้ผู้อ่านเข้าใจความสัมพันธ์ระหว่าง PM2.5 กับตัวแปรอื่นผิดได้อย่างไร
5. ค่า `errorbar=("pi", 50)` กับ `("ci", 95)` ใน `sns.lineplot` สื่อความหมายต่างกันอย่างไร

## อ่านเพิ่มเติม

- Wilkinson, L. (2005). *The Grammar of Graphics* (2nd ed.). Springer.
- Cleveland, W. S., & McGill, R. (1984). Graphical Perception. *JASA*, 79(387), 531–554.
- Wilke, C. O. *Fundamentals of Data Visualization* — <https://clauswilke.com/dataviz/>
- เอกสาร seaborn (tutorial และ `seaborn.objects`) — <https://seaborn.pydata.org/tutorial.html>
- เอกสาร Altair — <https://altair-viz.github.io/>

➡️ [คู่มือปฏิบัติการสัปดาห์ที่ 9](lab.md)
