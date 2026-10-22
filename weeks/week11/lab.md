---
title: "ปฏิบัติการสัปดาห์ที่ 11: ทดสอบสมมติฐานและแยก trend/seasonality ของ PM2.5"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO4
> **ผลงานที่ต้องส่ง:** `notebooks/11_stats.ipynb` ที่มีผลทดสอบสมมติฐานอย่างน้อย 2 ข้อ (พร้อม effect size และการยืนยันด้วยปี held-out) และ STL decomposition อย่างน้อย 1 สถานี + `questions.md` ที่มีสมมติฐาน (commit ก่อนทดสอบ) และข้อความสรุปผล พร้อม pull request ที่เพื่อน review แล้ว

## สิ่งที่ต้องเตรียม

- งานสัปดาห์ที่ 9–10 merge แล้ว และมีข้อสังเกตจากกราฟที่ต้องการทดสอบ (งานศึกษาด้วยตนเองสัปดาห์ที่ 10)
- `data/pm25.duckdb` ที่มี `daily_pm25_clean` อย่างน้อย 3 ปี (ถ้าข้อมูลของตนเองไม่ถึง ให้ใช้ไฟล์ตัวอย่างจากผู้สอนใน `data/sample/` และระบุใน PR)
- ตรวจช่วงปีของข้อมูล: `SELECT min(date), max(date) FROM daily_pm25_clean`
- ทดสอบไลบรารี: `python -c "import scipy, statsmodels; print(scipy.__version__, statsmodels.__version__)"` และ (เสริม) `python -c "import pingouin"`

---

## ขั้นที่ 1: สร้าง branch

```bash
git switch main
git pull
git switch -c week11-stats
```

## ขั้นที่ 2: เขียนสมมติฐานและ commit ก่อนทดสอบ (กัน HARKing)

เพิ่ม section ใหม่ใน `questions.md` ก่อนเปิด notebook ปรับปีให้ตรงกับข้อมูลจริง โดยกันปีล่าสุดไว้ 1 ปี

```markdown
## สมมติฐานสำหรับสัปดาห์ที่ 11 (เขียนก่อนทดสอบ)

ปีสำรวจ: 2563–2567 (2020–2024) · ปี held-out: 2568 (2025)
ฤดูแล้ง = ม.ค.–เม.ย. · ฤดูฝน = มิ.ย.–ก.ย. · หน่วยการวิเคราะห์ = มัธยฐานรายสถานี

- H1: ฤดูแล้ง สถานีภาคเหนือมี PM2.5 สูงกว่าสถานีในกรุงเทพมหานคร
  วิธี: Mann-Whitney U (หลัก), Welch t-test บน log (ประกอบ), effect size = ratio ของ geometric mean และ CLES
- H2: สถานีภาคเหนือมี PM2.5 ฤดูแล้งสูงกว่าฤดูฝน (จับคู่รายสถานี)
  วิธี: Wilcoxon signed-rank, effect size = มัธยฐานของอัตราส่วนแล้ง/ฝน
- เกณฑ์: α = 0.05 ปรับด้วย Holm เมื่อทดสอบหลายภาค
```

```bash
git add questions.md
git commit -m "บันทึกสมมติฐานและปี held-out ก่อนทดสอบ (สัปดาห์ที่ 11)"
```

> commit นี้เป็นหลักฐานว่าสมมติฐานเขียนไว้ก่อนเห็นผล ห้ามแก้ส่วนนี้ย้อนหลัง ถ้าเปลี่ยนใจให้เพิ่มหมายเหตุพร้อมเหตุผลแทน

## ขั้นที่ 3: เปิด notebook และตั้งค่า

สร้าง `notebooks/11_stats.ipynb`

```python
import os, sys
if os.path.basename(os.getcwd()) == "notebooks":
    os.chdir("..")
sys.path.append("src")

import duckdb, numpy as np, pandas as pd, matplotlib.pyplot as plt
from scipy import stats
import viz_style
viz_style.setup()

con = duckdb.connect("data/pm25.duckdb", read_only=True)
EXPLORE = (2020, 2024)      # ให้ตรงกับที่เขียนใน questions.md
HOLDOUT = (2025, 2025)
DRY, WET = (1, 4), (6, 9)   # ช่วงเดือน
NORTH = "ภาคเหนือ"           # ตรวจด้วย SELECT DISTINCT region FROM stations
BKK = "กรุงเทพมหานคร"
```

## ขั้นที่ 4: สถิติเชิงพรรณนาที่ทนต่อความเบ้

```python
desc = con.sql("""
    SELECT s.region, count(*) AS n,
           round(avg(d.pm25_mean), 1) AS mean, round(median(d.pm25_mean), 1) AS median,
           round(quantile_cont(d.pm25_mean, 0.75) - quantile_cont(d.pm25_mean, 0.25), 1) AS iqr,
           round(quantile_cont(d.pm25_mean, 0.95), 1) AS p95,
           round(avg(CASE WHEN d.pm25_mean > 37.5 THEN 1 ELSE 0 END), 3) AS share_over_std
    FROM daily_pm25_clean AS d JOIN stations AS s USING (station_id)
    GROUP BY s.region ORDER BY median DESC
""").df()
desc
```

```python
x = con.sql("SELECT pm25_mean FROM daily_pm25_clean WHERE pm25_mean > 0").df()["pm25_mean"]
print("skew เดิม:", round(stats.skew(x), 2), "| skew หลัง log:", round(stats.skew(np.log(x)), 2))
```

เขียน Markdown 2–3 บรรทัด: mean ต่างจาก median เท่าไร และ log ช่วยลดความเบ้แค่ไหน

## ขั้นที่ 5: สร้างหน่วยการวิเคราะห์และฟังก์ชันเปรียบเทียบ

```python
def station_units(years, months):
    """หนึ่งแถวต่อสถานี: มัธยฐาน PM2.5 รายวันในช่วงปีและเดือนที่กำหนด"""
    return con.execute("""
        SELECT d.station_id, s.region, s.province,
               median(d.pm25_mean) AS pm25, count(*) AS n_days
        FROM daily_pm25_clean AS d JOIN stations AS s USING (station_id)
        WHERE year(d.date) BETWEEN ? AND ? AND month(d.date) BETWEEN ? AND ?
        GROUP BY ALL
        HAVING count(*) >= 30
    """, [*years, *months]).df()


def compare(a, b):
    """เปรียบเทียบสองกลุ่มอิสระ คืนผลพร้อม effect size"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = stats.mannwhitneyu(a, b, alternative="two-sided")
    t = stats.ttest_ind(np.log(a), np.log(b), equal_var=False)
    return {"n_a": len(a), "n_b": len(b),
            "median_a": np.median(a).round(1), "median_b": np.median(b).round(1),
            "ratio_gm": round(float(np.exp(np.log(a).mean() - np.log(b).mean())), 2),
            "cles": round(u.statistic / (len(a) * len(b)), 2),
            "p_mwu": u.pvalue, "p_welch_log": t.pvalue}
```

## ขั้นที่ 6: ทดสอบ H1 ในปีสำรวจ

```python
dry = station_units(EXPLORE, DRY)
north = dry.loc[dry["region"] == NORTH, "pm25"]
bkk = dry.loc[dry["province"] == BKK, "pm25"]
h1_explore = compare(north, bkk)
h1_explore
```

ถ้าจำนวนสถานีกลุ่มใดน้อยกว่า 5 ให้บันทึกเป็นข้อจำกัด เพราะการทดสอบจะมี power ต่ำ

**(เสริม) ตรวจทานด้วย pingouin**

```python
import pingouin as pg
pg.mwu(north, bkk)     # เทียบค่า CLES และ p-value กับที่คำนวณเอง
```

## ขั้นที่ 7: ทดสอบ H2 แบบจับคู่รายสถานี

```python
wet = station_units(EXPLORE, WET)
paired = (dry[dry["region"] == NORTH][["station_id", "pm25"]]
          .merge(wet[["station_id", "pm25"]], on="station_id", suffixes=("_dry", "_wet")))
w = stats.wilcoxon(paired["pm25_dry"], paired["pm25_wet"])
ratio = (paired["pm25_dry"] / paired["pm25_wet"]).median()
print(f"n={len(paired)}  Wilcoxon p={w.pvalue:.4f}  มัธยฐานอัตราส่วนแล้ง/ฝน={ratio:.2f}")
```

ใช้ Wilcoxon signed-rank เพราะเป็นสถานีเดียวกันวัดสองฤดู (ข้อมูลจับคู่) ไม่ใช่สองกลุ่มอิสระ

## ขั้นที่ 8: Multiple comparisons — เทียบทุกภาคกับกรุงเทพฯ

```python
from statsmodels.stats.multitest import multipletests

rows = []
for region, g in dry[dry["province"] != BKK].groupby("region"):
    if len(g) >= 3:
        rows.append({"region": region, **compare(g["pm25"], bkk)})
multi = pd.DataFrame(rows)
multi["reject_holm"], multi["p_holm"], _, _ = multipletests(multi["p_mwu"], method="holm")
multi[["region", "n_a", "ratio_gm", "cles", "p_mwu", "p_holm", "reject_holm"]]
```

เขียนว่ามีภาคใดบ้างที่ "มีนัยสำคัญ" ก่อนปรับแต่ไม่ใช่หลังปรับ และควรรายงานอย่างไร

## ขั้นที่ 9: Correlation และ autocorrelation

```python
pair = con.sql("""
    SELECT pm25, pm10 FROM measurements
    WHERE pm25 > 0 AND pm10 > 0
    USING SAMPLE 1% (bernoulli, 42)
""").df()
print("Pearson :", stats.pearsonr(pair["pm25"], pair["pm10"]))
print("Spearman:", stats.spearmanr(pair["pm25"], pair["pm10"]))
```

```python
from statsmodels.graphics.tsaplots import plot_acf

SID = dry.loc[dry["region"] == NORTH, "station_id"].iloc[0]   # หรือใส่รหัสสถานีที่สนใจเอง
one = con.execute("SELECT date, pm25_mean FROM daily_pm25_clean WHERE station_id = ? ORDER BY date", [SID]).df()
y = one.set_index(pd.to_datetime(one["date"]))["pm25_mean"].asfreq("D")
fig = plot_acf(np.log(y), lags=60, missing="conservative")
fig.savefig("reports/figures/11_acf.png", dpi=150, bbox_inches="tight")
```

เขียนว่า lag ที่ 1 และ 7 มีค่า autocorrelation เท่าไร และอธิบายว่าทำไมขั้นที่ 6 จึงใช้ค่าต่อสถานีแทนค่ารายวัน

## ขั้นที่ 10: STL decomposition รายเดือน

```python
from statsmodels.tsa.seasonal import STL

m = con.execute("""
    SELECT date_trunc('month', date) AS month, avg(pm25_mean) AS pm25, count(*) AS n_days
    FROM daily_pm25_clean WHERE station_id = ? GROUP BY ALL ORDER BY month
""", [SID]).df()
s = m.set_index(pd.to_datetime(m["month"])).asfreq("MS")
print("เดือนที่หายทั้งเดือน:", s["pm25"].isna().sum())
s.loc[s["n_days"] < 20, "pm25"] = np.nan
y = np.log(s["pm25"]).interpolate(limit=2)
print("เดือนที่ยังเป็น NaN:", y.isna().sum())       # ต้องเป็น 0 ถ้าไม่ใช่ ให้เลือกช่วงที่ต่อเนื่อง
```

```python
res = STL(y, period=12, robust=True).fit()
fig = res.plot()
fig.savefig("reports/figures/11_stl.png", dpi=150, bbox_inches="tight")

f_t = max(0, 1 - res.resid.var() / (res.trend + res.resid).var())
f_s = max(0, 1 - res.resid.var() / (res.seasonal + res.resid).var())
print(f"trend strength={f_t:.2f}  seasonal strength={f_s:.2f}")
```

(เลือกทำ) ทำซ้ำกับสถานีใน กทม. แล้วเทียบ seasonal strength ของสองสถานี

## ขั้นที่ 11: ยืนยันด้วยปี held-out

รันการทดสอบ **เดิม** โดยไม่เปลี่ยนวิธี เปลี่ยนเฉพาะช่วงปี

```python
dry_h = station_units(HOLDOUT, DRY)
h1_holdout = compare(dry_h.loc[dry_h["region"] == NORTH, "pm25"],
                     dry_h.loc[dry_h["province"] == BKK, "pm25"])
pd.DataFrame([h1_explore, h1_holdout], index=["explore", "holdout"])
```

## ขั้นที่ 12: เขียนผลใน `questions.md`

เขียนผลใต้ section สมมติฐาน (ห้ามแก้ข้อความสมมติฐานเดิม) ให้มี ขนาดผล + หน่วย + ช่วงเวลา + วิธี + p-value + n + ข้อจำกัด เช่น

```markdown
### ผล H1
ในฤดูแล้งปี 2563–2567 มัธยฐาน PM2.5 ของสถานีภาคเหนือ (n = …) สูงกว่าสถานีใน กทม. (n = …)
ประมาณ … เท่า (CLES = …, Mann-Whitney p = …) ผลในทิศทางเดียวกันพบ/ไม่พบในปี 2568 (held-out)
ข้อจำกัด: จำนวนสถานีน้อย, สถานีไม่ได้สุ่มเลือก, …
```

ใช้ตารางถ้อยคำในเอกสารประกอบการสอนหัวข้อ 8 ตรวจว่าไม่อ้างเกินหลักฐาน

## ขั้นที่ 13: commit, push และเปิด pull request

**Restart Kernel and Run All** ก่อน commit

```bash
git status
git add notebooks/11_stats.ipynb reports/figures/11_*.png questions.md AI_USAGE.md
git commit -m "ทดสอบ H1/H2 พร้อม effect size, ปรับ Holm, STL รายเดือน และยืนยันด้วยปี held-out"
git push -u origin week11-stats
```

เปิด PR ขอ review จากเพื่อน 1 คน แล้ว merge เมื่อได้ approve

## ขั้นที่ 14: review PR ของเพื่อน

- [ ] commit สมมติฐานใน `questions.md` เกิดขึ้น *ก่อน* commit ผลทดสอบ (ดูใน tab Commits)
- [ ] หน่วยการวิเคราะห์เป็นค่าต่อสถานี ไม่ใช่ค่ารายวันทุกแถว
- [ ] ทุกผลทดสอบมี effect size และ n ไม่ใช่แค่ p-value
- [ ] ใช้วิธีจับคู่ (Wilcoxon) กับข้อมูลจับคู่ และวิธีกลุ่มอิสระกับกลุ่มอิสระ
- [ ] ปรับ p-value เมื่อทดสอบหลายภาค และรายงานผล held-out แม้ไม่ตรงกับปีสำรวจ
- [ ] การจัดการช่องว่างก่อน STL ถูกบันทึกไว้
- [ ] ถ้อยคำสรุปไม่อ้างเกินหลักฐาน (ไม่มี "พิสูจน์", "เป็นสาเหตุ", "ไม่มีความแตกต่าง")

---

## Checklist ก่อนส่งงาน

- [ ] มี commit สมมติฐานแยกต่างหากก่อน commit ผล
- [ ] notebook รัน Restart & Run All ผ่าน
- [ ] มีตารางสถิติเชิงพรรณนา (median, IQR, p95, สัดส่วนวันที่เกิน 37.5)
- [ ] มีผล H1 และ H2 พร้อม effect size ทั้งปีสำรวจและ (อย่างน้อย H1) ปี held-out
- [ ] มีตาราง multiple comparisons ที่ปรับด้วย Holm
- [ ] มีภาพ ACF และ STL ใน `reports/figures/`
- [ ] `questions.md` มีข้อความสรุปผลที่ระบุข้อจำกัด
- [ ] บันทึกการใช้ AI ใน `AI_USAGE.md` (ถ้ามี) และ PR ถูก review และ merge แล้ว

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `north` หรือ `bkk` ว่าง (length 0) | ค่าในคอลัมน์ `region` / `province` ไม่ตรงกับที่พิมพ์ ตรวจด้วย `SELECT DISTINCT region, province FROM stations` |
| `RuntimeWarning: divide by zero` ใน log | มีค่า 0 ในข้อมูล กรอง `pm25 > 0` ตามกฎใน data dictionary หรือใช้ `np.log1p` แล้วระบุไว้ |
| `ValueError` จาก STL เรื่อง NaN | ยังมีเดือนที่หาย ให้เลือกช่วงเวลาที่ต่อเนื่อง (`y.loc["2021":"2024"]`) แทนการเติมช่องว่างยาว |
| STL แจ้งว่าข้อมูลสั้นเกินไป | `period=12` ต้องมีอย่างน้อย 2 รอบ (24 เดือน) ถ้าไม่ถึงให้ใช้ข้อมูลรายวันกับ `period=7` หรือเลือกสถานีอื่น |
| `wilcoxon` แจ้งเตือนเรื่อง n น้อย | จำนวนสถานีจับคู่น้อย ให้รายงานเป็นข้อจำกัด และอย่าตีความ p-value หนักเกินไป |
| ผล held-out ตรงข้ามกับปีสำรวจ | ไม่ใช่ความผิดพลาด รายงานตามจริง เป็นสัญญาณว่าผลอาจขึ้นกับปี (เช่น ปีที่ไฟป่ารุนแรง) |
| ชื่อคอลัมน์ pingouin ไม่ตรงตัวอย่าง | ต่างตามเวอร์ชัน พิมพ์ทั้งตารางแล้วอ่านชื่อจริง |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 12)

1. อ่าน *Forecasting: Principles and Practice* บท "Time series decomposition" หัวข้อ STL
2. ทบทวนแนวคิด PCA และ k-means จากรายวิชาที่เคยเรียน หรืออ่าน scikit-learn User Guide หัวข้อ "Clustering" อย่างคร่าว ๆ
3. คิดว่าสถานีใดมีพฤติกรรม "ผิดจากกลุ่ม" ในผลสัปดาห์นี้ (เช่น seasonal strength ต่างจากสถานีอื่นในภาคเดียวกัน) จดไว้เพื่อใช้ในหัวข้อ outlier สัปดาห์ที่ 12
