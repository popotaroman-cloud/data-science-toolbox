---
title: "ปฏิบัติการสัปดาห์ที่ 9: กราฟ univariate และ bivariate ที่ตอบคำถาม"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO4
> **ผลงานที่ต้องส่ง:** `src/viz_style.py` + `notebooks/09_static_viz.ipynb` ที่มีกราฟอย่างน้อย 4 ภาพ (univariate ≥ 2, bivariate ≥ 2) แต่ละภาพผูกกับคำถามใน `questions.md` และมี pull request ที่เพื่อน review แล้ว

## สิ่งที่ต้องเตรียม

- pipeline จาก Checkpoint 1 (สัปดาห์ที่ 8) ทำงานได้ และมี `data/pm25.duckdb` ที่มีตาราง `stations`, `measurements` และ view `daily_pm25_clean`
- `questions.md` ที่มีคำถามเชิงวิเคราะห์ (สัปดาห์ที่ 2) และกฎ pandera ที่ผ่านแล้ว (สัปดาห์ที่ 6–7)
- ถ้าฐานข้อมูลของตนเองยังไม่สมบูรณ์ ให้ใช้ **ไฟล์ตัวอย่างจากผู้สอน** `data/sample/pm25_sample.duckdb` แทนชั่วคราว (เปลี่ยนชื่อไฟล์ในโค้ด) และระบุใน PR ว่าใช้ข้อมูลตัวอย่าง
- ทดสอบว่าไลบรารีพร้อม: `python -c "import seaborn, altair; print(seaborn.__version__)"` (ควรเป็น 0.13 ขึ้นไป)

---

## ขั้นที่ 1: สร้าง branch และโฟลเดอร์สำหรับภาพ

```bash
git switch main
git pull
git switch -c week09-static-viz
mkdir -p reports/figures
```

## ขั้นที่ 2: สร้าง `src/viz_style.py` สำหรับ font ไทยและธีมกลาง

ตรวจก่อนว่าเครื่องมี font ไทยอะไร

```python
from matplotlib import font_manager
sorted({f.name for f in font_manager.fontManager.ttflist if "Thai" in f.name or f.name in ("Tahoma", "Sarabun", "Leelawadee UI", "Thonburi")})
```

แล้วสร้างไฟล์ `src/viz_style.py`

```python
"""ธีมกลางของกราฟในโครงการ: font ไทย palette และค่ามาตรฐาน"""
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager

THAI_STD = 37.5   # มาตรฐาน PM2.5 เฉลี่ย 24 ชม. ของไทย (µg/m³)
WHO_GUIDE = 15    # แนวทาง WHO 2021 (µg/m³)

CANDIDATES = ["Sarabun", "Tahoma", "Leelawadee UI", "Thonburi", "Noto Sans Thai", "Loma"]


def setup(font_path: str | None = None) -> str:
    """ตั้งธีม seaborn ด้วย font ไทยตัวแรกที่หาเจอ แล้วคืนชื่อ font ที่ใช้"""
    if font_path:                                   # เช่น Colab: ไฟล์ Sarabun-Regular.ttf
        font_manager.fontManager.addfont(font_path)
    available = {f.name for f in font_manager.fontManager.ttflist}
    font = next((f for f in CANDIDATES if f in available), None)
    if font is None:
        raise RuntimeError("ไม่พบ font ไทย ให้ติดตั้ง Sarabun แล้วส่ง font_path")
    sns.set_theme(style="whitegrid", palette="colorblind", font=font)
    plt.rcParams["axes.unicode_minus"] = False
    return font


def add_std_line(ax, axis: str = "y", who: bool = False):
    """วาดเส้นมาตรฐาน 37.5 (และ WHO 15 ถ้าต้องการ) พร้อมป้าย"""
    line = ax.axhline if axis == "y" else ax.axvline
    line(THAI_STD, color="black", linestyle="--", linewidth=1)
    if who:
        line(WHO_GUIDE, color="gray", linestyle=":", linewidth=1)
    if axis == "y":
        ax.annotate("มาตรฐานไทย 37.5", xy=(1, THAI_STD), xycoords=("axes fraction", "data"),
                    ha="right", va="bottom", fontsize=9)
    else:
        ax.annotate("มาตรฐานไทย 37.5", xy=(THAI_STD, 1), xycoords=("data", "axes fraction"),
                    ha="left", va="top", fontsize=9)
```

## ขั้นที่ 3: เปิด notebook และโหลดข้อมูล

สร้าง `notebooks/09_static_viz.ipynb` cell แรกให้ตั้ง working directory เป็น root ของ repo เพื่อให้ path `data/...` และ `src/...` ใช้ได้

```python
import os, sys
if os.path.basename(os.getcwd()) == "notebooks":
    os.chdir("..")
sys.path.append("src")

import duckdb, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
import viz_style
print("ใช้ font:", viz_style.setup())

con = duckdb.connect("data/pm25.duckdb", read_only=True)
con.sql("SELECT DISTINCT region FROM stations ORDER BY region").df()   # ดูค่าจริงของคอลัมน์ region ก่อน
```

```python
daily = con.sql("""
    SELECT d.station_id, d.date, d.pm25_mean, d.pm25_max, d.n_hours,
           s.name_th, s.province, s.region
    FROM daily_pm25_clean AS d JOIN stations AS s USING (station_id)
    WHERE d.is_complete
""").df()
daily["date"] = pd.to_datetime(daily["date"])
daily["month"] = daily["date"].dt.month
daily["year"] = daily["date"].dt.year
daily.info()
```

> ตรวจ `daily.info()` ว่า `pm25_mean` เป็นตัวเลขและ `date` เป็น datetime ถ้าไม่ใช่ แปลว่า view ในสัปดาห์ที่ 7 มีปัญหา ให้แก้ที่ต้นทาง ไม่ใช่แก้ใน notebook

## ขั้นที่ 4: เขียนหัว section ที่ผูกกับคำถาม

ก่อนวาดแต่ละภาพ ให้มี Markdown cell รูปแบบนี้ (ใช้หมายเลขคำถามจริงใน `questions.md` ของตนเอง)

```markdown
### Q1: PM2.5 รายวันกระจายตัวอย่างไร และเกินมาตรฐานบ่อยแค่ไหน
- ชนิดคำถาม: distribution
- กราฟ: histogram (log scale) + ECDF
- encoding: x = pm25_mean
```

## ขั้นที่ 5: กราฟ univariate (อย่างน้อย 2 ภาพ)

**5.1 Histogram แบบ log scale พร้อมเส้นมาตรฐาน**

```python
fig, ax = plt.subplots(figsize=(8, 4))
sns.histplot(data=daily, x="pm25_mean", bins=60, log_scale=True, ax=ax)
viz_style.add_std_line(ax, axis="x", who=True)
ax.set(xlabel="PM2.5 เฉลี่ย 24 ชม. (µg/m³, log scale)", ylabel="จำนวนสถานี-วัน")
fig.savefig("reports/figures/09_hist_pm25.png", dpi=150, bbox_inches="tight")
```

**5.2 ECDF แยกภาค** ตอบว่า "สัดส่วนวันที่เกินมาตรฐานของแต่ละภาคเป็นเท่าไร"

```python
fig, ax = plt.subplots(figsize=(8, 4))
sns.ecdfplot(data=daily, x="pm25_mean", hue="region", ax=ax)
viz_style.add_std_line(ax, axis="x")
ax.set(xlabel="PM2.5 เฉลี่ย 24 ชม. (µg/m³)", ylabel="สัดส่วนสะสม", xlim=(0, 150))

# ตรวจตัวเลขที่อ่านจากภาพด้วยการคำนวณ
daily.assign(over=daily["pm25_mean"] > viz_style.THAI_STD).groupby("region")["over"].mean().round(3)
```

## ขั้นที่ 6: กราฟ bivariate (อย่างน้อย 2 ภาพ)

**6.1 Comparison: boxplot แยกภาค เรียงตามมัธยฐาน**

```python
order = daily.groupby("region")["pm25_mean"].median().sort_values().index
fig, ax = plt.subplots(figsize=(8, 4))
sns.boxplot(data=daily, x="pm25_mean", y="region", order=order, showfliers=False,
            color="lightsteelblue", ax=ax)
viz_style.add_std_line(ax, axis="x")
ax.set(xlabel="PM2.5 เฉลี่ย 24 ชม. (µg/m³)", ylabel="")
```

**6.2 Time: heatmap เดือน × ปี ของภาคที่สนใจ** (sequential palette)

```python
region = order[-1]     # ภาคที่มัธยฐานสูงสุด หรือเลือกตามคำถามของตนเอง
pivot = (daily[daily["region"] == region]
         .pivot_table(index="year", columns="month", values="pm25_mean", aggfunc="median"))
fig, ax = plt.subplots(figsize=(9, 3.5))
sns.heatmap(pivot, cmap="rocket_r", annot=True, fmt=".0f", cbar_kws={"label": "µg/m³"}, ax=ax)
ax.set(title=f"มัธยฐาน PM2.5 รายเดือน: {region}", xlabel="เดือน", ylabel="ปี")
```

**6.3 (เลือกทำ) Relationship: ค่าเฉลี่ยกับค่าสูงสุดรายวัน** ใช้ 2D histogram แทน scatter

```python
sns.histplot(data=daily, x="pm25_mean", y="pm25_max", bins=80, log_scale=True, cmap="mako")
```

## ขั้นที่ 7: แก้กราฟที่หลอกตา 1 ภาพ

วาดกราฟ "ผิด" แล้ววาดฉบับแก้ไขเคียงกัน เพื่อฝึกมองเห็นปัญหา

```python
top = daily.groupby("province")["pm25_mean"].mean().nlargest(5).reset_index()
fig, (bad, good) = plt.subplots(1, 2, figsize=(11, 4))
sns.barplot(data=top, x="pm25_mean", y="province", ax=bad)
bad.set_xlim(top["pm25_mean"].min() - 2, None)          # ตัดแกน = ผิด
bad.set_title("ผิด: แกนไม่เริ่มที่ 0")
sns.barplot(data=top, x="pm25_mean", y="province", ax=good)
good.set_xlim(0, None)
good.set_title("ถูก: แกนเริ่มที่ 0")
```

เขียน Markdown 2–3 บรรทัดใต้ภาพว่าภาพซ้ายทำให้ผู้อ่านเข้าใจผิดอย่างไร

## ขั้นที่ 8: (เสริม) ทำกราฟหนึ่งภาพซ้ำด้วย Altair

```python
import altair as alt
monthly = daily.groupby(["region", "month"], as_index=False)["pm25_mean"].median()
line = alt.Chart(monthly).mark_line(point=True).encode(
    x=alt.X("month:O", title="เดือน"), y=alt.Y("pm25_mean:Q", title="มัธยฐาน PM2.5 (µg/m³)"),
    color=alt.Color("region:N", title="ภาค"), tooltip=["region", "month", "pm25_mean"])
rule = alt.Chart(pd.DataFrame({"y": [37.5]})).mark_rule(strokeDash=[4, 4]).encode(y="y:Q")
line + rule
```

## ขั้นที่ 9: เขียนข้อสังเกตและอัปเดต `questions.md`

ใต้กราฟแต่ละภาพ เขียน **ข้อสังเกต** 1–3 ข้อ โดยใช้คำที่บอกว่าเป็นเบาะแส เช่น "ภาพนี้ชี้ว่า…", "ดูเหมือนว่า…" ไม่ใช่ "พิสูจน์ว่า…" แล้วเพิ่มลิงก์ภาพใน `questions.md` ใต้คำถามที่เกี่ยวข้อง เช่น

```markdown
- กราฟ: `reports/figures/09_hist_pm25.png` (สัปดาห์ที่ 9) — ข้อสังเกต: …
- ต้องทดสอบต่อในสัปดาห์ที่ 11: …
```

## ขั้นที่ 10: commit, push และเปิด pull request

ก่อน commit ให้ **Restart Kernel and Run All** เพื่อยืนยันว่า notebook รันจากบนลงล่างได้

```bash
git status
git add src/viz_style.py notebooks/09_static_viz.ipynb reports/figures/*.png questions.md AI_USAGE.md
git commit -m "เพิ่มกราฟ univariate/bivariate ของ PM2.5 พร้อมเส้นมาตรฐาน 37.5"
git push -u origin week09-static-viz
```

เปิด PR บน GitHub ขอ review จากเพื่อน 1 คน เมื่อได้ approve แล้วจึง merge

## ขั้นที่ 11: review PR ของเพื่อน

- [ ] กราฟทุกภาพมีหัวข้อที่บอกว่าตอบคำถามข้อใดใน `questions.md`
- [ ] ป้ายภาษาไทยแสดงถูกต้อง ไม่มีสี่เหลี่ยม และแกนมีหน่วย µg/m³
- [ ] bar chart เริ่มที่ 0 ไม่มีแกนคู่ และ scatter ไม่ทับกันจนอ่านไม่ออก
- [ ] palette เหมาะกับชนิดข้อมูล (categorical / sequential / diverging) และไม่พึ่งคู่สีแดง-เขียว
- [ ] มีเส้นมาตรฐาน 37.5 ในกราฟที่เกี่ยวกับระดับ PM2.5
- [ ] ข้อสังเกตใช้ถ้อยคำที่ไม่อ้างเกินหลักฐาน

เขียนความคิดเห็นที่เจาะจงอย่างน้อย 1 ข้อ เช่น "ภาพ ECDF ควรจำกัด xlim เพราะหางยาวทำให้ช่วง 0–50 แคบ"

---

## Checklist ก่อนส่งงาน

- [ ] `src/viz_style.py` import ได้ และ `setup()` คืนชื่อ font ไทย
- [ ] `notebooks/09_static_viz.ipynb` รัน Restart & Run All ผ่าน
- [ ] มีกราฟ univariate ≥ 2 และ bivariate ≥ 2 แต่ละภาพผูกกับคำถาม
- [ ] มีภาพ "ผิด vs ถูก" 1 คู่ พร้อมคำอธิบาย
- [ ] ภาพสำคัญบันทึกใน `reports/figures/` และ `questions.md` อัปเดตแล้ว
- [ ] ไม่ได้ commit `data/` หรือไฟล์ `.duckdb`
- [ ] บันทึกการใช้ AI ใน `AI_USAGE.md` (ถ้ามี)
- [ ] PR ถูก review และ merge แล้ว

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| ป้ายภาษาไทยเป็นสี่เหลี่ยม □□□ | font ไม่มีอักษรไทย ให้เรียก `viz_style.setup()` *ก่อน* วาด ถ้ายังไม่หายให้ลบ cache ของ matplotlib (โฟลเดอร์ที่ได้จาก `matplotlib.get_cachedir()`) แล้ว restart kernel |
| สระ/วรรณยุกต์ลอยหรือซ้อนผิดตำแหน่ง | font บางตัวจัดวางอักษรไทยไม่ดี ให้ลอง Sarabun หรือ Tahoma |
| `IOException: Could not set lock on file` | มีโปรแกรมอื่นเปิดไฟล์ DuckDB แบบเขียนอยู่ ปิด connection อื่นหรือใช้ `read_only=True` ทุก notebook |
| `IO Error: Cannot open file "data/pm25.duckdb"` | notebook รันจากโฟลเดอร์ `notebooks/` ให้รัน cell `os.chdir("..")` ในขั้นที่ 3 |
| `ModuleNotFoundError: viz_style` | ยังไม่ได้ `sys.path.append("src")` หรือ working directory ไม่ใช่ root ของ repo |
| Altair แจ้ง `MaxRowsError` | ข้อมูลเกิน 5,000 แถว ให้ `groupby` สรุปก่อนวาด |
| boxplot แสดงภาคเรียงตามตัวอักษร | ส่ง `order=` ที่เรียงตามมัธยฐาน |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 10)

1. อ่าน *Fundamentals of Data Visualization* บท "Visualizing distributions" และ "Color basics"
2. ลองเปิด <https://plotly.com/python/plotly-express/> แล้วดูตัวอย่าง `px.line` และ `px.scatter`
3. ใช้ SQL นับจำนวนแถวของ `measurements` (`SELECT count(*) FROM measurements`) จดไว้ จะใช้ตัดสินใจเรื่องข้อมูลขนาดใหญ่ในสัปดาห์ที่ 10
4. เลือกกราฟจากสัปดาห์นี้ 1 ภาพที่คิดว่า "ถ้า hover ดูค่าได้จะช่วยตอบคำถามได้ดีขึ้น" และเขียนเหตุผลสั้น ๆ
