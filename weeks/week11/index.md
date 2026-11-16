---
title: "สัปดาห์ที่ 11: สถิติเชิงสำรวจและ time series"
---

> **CLO:** CLO4 · **เครื่องมือ:** SciPy, statsmodels (หลัก), pingouin (เสริม)
> **ผลงานที่เพิ่มในระบบ:** ผลทดสอบสมมติฐานและการแยก trend/seasonality ใน `notebooks/11_stats.ipynb` พร้อมข้อความสรุปผลใน `questions.md`
>
> **อ่านประกอบในหนังสือ:** บทที่ 13 [สถิติเชิงพรรณนาและการอนุมานเชิงสำรวจ](../../book/chapters/13-exploratory-statistics.html) · บทที่ 14 [การวิเคราะห์อนุกรมเวลาเชิงสำรวจ](../../book/chapters/14-time-series.html)

## วัตถุประสงค์การเรียนรู้

เมื่อจบสัปดาห์นี้ ผู้เรียนสามารถ

1. เลือกสถิติเชิงพรรณนาที่ทนต่อความเบ้ (median, IQR, percentile) และใช้ log transform กับ PM2.5 ได้อย่างมีเหตุผล
2. เปรียบเทียบสองกลุ่มด้วย t-test หรือ Mann-Whitney U และรายงาน effect size คู่กับ p-value
3. เลือกใช้ Pearson หรือ Spearman correlation และอธิบายได้ว่า autocorrelation ละเมิดสมมติฐานความเป็นอิสระอย่างไร
4. แยก trend / seasonality / remainder ด้วย STL ของ statsmodels หลังจัดการช่องว่างของข้อมูลแล้ว
5. อธิบายปัญหา multiple comparisons และ HARKing และใช้ข้อมูลปีที่กันไว้ (held-out) ยืนยันผล
6. เขียนสรุปผลด้วยถ้อยคำที่ตรงกับความหนักแน่นของหลักฐาน

---

## 1. จากเบาะแสสู่การทดสอบ

สัปดาห์ที่ 9–10 ให้ **เบาะแส** จากกราฟ เช่น "ภาคเหนือดูสูงกว่ากรุงเทพฯ ในฤดูแล้ง" สัปดาห์นี้เราถามต่อว่า *ความต่างนั้นใหญ่แค่ไหน และเชื่อได้แค่ไหน* ซึ่งเป็นการเปลี่ยนจาก "งานนักสืบ" ไปเป็น "งานศาล" ตามที่ Tukey เปรียบไว้ (สัปดาห์ที่ 1)

ข้อควรระวังสำคัญจากสัปดาห์ที่ 2: ถ้าใช้ข้อมูลชุดเดียวกันทั้ง *ตั้ง* สมมติฐานและ *ทดสอบ* สมมติฐาน ผลทดสอบจะดูดีเกินจริง เพราะเราเลือกคำถามที่ข้อมูลชุดนั้นตอบ "ใช่" อยู่แล้ว ทางแก้ที่ใช้ในรายวิชานี้คือ **แบ่งปี**

```text
ปีสำรวจ (exploration)          ปีที่กันไว้ (held-out)
├── ดูกราฟ ตั้งสมมติฐาน        ├── ไม่ดูก่อนเขียนสมมติฐานเสร็จ
├── เลือกวิธีทดสอบ              └── รันการทดสอบที่เขียนไว้แล้ว ครั้งเดียว
└── เขียนลง questions.md
```

## 2. สถิติเชิงพรรณนาที่ทนต่อความเบ้

กราฟสัปดาห์ที่ 9 แสดงว่า PM2.5 **เบ้ขวา** ค่าส่วนใหญ่ต่ำ แต่มีวันที่สูงมากในฤดูหมอกควัน ค่าเฉลี่ย (mean) และส่วนเบี่ยงเบนมาตรฐาน (SD) ถูกดึงด้วยค่าสุดขั้วเหล่านี้

| สถิติ | ทนต่อค่าสุดขั้ว | ใช้เมื่อ |
|---|---|---|
| mean, SD | ไม่ทน | ข้อมูลค่อนข้างสมมาตร หรือต้องการ "ปริมาณรวม" (เช่น ค่าเฉลี่ย 24 ชม. ตามนิยามมาตรฐาน) |
| **median** | ทน | ค่ากลางของข้อมูลเบ้ |
| **IQR** (Q3 − Q1) | ทน | การกระจายของข้อมูลเบ้ |
| percentile 90/95/99 | — | อธิบายหางขวา เช่น "วันแย่ที่สุด 10%" |
| สัดส่วนวันที่เกิน 37.5 | ทน | สื่อสารกับคนทั่วไป และผูกกับมาตรฐานโดยตรง |

```python
import duckdb, numpy as np, pandas as pd
from scipy import stats

con = duckdb.connect("data/pm25.duckdb", read_only=True)
con.sql("""
    SELECT s.region,
           count(*)                                  AS n_station_days,
           round(avg(d.pm25_mean), 1)                AS mean,
           round(median(d.pm25_mean), 1)             AS median,
           round(quantile_cont(d.pm25_mean, 0.75)
                 - quantile_cont(d.pm25_mean, 0.25), 1) AS iqr,
           round(quantile_cont(d.pm25_mean, 0.95), 1) AS p95,
           round(avg(CASE WHEN d.pm25_mean > 37.5 THEN 1 ELSE 0 END), 3) AS share_over_std
    FROM daily_pm25_clean AS d JOIN stations AS s USING (station_id)
    WHERE d.is_complete
    GROUP BY s.region ORDER BY median DESC
""").df()
```

ถ้า mean สูงกว่า median ชัดเจน แสดงว่ามีหางขวา ตรวจระดับความเบ้ด้วย `stats.skew(x)` (ค่า > 1 ถือว่าเบ้มาก)

### Log transform

การแปลง `log(pm25)` ทำให้การกระจายใกล้สมมาตรขึ้น ช่วยให้วิธีที่สมมติการแจกแจงปกติ (เช่น t-test) เหมาะสมขึ้น และทำให้ผลอ่านเป็น **อัตราส่วน** ได้ ซึ่งเข้ากับธรรมชาติของมลพิษ ("สูงกว่า 1.6 เท่า")

| ข้อควรระวัง | วิธีจัดการ |
|---|---|
| `log(0)` = −∞ | ตรวจว่ามีค่า 0 หรือไม่ ถ้ามีให้ใช้ `np.log1p` หรือกรองตามกฎใน data dictionary สัปดาห์ที่ 7 |
| ค่าเฉลี่ยของ log ไม่ใช่ log ของค่าเฉลี่ย | `exp(mean(log x))` คือ **geometric mean** ไม่ใช่ mean ปกติ ต้องเขียนกำกับ |
| ผู้อ่านทั่วไปไม่คุ้น log | รายงานผลกลับเป็นหน่วยเดิมหรือเป็นอัตราส่วน |

## 3. เปรียบเทียบสองกลุ่ม

ตัวอย่างสมมติฐาน (เขียนไว้ใน `questions.md` ก่อนทดสอบ): *ในฤดูแล้ง (ม.ค.–เม.ย.) ระดับ PM2.5 ของสถานีภาคเหนือสูงกว่าสถานีในกรุงเทพมหานคร*

### หน่วยการวิเคราะห์ (unit of analysis) ต้องมาก่อนเลือกการทดสอบ

ถ้านำค่ารายวันทุกวันของทุกสถานีเข้า t-test จะได้ n หลายหมื่น และ p-value เล็กมากเสมอ แต่ค่ารายวันของสถานีเดียวกัน *ไม่เป็นอิสระต่อกัน* (วันนี้สูง พรุ่งนี้ก็มักสูง ดูหัวข้อ 5) วิธีที่ซื่อตรงกว่าคือ **สรุปให้เหลือหนึ่งค่าต่อสถานี** แล้วเทียบสถานีกับสถานี

```python
units = con.sql("""
    SELECT d.station_id, s.region, s.province,
           median(d.pm25_mean) AS dry_median, count(*) AS n_days
    FROM daily_pm25_clean AS d JOIN stations AS s USING (station_id)
    WHERE d.is_complete AND month(d.date) BETWEEN 1 AND 4
      AND year(d.date) < 2025                 -- ปีสำรวจเท่านั้น (ปรับตามช่วงข้อมูลจริง)
    GROUP BY ALL
    HAVING count(*) >= 60                      -- สถานีต้องมีข้อมูลพอ
""").df()
north = units.loc[units["region"] == "ภาคเหนือ", "dry_median"]          # ตรวจค่าจริงด้วย SELECT DISTINCT region
bkk   = units.loc[units["province"] == "กรุงเทพมหานคร", "dry_median"]
len(north), len(bkk)
```

### t-test กับ Mann-Whitney U

| | Welch t-test | Mann-Whitney U |
|---|---|---|
| ทดสอบอะไร | ค่าเฉลี่ยของสองกลุ่มต่างกันหรือไม่ | ค่าจากกลุ่มหนึ่งมีแนวโน้มสูงกว่าอีกกลุ่มหรือไม่ (อิงลำดับ) |
| สมมติฐาน | ใกล้การแจกแจงปกติ หรือ n ใหญ่พอ, ความแปรปรวนต่างกันได้ | ไม่สมมติการแจกแจง |
| กับ PM2.5 | ใช้กับ `log(pm25)` | ใช้กับค่าเดิมได้เลย |
| SciPy | `stats.ttest_ind(a, b, equal_var=False)` | `stats.mannwhitneyu(a, b, alternative="two-sided")` |

ทั้งสองวิธี **สมมติว่าแต่ละค่าเป็นอิสระต่อกัน** ซึ่งเป็นเหตุผลที่ต้องสรุปเป็นค่าต่อสถานีก่อน

```python
t = stats.ttest_ind(np.log(north), np.log(bkk), equal_var=False)
u = stats.mannwhitneyu(north, bkk, alternative="two-sided")
print(t)
print(u)
```

### Effect size: ต่างกัน *เท่าไร* ไม่ใช่แค่ *ต่างหรือไม่*

p-value บอกว่าความต่างที่เห็น "ไม่น่าเกิดจากความบังเอิญ" แค่ไหน แต่ไม่ได้บอกว่าต่างมากหรือน้อย เมื่อ n ใหญ่ ความต่างเล็กน้อยก็ได้ p < 0.05 จึงต้องรายงาน effect size เสมอ

```python
ratio = np.exp(np.log(north).mean() - np.log(bkk).mean())       # อัตราส่วน geometric mean
pooled_sd = np.sqrt((np.log(north).var(ddof=1) + np.log(bkk).var(ddof=1)) / 2)
cohen_d = (np.log(north).mean() - np.log(bkk).mean()) / pooled_sd
cles = u.statistic / (len(north) * len(bkk))   # P(สถานีเหนือ > สถานี กทม.) เมื่อสุ่มอย่างละหนึ่ง
print(f"ratio={ratio:.2f}  d={cohen_d:.2f}  CLES={cles:.2f}")
```

| effect size | อ่านว่า | ตัวอย่างการรายงาน |
|---|---|---|
| ratio ของ geometric mean | กลุ่มหนึ่งสูงเป็นกี่เท่าของอีกกลุ่ม | "สูงกว่าประมาณ 1.6 เท่า" |
| Cohen's d (บน log) | ต่างกันกี่ SD (0.2 เล็ก, 0.5 กลาง, 0.8 ใหญ่ เป็นเกณฑ์คร่าว ๆ) | "d = 0.9" |
| CLES (common-language effect size) | ความน่าจะเป็นที่ค่าจากกลุ่มแรกสูงกว่า | "สถานีภาคเหนือสูงกว่าสถานี กทม. ใน 78% ของคู่ที่สุ่ม" |

**pingouin (เสริม)** คำนวณ effect size ให้พร้อมในตารางเดียว เหมาะสำหรับตรวจทานตัวเลขที่คำนวณเอง

```python
import pingouin as pg
pg.mwu(north, bkk)                  # มี RBC (rank-biserial) และ CLES
pg.ttest(np.log(north), np.log(bkk)) # มี CI95, cohen_d, power
```

> ชื่อคอลัมน์ของผลจาก pingouin ต่างกันในแต่ละเวอร์ชัน (เช่น `p-val` กับ `p_val`) ให้พิมพ์ทั้งตารางดูก่อนเลือกคอลัมน์

## 4. Correlation: Pearson กับ Spearman

| | Pearson r | Spearman ρ |
|---|---|---|
| วัดอะไร | ความสัมพันธ์ *เชิงเส้น* | ความสัมพันธ์ *ทางเดียว* (monotonic) อิงลำดับ |
| ไวต่อค่าสุดขั้ว | ไวมาก จุดสุดขั้วไม่กี่จุดเปลี่ยนค่าได้มาก | ทน |
| กับ PM2.5 | ใช้กับ log ได้ | ใช้กับค่าเดิมได้ |
| SciPy | `stats.pearsonr(x, y)` | `stats.spearmanr(x, y)` |

```python
pair = con.sql("""
    SELECT pm25, pm10 FROM measurements
    WHERE pm25 > 0 AND pm10 > 0
    USING SAMPLE 1% (bernoulli, 42)
""").df()
print(stats.pearsonr(pair["pm25"], pair["pm10"]))
print(stats.spearmanr(pair["pm25"], pair["pm10"]))
```

ข้อควรจำ: correlation สูงระหว่างสองตัวแปรที่มีฤดูกาลเหมือนกัน (เช่น PM2.5 ที่เชียงใหม่กับจำนวนผู้ป่วยโรคทางเดินหายใจ) อาจเกิดเพียงเพราะทั้งคู่สูงในฤดูแล้ง ไม่ใช่เพราะเกี่ยวข้องกันโดยตรง วิธีตรวจคือหาความสัมพันธ์ของ **remainder** หลังตัด seasonality ออก (หัวข้อ 6)

## 5. Autocorrelation ใน time series

**Autocorrelation** คือ correlation ของอนุกรมกับตัวเองที่เลื่อนเวลาไป (lag) PM2.5 วันนี้สัมพันธ์กับเมื่อวานสูงมาก เพราะสภาพอากาศและการเผาไม่ได้เปลี่ยนทันทีทุกวัน

```python
from statsmodels.graphics.tsaplots import plot_acf

one = con.execute("SELECT date, pm25_mean FROM daily_pm25_clean WHERE is_complete AND station_id = ? ORDER BY date",
                  ["<station_id>"]).df()
y = one.set_index(pd.to_datetime(one["date"]))["pm25_mean"].asfreq("D")   # ให้มีทุกวัน ช่องว่างเป็น NaN
plot_acf(np.log(y), lags=60, missing="conservative")
```

| ผลของ autocorrelation | ความหมาย |
|---|---|
| ข้อมูล 365 วันไม่ได้มีข้อมูล "อิสระ" 365 ชิ้น | **effective sample size** น้อยกว่าจำนวนแถวมาก |
| t-test / correlation บนค่ารายวันให้ p-value เล็กเกินจริง | ความเชื่อมั่นสูงเกินกว่าที่ข้อมูลรองรับ |
| สองอนุกรมที่มี trend หรือฤดูกาลมัก correlate กันเอง | spurious correlation |

ทางแก้ระดับรายวิชา: สรุปเป็นหน่วยที่ใกล้อิสระ (ค่าต่อสถานี ต่อฤดู ต่อปี) แยก seasonality ออกก่อนหาความสัมพันธ์ และยืนยันผลด้วยปีที่กันไว้ วิธีที่ซับซ้อนกว่า (เช่น block bootstrap หรือโมเดล ARIMA) อยู่นอกขอบเขตรายวิชานี้

## 6. แยก trend และ seasonality ด้วย STL

**STL** (Seasonal-Trend decomposition using LOESS; Cleveland et al., 1990) แยกอนุกรมเวลาเป็นสามส่วน

```text
y(t) = trend(t) + seasonal(t) + remainder(t)        (บน log: อ่านเป็นผลคูณ)
```

### จัดการช่องว่างก่อน

STL ต้องการอนุกรมที่ **ระยะห่างเท่ากันและไม่มีค่าหาย** ข้อมูล PM2.5 มีช่องว่างจากเครื่องเสีย (สัปดาห์ที่ 7) จึงต้องตัดสินใจก่อน

| ขั้น | ทำอะไร |
|---|---|
| 1. เลือกความละเอียด | รายเดือนเหมาะกับ trend หลายปีและฤดูกาลรายปี (`period=12`) รายวันใช้ได้ แต่ช่องว่างมากกว่า |
| 2. ทำให้ระยะห่างเท่ากัน | `asfreq("MS")` หรือ `asfreq("D")` ช่วงที่หายจะกลายเป็น NaN ให้เห็นชัด |
| 3. กำหนดเกณฑ์ความครบ | เช่น เดือนที่มีข้อมูลน้อยกว่า 20 วันถือเป็น NaN |
| 4. เติมเฉพาะช่องว่างสั้น | `interpolate(limit=2)` ถ้ายังมีช่องว่างยาว ให้เลือกช่วงเวลาที่ต่อเนื่องแทนการเติมมั่ว |
| 5. บันทึกการตัดสินใจ | เขียนใน notebook ว่าเติมกี่จุด เพราะอะไร |

```python
from statsmodels.tsa.seasonal import STL

m = con.execute("""
    SELECT date_trunc('month', date) AS month, avg(pm25_mean) AS pm25, count(*) AS n_days
    FROM daily_pm25_clean WHERE is_complete AND station_id = ?
    GROUP BY ALL ORDER BY month
""", ["<station_id>"]).df()
s = m.set_index(pd.to_datetime(m["month"])).asfreq("MS")
s.loc[s["n_days"] < 20, "pm25"] = np.nan
y = np.log(s["pm25"]).interpolate(limit=2)
print("ยังเหลือ NaN:", y.isna().sum())          # ต้องเป็น 0 ก่อนเข้า STL

res = STL(y, period=12, robust=True).fit()     # robust=True ลดอิทธิพลของเดือนผิดปกติ
res.plot()
```

### อ่านผล STL

```python
strength_trend    = max(0, 1 - res.resid.var() / (res.trend + res.resid).var())
strength_seasonal = max(0, 1 - res.resid.var() / (res.seasonal + res.resid).var())
print(f"trend strength={strength_trend:.2f}, seasonal strength={strength_seasonal:.2f}")
```

ค่า strength (Hyndman & Athanasopoulos) อยู่ระหว่าง 0–1 ค่าใกล้ 1 แปลว่าส่วนนั้นอธิบายความผันแปรได้มาก สำหรับสถานีภาคเหนือ คาดว่า seasonal strength สูงมาก ส่วน trend บอกว่าปีหลัง ๆ ดีขึ้นหรือแย่ลง **แต่ trend จากข้อมูลไม่กี่ปีเป็นเพียงคำบรรยาย ไม่ใช่การพยากรณ์**

## 7. Multiple comparisons, HARKing และ held-out years

ถ้าทดสอบ 80 สถานี สถานีละหนึ่งครั้งที่ α = 0.05 แม้ไม่มีความต่างจริงเลย ก็คาดว่าจะได้ผล "มีนัยสำคัญ" ประมาณ 4 สถานีโดยบังเอิญ

| แนวทาง | ทำอย่างไร |
|---|---|
| ลดจำนวนการทดสอบ | ทดสอบเฉพาะสมมติฐานที่เขียนไว้ใน `questions.md` ก่อนดูผล |
| ปรับ p-value | `multipletests(pvals, method="holm")` (คุม family-wise error) หรือ `"fdr_bh"` (คุม false discovery rate) |
| กันข้อมูลไว้ยืนยัน | ทดสอบซ้ำกับปีที่ไม่ได้ใช้สำรวจ |

```python
from statsmodels.stats.multitest import multipletests
reject, p_adj, _, _ = multipletests(pvals, method="holm")
```

**HARKing** (Hypothesizing After the Results are Known) คือการเห็นผลก่อนแล้วเขียนสมมติฐานย้อนหลังให้ดูเหมือนตั้งไว้ตั้งแต่แรก (สัปดาห์ที่ 2) ป้องกันด้วยการ commit `questions.md` ที่มีสมมติฐาน วิธีทดสอบ และปี held-out **ก่อน** รันการทดสอบกับปี held-out ประวัติ Git จะเป็นหลักฐานว่าเขียนไว้ก่อน

## 8. เขียนผลให้ตรงกับความหนักแน่นของหลักฐาน

| ความหนักแน่นของหลักฐาน | ถ้อยคำที่เหมาะ | ถ้อยคำที่เกินหลักฐาน |
|---|---|---|
| เห็นจากกราฟเท่านั้น | "กราฟชี้ว่า…", "ดูเหมือนว่า…" | "พิสูจน์ว่า…" |
| ทดสอบในปีสำรวจ มีนัยสำคัญ effect ใหญ่ | "ในปี 2563–2567 สถานีภาคเหนือมี PM2.5 ฤดูแล้งสูงกว่า กทม. ประมาณ 1.6 เท่า (Mann-Whitney p = 0.002, CLES = 0.78, n = 18 และ 12 สถานี)" | "ภาคเหนือมีมลพิษมากกว่า กทม. เสมอ" |
| ยืนยันซ้ำใน held-out year | "ผลเดียวกันพบในปี 2568 ที่ไม่ได้ใช้ตั้งสมมติฐาน" | — |
| p ≥ 0.05 | "ข้อมูลไม่เพียงพอที่จะสรุปว่าต่างกัน" | "ไม่มีความแตกต่าง" |
| correlation | "สัมพันธ์กัน" | "เป็นสาเหตุ", "ทำให้" |

รายงานผลที่ดีมี: **ขนาดผล + หน่วย + ช่วงเวลา/ประชากร + วิธี + p-value + n + ข้อจำกัด**

## สรุป

- PM2.5 เบ้ขวา ใช้ median, IQR, percentile และสัดส่วนวันที่เกิน 37.5 และพิจารณา log transform
- เลือกหน่วยการวิเคราะห์ที่ใกล้อิสระก่อนทดสอบ แล้วรายงาน effect size คู่กับ p-value เสมอ
- Spearman ทนต่อค่าสุดขั้วกว่า Pearson และ autocorrelation ทำให้ p-value จากค่ารายวันเชื่อถือไม่ได้
- STL แยก trend / seasonal / remainder ได้ แต่ต้องจัดการช่องว่างและบันทึกการตัดสินใจก่อน
- ตั้งสมมติฐานก่อนดูผล ปรับ p-value เมื่อทดสอบหลายครั้ง ยืนยันด้วยปี held-out และเขียนผลไม่เกินหลักฐาน

## คำถามทบทวน

1. ทำไมค่า mean ของ PM2.5 ทั้งปีจึงมักสูงกว่า median และควรรายงานค่าใดเมื่อสื่อสารกับประชาชน
2. ถ้านำค่ารายวัน 20,000 แถวเข้า Mann-Whitney แล้วได้ p < 0.001 ทำไมยังสรุปไม่ได้ว่าผลหนักแน่น
3. Cohen's d = 0.1 กับ p = 0.0001 ควรตีความอย่างไร
4. ยกตัวอย่าง spurious correlation ที่เกิดจาก seasonality ในข้อมูล PM2.5 และวิธีตรวจสอบ
5. ถ้าเดือนมีนาคมปีหนึ่งของสถานีที่เลือกหายทั้งเดือน ควรจัดการอย่างไรก่อนเข้า STL
6. เขียนประโยคสรุปผลที่เหมาะสมเมื่อการทดสอบในปีสำรวจมีนัยสำคัญ แต่ใน held-out year ไม่มีนัยสำคัญ

## อ่านเพิ่มเติม

- Hyndman, R. J., & Athanasopoulos, G. *Forecasting: Principles and Practice* (3e), บท "Time series decomposition" — <https://otexts.com/fpp3/>
- Cleveland, R. B. et al. (1990). STL: A Seasonal-Trend Decomposition Procedure Based on Loess. *Journal of Official Statistics*, 6(1), 3–73.
- Wasserstein, R. L., & Lazar, N. A. (2016). The ASA Statement on p-Values. *The American Statistician*, 70(2).
- Kerr, N. L. (1998). HARKing: Hypothesizing After the Results are Known. *Personality and Social Psychology Review*, 2(3).
- เอกสาร `scipy.stats` — <https://docs.scipy.org/doc/scipy/reference/stats.html> และ statsmodels STL — <https://www.statsmodels.org/stable/examples/notebooks/generated/stl_decomposition.html>

➡️ [คู่มือปฏิบัติการสัปดาห์ที่ 11](lab.md)
