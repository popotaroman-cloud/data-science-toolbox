---
title: "ปฏิบัติการสัปดาห์ที่ 13: แผนที่สถานีและกราฟลำดับชั้น"
---

> **เวลา:** 2 ชั่วโมง · **CLO:** CLO4
> **ผลงานที่ต้องส่ง:** PR ที่มี `notebooks/13_spatial.ipynb`, `src/geo_utils.py` และหัวข้อ "แหล่งข้อมูลขอบเขตจังหวัด" ใน `README.md` (ไฟล์แผนที่ HTML อยู่ใน `outputs/` ซึ่งไม่ต้อง commit)

## สิ่งที่ต้องเตรียม

- `data/pm25.duckdb` ที่มี `stations` (มี `lat`, `lon`, `province`, `region`), `daily_pm25_clean` และ `station_clusters` จากสัปดาห์ที่ 12
- ไฟล์ขอบเขตจังหวัด **GeoJSON จากผู้สอน** วางไว้ที่ `data/geo/thailand_provinces.geojson` หรือไฟล์ที่ดาวน์โหลดเองจากแหล่งเปิดที่ระบุชื่อได้ (geoBoundaries, HDX, GADM) **พร้อมบันทึกสัญญาอนุญาต**
- ตรวจไลบรารี

```bash
python -c "import geopandas, folium; print(geopandas.__version__, folium.__version__)"
```

ถ้า import GeoPandas ไม่ผ่าน ให้ติดตั้งผ่าน conda-forge (`conda install -c conda-forge geopandas`) ไม่ใช้ pip

---

## ขั้นที่ 1: สร้าง branch และตรวจพิกัดสถานี

```bash
git switch main && git pull
git switch -c week13-spatial
mkdir outputs
```

เพิ่ม `outputs/` ใน `.gitignore` แล้วสร้าง `notebooks/13_spatial.ipynb`

```python
import duckdb, pandas as pd, geopandas as gpd
import plotly.express as px

con = duckdb.connect("data/pm25.duckdb", read_only=True)
st = con.sql("""
    SELECT s.*, c.cluster
    FROM stations s LEFT JOIN station_clusters c USING (station_id)
""").df()
print("ไม่มีพิกัด:", st[["lat", "lon"]].isna().any(axis=1).sum(), "สถานี")
st = st.dropna(subset=["lat", "lon"])

stations = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.lon, st.lat), crs="EPSG:4326")
print(stations.total_bounds)   # [minx miny maxx maxy] ควรอยู่ราว [97 5 106 21]
```

ถ้า `total_bounds` ไม่อยู่ในช่วงนี้ ให้ตรวจว่า lat/lon สลับกันหรือไม่ แล้วแก้ที่ต้นทาง (script โหลดข้อมูลใน `src/`) ไม่ใช่แก้ใน notebook

## ขั้นที่ 2: โหลดขอบเขตจังหวัดและตรวจโครงสร้าง

```python
prov = gpd.read_file("data/geo/thailand_provinces.geojson")
print(prov.crs, len(prov))
prov.head(3)
```

ดูชื่อคอลัมน์จริงแล้วเปลี่ยนชื่อให้เป็นมาตรฐานของเรา

```python
prov = prov.rename(columns={"<คอลัมน์ชื่อจังหวัด>": "prov_name"})[["prov_name", "geometry"]]
prov = prov.to_crs("EPSG:4326")
prov.plot(edgecolor="white", figsize=(5, 8))
```

## ขั้นที่ 3: Spatial join และตรวจคุณภาพคอลัมน์จังหวัด

```python
joined = gpd.sjoin(stations, prov, how="left", predicate="within")
print("อยู่นอกทุกจังหวัด:", joined["prov_name"].isna().sum())

mismatch = joined[joined["province"] != joined["prov_name"]][["station_id", "name_th", "province", "prov_name"]]
mismatch
```

ความไม่ตรงกันส่วนใหญ่มักมาจากการสะกด (เช่น "กรุงเทพมหานคร" vs "กรุงเทพฯ" หรือภาษาไทย vs อังกฤษ) ให้สร้างตาราง mapping ใน `src/geo_utils.py` ส่วนกรณีที่ต่างจังหวัดจริง ให้ตรวจพิกัดกับเว็บไซต์ Air4Thai และบันทึกผลไว้ใน notebook

```python
# src/geo_utils.py
"""ฟังก์ชันช่วยงานเชิงพื้นที่ ใช้ร่วมกันใน notebook, report และ app"""
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
PROV_FILE = ROOT / "data" / "geo" / "thailand_provinces.geojson"
NAME_FIX = {"กรุงเทพฯ": "กรุงเทพมหานคร"}   # เติมตามที่พบจริง

def load_provinces(name_col: str) -> gpd.GeoDataFrame:
    prov = gpd.read_file(PROV_FILE).rename(columns={name_col: "prov_name"})
    prov["prov_name"] = prov["prov_name"].replace(NAME_FIX)
    return prov[["prov_name", "geometry"]].to_crs("EPSG:4326")
```

## ขั้นที่ 4: คำนวณระยะทางใน projected CRS

หาสถานีที่ใกล้ที่สุดของแต่ละสถานี เพื่อใช้ตรวจ outlier ตามบริบท (ต่อยอดสัปดาห์ที่ 12)

```python
s_m = stations.to_crs(epsg=32647)[["station_id", "name_th", "geometry"]]
near = gpd.sjoin_nearest(s_m, s_m.rename(columns={"station_id": "nb_id", "name_th": "nb_name"}),
                         distance_col="dist_m", exclusive=True)
near["dist_km"] = (near["dist_m"] / 1000).round(1)
near.sort_values("dist_km", ascending=False).head()
```

`exclusive=True` ป้องกันไม่ให้จับคู่สถานีกับตัวเอง (ต้องใช้ GeoPandas 1.x) สถานีที่ห่างจากเพื่อนบ้านมากที่สุดคือสถานีที่ "แทน" พื้นที่กว้าง ให้ระวังเมื่อตีความ choropleth

## ขั้นที่ 5: Choropleth ระดับจังหวัด

```python
agg = con.sql("""
    WITH per_station AS (
        SELECT station_id, avg(pm25_mean) AS pm25, avg((pm25_mean > 37.5)::INT) AS share_over
        FROM daily_pm25_clean GROUP BY station_id)
    SELECT s.province, count(*) AS n_stations,
           avg(p.pm25) AS pm25_mean, avg(p.share_over) AS share_over_std
    FROM per_station p JOIN stations s USING (station_id)
    GROUP BY s.province
""").df()

m = prov.merge(agg, left_on="prov_name", right_on="province", how="left")
print("จังหวัดที่ไม่มีสถานี:", m["n_stations"].isna().sum())
m.plot(column="share_over_std", cmap="YlOrRd", legend=True, figsize=(6, 9),
       missing_kwds={"color": "lightgrey"})
```

ทำ choropleth แบบ interactive ด้วย Plotly เพื่อให้ tooltip แสดงจำนวนสถานี

```python
mm = m.dropna(subset=["n_stations"]).reset_index(drop=True)
fig = px.choropleth(mm, geojson=mm.geometry.__geo_interface__, locations=mm.index,
                    color="share_over_std", color_continuous_scale="YlOrRd",
                    hover_name="prov_name", hover_data={"n_stations": True, "pm25_mean": ":.1f"})
fig.update_geos(fitbounds="locations", visible=False)
fig.show()
```

เขียน markdown 3–5 บรรทัด: จังหวัดใดดูแย่ที่สุด และข้อสรุปนั้นเชื่อถือได้แค่ไหนเมื่อดู `n_stations` และ MAUP

## ขั้นที่ 6: แผนที่สถานีด้วย Folium พร้อม popup (เสริม แต่แนะนำ)

```python
import folium

daily = con.sql("SELECT station_id, avg(pm25_mean) AS pm25 FROM daily_pm25_clean GROUP BY 1").df()
sm = stations.merge(daily, on="station_id", how="left")

def color(v):
    if pd.isna(v): return "gray"
    return "green" if v <= 15 else "orange" if v <= 37.5 else "red"

fmap = folium.Map(location=[13.5, 101.0], zoom_start=6)
for r in sm.itertuples():
    html = (f"<b>{r.name_th}</b><br>{r.province} ({r.region})<br>"
            f"PM2.5 เฉลี่ย: {r.pm25:.1f} µg/m³<br>cluster: {r.cluster}")
    folium.CircleMarker([r.lat, r.lon], radius=6, color=color(r.pm25), fill=True,
                        fill_opacity=0.8, tooltip=r.name_th,
                        popup=folium.Popup(html, max_width=250)).add_to(fmap)
fmap.save("outputs/stations_map.html")
fmap
```

เกณฑ์สี: เขียว ≤ 15 (WHO 2021) · ส้ม ≤ 37.5 (มาตรฐานไทย) · แดง > 37.5 ให้เพิ่ม legend เป็นข้อความใน markdown cell และสังเกตว่าสี cluster จากสัปดาห์ที่ 12 กระจุกตามภูมิศาสตร์หรือไม่ (ลองวาด `px.scatter_geo` หรือ `stations.explore(column="cluster")`)

## ขั้นที่ 7: Treemap และ sunburst ภาค → จังหวัด → สถานี

```python
h = con.sql("""
    SELECT coalesce(s.region, 'ไม่ระบุ') AS region, coalesce(s.province, 'ไม่ระบุ') AS province,
           s.name_th, count(*) AS n_days, avg(d.pm25_mean) AS pm25_mean
    FROM daily_pm25_clean d JOIN stations s USING (station_id)
    GROUP BY ALL
""").df()

path = [px.Constant("ประเทศไทย"), "region", "province", "name_th"]
px.treemap(h, path=path, values="n_days", color="pm25_mean",
           color_continuous_scale="YlOrRd", color_continuous_midpoint=37.5).show()
px.sunburst(h, path=path, values="n_days", color="pm25_mean",
            color_continuous_scale="YlOrRd", color_continuous_midpoint=37.5).show()
```

ตรวจความสะอาดของลำดับชั้น: จังหวัดหนึ่งต้องอยู่ภาคเดียว

```python
chk = h.groupby("province")["region"].nunique()
chk[chk > 1]      # ควรว่าง ถ้าไม่ว่างให้แก้ข้อมูล stations
```

คลิกบนกราฟเพื่อ drill-down แล้วจดว่าอยากให้แดชบอร์ดสัปดาห์ที่ 14 แสดงอะไรในแต่ละระดับ (ประเทศ / ภาค / จังหวัด / สถานี)

## ขั้นที่ 8: บันทึกแหล่งข้อมูลขอบเขตใน README

```markdown
## แหล่งข้อมูลขอบเขตจังหวัด
- ไฟล์: data/geo/thailand_provinces.geojson (ไม่ commit)
- แหล่งที่มา: ... (ผู้สอน / ชื่อแหล่งเปิด) · วันที่ดาวน์โหลด: ...
- สัญญาอนุญาต: ... · การระบุที่มาที่ต้องใส่: ...
- คอลัมน์ชื่อจังหวัดในไฟล์ต้นฉบับ: ...
```

## ขั้นที่ 9: commit, push และเปิด pull request

```bash
git add notebooks/13_spatial.ipynb src/geo_utils.py README.md .gitignore AI_USAGE.md
git commit -m "เพิ่มแผนที่สถานี choropleth รายจังหวัด และ treemap ภาค-จังหวัด-สถานี"
git push -u origin week13-spatial
```

เปิด PR แล้วขอ review จากเพื่อน 1 คน

## ขั้นที่ 10: review PR ของเพื่อน

- [ ] ตรวจ CRS ก่อน join และคำนวณระยะทางใน projected CRS
- [ ] มีการเทียบ `province` เดิมกับผล spatial join และอธิบายกรณีไม่ตรงกัน
- [ ] choropleth แสดงพื้นที่ไม่มีข้อมูลแยกสี และมีจำนวนสถานีใน tooltip หรือข้อความ
- [ ] ใช้ค่าที่บวกกันได้เป็น `values` ของ treemap
- [ ] README ระบุแหล่งที่มาและสัญญาอนุญาตของขอบเขตจังหวัด
- [ ] ไม่มีไฟล์ GeoJSON หรือ HTML ขนาดใหญ่ถูก commit

---

## Checklist ก่อนส่งงาน

- [ ] notebook รันได้ตั้งแต่ต้นจนจบด้วย *Restart & Run All*
- [ ] มีแผนที่จุดสถานี, choropleth รายจังหวัด, treemap และ sunburst พร้อมคำอธิบาย
- [ ] `outputs/stations_map.html` เปิดใน browser ได้และ popup แสดงข้อมูลถูกต้อง
- [ ] `src/geo_utils.py` ใช้ path แบบ relative จาก root ของโครงการ
- [ ] อัปเดต `AI_USAGE.md` และมี PR ที่เพื่อน review แล้ว

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
|---|---|
| จุดทุกจุดไปอยู่ในมหาสมุทรอินเดียหรือแอฟริกา | สลับ lat/lon ใช้ `points_from_xy(lon, lat)` |
| `sjoin` ได้ `NaN` ทั้งหมด | CRS ไม่ตรงกัน ตรวจ `stations.crs` และ `prov.crs` แล้ว `to_crs` ให้ตรงกัน |
| เตือน `Geometry is in a geographic CRS` ตอนใช้ `distance`/`buffer` | ยังคำนวณใน EPSG:4326 ให้ `to_crs(epsg=32647)` ก่อน |
| merge choropleth แล้วหลายจังหวัดเป็นค่าว่าง | ชื่อจังหวัดสะกดไม่ตรงกัน เพิ่มใน `NAME_FIX` |
| ตัวอักษรไทยในกราฟ matplotlib เป็นสี่เหลี่ยม | ตั้งฟอนต์ไทย เช่น `plt.rcParams["font.family"] = "Tahoma"` (Windows) หรือใช้ Plotly แทน |
| treemap error เรื่อง `None entries cannot have not-None children` | มีค่าว่างใน `region`/`province` ใช้ `coalesce` หรือ `fillna("ไม่ระบุ")` |
| แผนที่ Folium ไม่แสดงใน notebook | ให้เปิด `outputs/stations_map.html` ใน browser หรือ trust notebook |

## งานศึกษาด้วยตนเอง (ก่อนสัปดาห์ที่ 14)

1. ติดตั้ง Quarto CLI (<https://quarto.org/docs/get-started/>) และทดสอบ `quarto check`
2. ทบทวน `questions.md` แล้วเลือก 3–4 คำถามที่ตอบได้ชัดที่สุด จดข้อค้นพบหลักของแต่ละคำถามเป็น 1 ประโยค
3. ร่าง wireframe ของแดชบอร์ดบนกระดาษ: แต่ละระดับ (ประเทศ / ภาค / จังหวัด / สถานี) แสดงกราฟอะไรและมีตัวกรองอะไร
