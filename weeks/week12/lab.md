---
title: "ปฏิบัติการสัปดาห์ที่ 12: จัดกลุ่มสถานี วิเคราะห์ outlier และสร้างข้อมูลสังเคราะห์"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO4, CLO6
> **ผลงานที่ต้องส่ง:** PR ที่มี `notebooks/12_multivariate.ipynb`, ตาราง `station_clusters` และ `daily_outlier_flags` ใน DuckDB (สร้างจากโค้ด), `src/make_fake_visits.py` และหัวข้อ PDPA ใน `README.md` ของโครงการ

## สิ่งที่ต้องเตรียม

- `data/pm25.duckdb` ที่มีตาราง `stations`, `measurements` และ view `daily_pm25_clean(station_id, date, pm25_mean, pm25_max, n_hours)` จากสัปดาห์ที่ 4–7
- ผล STL decomposition ของสัปดาห์ที่ 11 (ใช้เทียบ outlier) และกราฟ Plotly จากสัปดาห์ที่ 10
- ตรวจไลบรารี

```bash
python -c "import sklearn, faker; print(sklearn.__version__, faker.VERSION)"
python -c "import umap, pyod, sdv, imblearn"    # เสริม ถ้าไม่ผ่านข้ามได้
```

ถ้าฐานข้อมูลมีสถานีน้อยกว่า 15 แห่งหรือข้อมูลไม่ครบ 12 เดือน ให้ใช้ไฟล์ตัวอย่างจากผู้สอนที่ `data/sample/` แทน และระบุใน notebook

---

## ขั้นที่ 1: สร้าง branch และเมทริกซ์ monthly profile

```bash
git switch main && git pull
git switch -c week12-multivariate
```

สร้าง `notebooks/12_multivariate.ipynb`

```python
import duckdb, pandas as pd
import plotly.express as px

con = duckdb.connect("data/pm25.duckdb", read_only=True)
monthly = con.sql("""
    SELECT d.station_id, s.name_th, s.region, month(d.date) AS m,
           avg(d.pm25_mean) AS pm25
    FROM daily_pm25_clean d JOIN stations s USING (station_id)
    GROUP BY ALL
""").df()

profile = monthly.pivot(index="station_id", columns="m", values="pm25")
meta = monthly.drop_duplicates("station_id").set_index("station_id")[["name_th", "region"]]
print(profile.shape, "ค่าว่าง:", int(profile.isna().sum().sum()))
```

จัดการค่าว่าง แล้ว **เขียนเหตุผลใน markdown cell**

```python
keep = profile.isna().sum(axis=1) <= 2
P = profile[keep].apply(lambda c: c.fillna(c.mean()))
P.columns = [f"m{m:02d}" for m in P.columns]      # ชื่อคอลัมน์เป็น string
print(f"ใช้ {len(P)} สถานี ตัดออก {(~keep).sum()} สถานี")
```

## ขั้นที่ 2: Scale และ PCA

```python
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

X = StandardScaler().fit_transform(P)
pca = PCA(n_components=3, random_state=42).fit(X)
print("explained variance:", pca.explained_variance_ratio_.round(3))

loadings = pd.DataFrame(pca.components_.T, index=P.columns, columns=["PC1", "PC2", "PC3"])
px.line(loadings, markers=True, title="PCA loadings รายเดือน")
```

```python
scores = pd.DataFrame(pca.transform(X)[:, :2], index=P.index, columns=["PC1", "PC2"]).join(meta)
px.scatter(scores, x="PC1", y="PC2", color="region", hover_name="name_th")
```

**ทดลอง:** รันซ้ำโดย *ไม่* scale (`pca.fit(P)`) แล้วเปรียบเทียบ loadings เขียนสั้น ๆ ว่าต่างกันอย่างไร

## ขั้นที่ 3: เลือก k และจัดกลุ่มด้วย KMeans

```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

rows = []
for k in range(2, 8):
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
    rows.append({"k": k, "inertia": km.inertia_, "silhouette": silhouette_score(X, km.labels_)})
pd.DataFrame(rows).round(3)
```

เลือก k แล้วเขียนเหตุผลโดยใช้ทั้ง silhouette, elbow และความหมาย

```python
K = 3   # เปลี่ยนตามผลของตนเอง
km = KMeans(n_clusters=K, n_init=10, random_state=42).fit(X)
clusters = pd.DataFrame({"station_id": P.index, "cluster": km.labels_, "k": K})
pd.crosstab(clusters.set_index("station_id").join(meta)["region"], km.labels_)
```

วาด profile เฉลี่ยของแต่ละกลุ่ม (ใช้ค่าจริง ไม่ใช่ค่าที่ scale แล้ว เพื่อให้อ่านเป็น µg/m³ ได้)

```python
avg = P.assign(cluster=km.labels_).groupby("cluster").mean().T
fig = px.line(avg, markers=True, labels={"index": "เดือน", "value": "PM2.5 (µg/m³)"})
fig.add_hline(y=37.5, line_dash="dash", annotation_text="มาตรฐานไทย 37.5")
fig
```

**ตรวจความเสถียร:** เปลี่ยน `random_state` เป็น 0, 1, 2 แล้วดูว่าสมาชิกของกลุ่มเปลี่ยนมากหรือไม่ เขียนผลใน markdown

## ขั้นที่ 4: บันทึกผลการจัดกลุ่มลง DuckDB

ปิด connection แบบ read-only ก่อน แล้วเปิดใหม่แบบเขียนได้

```python
con.close()
con = duckdb.connect("data/pm25.duckdb")
con.register("clusters_df", clusters)
con.execute("CREATE OR REPLACE TABLE station_clusters AS SELECT * FROM clusters_df")
con.sql("SELECT cluster, count(*) FROM station_clusters GROUP BY cluster").show()
```

> ตาราง `station_clusters` จะใช้ต่อในแผนที่สัปดาห์ที่ 13 และแดชบอร์ดสัปดาห์ที่ 14

## ขั้นที่ 5: วิเคราะห์ outlier ตามบริบท

```python
d = con.sql("""
    SELECT d.station_id, s.province, d.date, d.pm25_mean
    FROM daily_pm25_clean d JOIN stations s USING (station_id)
""").df()
d["month"] = pd.to_datetime(d["date"]).dt.month

g = d.groupby(["station_id", "month"])["pm25_mean"]
mad = g.transform(lambda s: (s - s.median()).abs().median())
d["robust_z"] = 0.6745 * (d["pm25_mean"] - g.transform("median")) / mad
d["is_outlier"] = d["robust_z"].abs() > 3.5
print(d["is_outlier"].mean().round(4), "ของวันทั้งหมดถูกติดธง")
```

ตรวจบริบท: วันเดียวกัน สถานีอื่นในจังหวัดเดียวกันถูกติดธงด้วยหรือไม่

```python
ctx = d.groupby(["province", "date"]).agg(n_st=("station_id", "nunique"),
                                          n_flag=("is_outlier", "sum")).reset_index()
d = d.merge(ctx, on=["province", "date"])
d["outlier_reason"] = None
d.loc[d.is_outlier & (d.n_flag >= 2), "outlier_reason"] = "likely real: หลายสถานีผิดปกติพร้อมกัน"
d.loc[d.is_outlier & (d.pm25_mean < 0), "outlier_reason"] = "error: ค่าติดลบ"   # กฎนี้สำคัญกว่า จึงเขียนทับ
d.loc[d.is_outlier & d.outlier_reason.isna(), "outlier_reason"] = "uncertain: ตรวจต่อ"
d.loc[d.is_outlier, "outlier_reason"].value_counts()
```

เลือกกรณี "uncertain" มา 2–3 กรณี วาด time series ±7 วันของสถานีนั้นเทียบกับสถานีใกล้เคียง (ใช้ Plotly จากสัปดาห์ที่ 10) และเขียนข้อสรุป **ห้ามลบแถวใด ๆ** ให้บันทึกเป็นตารางธง

```python
flags = d.loc[d.is_outlier, ["station_id", "date", "pm25_mean", "robust_z", "outlier_reason"]]
con.register("flags_df", flags)
con.execute("CREATE OR REPLACE TABLE daily_outlier_flags AS SELECT * FROM flags_df")
```

### (เสริม) Isolation Forest ด้วย PyOD

```python
from pyod.models.iforest import IForest

h = con.sql("""SELECT station_id, ts, pm25, pm10 FROM measurements
               WHERE pm25 IS NOT NULL AND pm10 IS NOT NULL""").df()
clf = IForest(contamination=0.005, random_state=42).fit(h[["pm25", "pm10"]])
h["iforest_flag"] = clf.labels_          # 1 = outlier
h[h.iforest_flag == 1].sort_values("pm25").head(10)
```

สังเกตว่ามีกรณี PM2.5 > PM10 หรือไม่ ซึ่งเป็นไปไม่ได้ทางกายภาพ (PM2.5 เป็นส่วนหนึ่งของ PM10) จึงน่าจะเป็น error

## ขั้นที่ 6: สร้างข้อมูลปลอมด้วย Faker เพื่อทดสอบ pipeline

สร้าง `src/make_fake_visits.py`

```python
"""สร้างตารางผู้ป่วยปลอม (ไม่ใช่ข้อมูลจริง) สำหรับทดสอบการเชื่อมกับ daily_pm25_clean"""
from pathlib import Path
import duckdb, pandas as pd
from faker import Faker

ROOT = Path(__file__).resolve().parents[1]
Faker.seed(42)
fake = Faker("th_TH")

con = duckdb.connect(str(ROOT / "data" / "pm25.duckdb"), read_only=True)
provinces = con.sql("SELECT DISTINCT province FROM stations").df()["province"].tolist()
dmin, dmax = con.execute("SELECT min(date), max(date) FROM daily_pm25_clean").fetchone()

rows = [{
    "visit_id": f"V{i:06d}",
    "patient_name": fake.name(),                     # ปลอม
    "age": fake.random_int(min=1, max=95),
    "sex": fake.random_element(["M", "F"]),
    "province": fake.random_element(provinces),
    "visit_date": fake.date_between(start_date=dmin, end_date=dmax),
    "icd10": fake.random_element(["J44", "J45", "J18", "I21"]),
} for i in range(5000)]

out = ROOT / "data" / "synthetic"
out.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_csv(out / "fake_visits.csv", index=False)
print("เขียน", len(rows), "แถว ->", out / "fake_visits.csv")
```

รัน `python src/make_fake_visits.py` แล้วทดสอบการเชื่อมใน notebook

```python
test = con.sql("""
    WITH v AS (SELECT province, visit_date::DATE AS date, count(*) AS n_visits
               FROM 'data/synthetic/fake_visits.csv' GROUP BY ALL),
         p AS (SELECT s.province, d.date, avg(d.pm25_mean) AS pm25
               FROM daily_pm25_clean d JOIN stations s USING (station_id) GROUP BY ALL)
    SELECT * FROM v JOIN p USING (province, date)
""").df()
test.head()
```

ตรวจว่า join ได้จำนวนแถวตามที่คาด (ไม่ซ้ำ ไม่หาย) **อย่าตีความความสัมพันธ์** เพราะข้อมูลสุ่ม

### (เสริม) SDV

ลองสร้างตารางสังเคราะห์จาก `daily_pm25_clean` ของสถานีเดียว (ไม่ใช่ข้อมูลส่วนบุคคล จึงใช้ฝึกได้)

```python
from sdv.metadata import Metadata
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.evaluation.single_table import evaluate_quality

real = con.sql("SELECT pm25_mean, pm25_max, n_hours FROM daily_pm25_clean WHERE station_id = '<รหัสสถานี>'").df()
md = Metadata.detect_from_dataframe(data=real, table_name="daily")
syn = GaussianCopulaSynthesizer(md)
syn.fit(real)
fake_daily = syn.sample(num_rows=len(real))
evaluate_quality(real, fake_daily, md)
```

เปรียบเทียบ histogram และค่า max ของ `real` กับ `fake_daily` แล้วเขียนว่า SDV รักษาอะไรได้และอะไรหายไป

## ขั้นที่ 7: เขียนหัวข้อ PDPA ใน README ของโครงการ

เพิ่มใน `README.md`

```markdown
## ข้อมูลส่วนบุคคลและ PDPA
- ข้อมูลที่ใช้: ... (เป็น/ไม่เป็นข้อมูลส่วนบุคคล เพราะ ...)
- ถ้าต่อยอดกับข้อมูลสุขภาพ: เป็นข้อมูลอ่อนไหว (มาตรา 26) จะใช้เฉพาะข้อมูลรวมระดับ ... / ข้อมูลสังเคราะห์
- quasi-identifier ที่ต้องระวัง: ...
- `data/synthetic/fake_visits.csv` สร้างด้วย Faker ใช้ทดสอบโค้ดเท่านั้น
```

## ขั้นที่ 8: commit, push และเปิด pull request

```bash
git add notebooks/12_multivariate.ipynb src/make_fake_visits.py README.md AI_USAGE.md
git commit -m "จัดกลุ่มสถานีด้วย PCA+KMeans, ติดธง outlier และสร้างข้อมูลผู้ป่วยปลอมด้วย Faker"
git push -u origin week12-multivariate
```

เปิด PR แล้วขอ review จากเพื่อน 1 คน (ห้าม commit ไฟล์ใน `data/` รวมถึง `data/synthetic/`)

## ขั้นที่ 9: review PR ของเพื่อน

- [ ] มีเหตุผลการจัดการค่าว่างและการ scale
- [ ] การเลือก k อ้างอิงทั้งตัวเลขและความหมาย ไม่ใช่เลือก silhouette สูงสุดอย่างเดียว
- [ ] ข้อความสรุป cluster ใช้ภาษาแบบสมมติฐาน ("มีแนวโน้ม") ไม่ฟันธง
- [ ] ไม่มีโค้ดลบ outlier ทิ้ง มีคอลัมน์เหตุผลของธง
- [ ] `make_fake_visits.py` ใช้ `Faker.seed` และ path แบบ relative
- [ ] หัวข้อ PDPA ระบุ quasi-identifier ได้ถูกต้อง

---

## Checklist ก่อนส่งงาน

- [ ] notebook รันได้ตั้งแต่ต้นจนจบด้วย *Restart & Run All*
- [ ] มีตาราง `station_clusters` และ `daily_outlier_flags` ใน DuckDB
- [ ] มีกราฟ loadings, scatter PC1–PC2 และ profile เฉลี่ยรายกลุ่ม พร้อมคำอธิบาย
- [ ] มีการวิเคราะห์ outlier อย่างน้อย 2 กรณีพร้อมข้อสรุปว่าเป็น error หรือเหตุการณ์จริง
- [ ] `src/make_fake_visits.py` รันผ่านและทดสอบ join แล้ว
- [ ] อัปเดต `AI_USAGE.md` และมี PR ที่เพื่อน review แล้ว

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| `ValueError: Input X contains NaN` | ยังมีค่าว่างในเมทริกซ์ ตรวจ `P.isna().sum()` ก่อน scale |
| `IOException: Could not set lock on file` | มี connection อื่นเปิดไฟล์อยู่ (notebook อื่นหรือ Streamlit) ปิด kernel อื่นก่อน หรือ `con.close()` |
| silhouette สูงสุดที่ k = 2 เสมอ | พบบ่อยเมื่อมีกลุ่มใหญ่ 2 กลุ่ม (เช่น เหนือ vs ที่เหลือ) ลองตัดผลของระดับรวม (หารด้วยค่าเฉลี่ยแถว) แล้วดูใหม่ |
| robust z เป็น `inf` | MAD = 0 เพราะค่าซ้ำกันมาก (เช่น ค่าค้าง) นั่นคือเบาะแส error ให้ตรวจสถานีนั้น |
| `import umap` error แต่ติดตั้ง `umap` แล้ว | แพ็กเกจที่ถูกคือ `umap-learn` |
| SDV import หรือ API ไม่ตรงกับคู่มือ | SDV เปลี่ยน API บ่อย ตรวจ `sdv.__version__` และเอกสารของเวอร์ชันนั้น (เวอร์ชันเก่าใช้ `SingleTableMetadata`) |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 13)

1. สรุปลักษณะของแต่ละ cluster 2–3 บรรทัด และเพิ่มคำถามใหม่ที่เกิดขึ้นลงใน `questions.md`
2. ขอไฟล์ GeoJSON ขอบเขตจังหวัดจากผู้สอน (หรือเลือกแหล่งเปิด เช่น geoBoundaries / HDX) แล้วอ่านเงื่อนไขสัญญาอนุญาต
3. อ่านเอกสาร GeoPandas หัวข้อ *Managing Projections* และทบทวนว่า `stations` มีคอลัมน์ `lat`, `lon` ครบทุกสถานีหรือไม่
