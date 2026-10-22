---
title: "สัปดาห์ที่ 13: ข้อมูลเชิงพื้นที่และข้อมูลลำดับชั้น"
---

> **CLO:** CLO4 · **เครื่องมือหลัก:** GeoPandas · **เครื่องมือเสริม:** Folium, Plotly treemap/sunburst
> **ผลงานที่เพิ่มในระบบ:** แผนที่สถานีและแผนที่ระดับจังหวัด + กราฟลำดับชั้น ภาค → จังหวัด → สถานี

## วัตถุประสงค์การเรียนรู้

เมื่อจบสัปดาห์นี้ ผู้เรียนสามารถ

1. อธิบายระบบพิกัดอ้างอิง (CRS) และเลือกใช้ EPSG:4326 หรือ projected CRS ของประเทศไทยได้เหมาะกับงาน
2. สร้าง GeoDataFrame ของสถานีจาก lat/lon และ spatial join เข้ากับขอบเขตจังหวัดได้
3. สร้างแผนที่ choropleth และอธิบายข้อควรระวัง เช่น จังหวัดที่มีสถานีน้อย และ modifiable areal unit problem (MAUP)
4. สร้างแผนที่ interactive ที่มี popup ด้วย Folium
5. แสดงข้อมูลลำดับชั้น ภาค → จังหวัด → สถานี ด้วย Plotly treemap และ sunburst และเชื่อมโยงกับระดับ drill-down ของแดชบอร์ดสัปดาห์ที่ 14

---

## 1. ทำไมต้องดูข้อมูลบนแผนที่

PM2.5 เป็นปรากฏการณ์เชิงพื้นที่ ควันจากการเผาเคลื่อนข้ามจังหวัดและข้ามประเทศ สถานีที่อยู่ใกล้กันมักมีค่าคล้ายกัน คำถามหลายข้อใน `questions.md` จึงตอบได้ดีที่สุดบนแผนที่

| คำถาม (ตัวอย่าง) | ภาพที่เหมาะ |
|---|---|
| สถานีอยู่ที่ไหนบ้าง ครอบคลุมทั้งประเทศหรือไม่ | แผนที่จุด (point map) |
| จังหวัดใดมีจำนวนวันเกินมาตรฐาน 37.5 µg/m³ มากที่สุด | choropleth ระดับจังหวัด |
| cluster จากสัปดาห์ที่ 12 กระจุกตามภูมิศาสตร์หรือไม่ | แผนที่จุดระบายสีตาม cluster |
| ภาคใดมีสัดส่วนสถานีอากาศแย่มาก | treemap / sunburst |

ข้อควรจำ: แผนที่สวยงามดึงดูดสายตา แต่ก็ทำให้เข้าใจผิดได้ง่าย เพราะพื้นที่ใหญ่ดูสำคัญกว่าพื้นที่เล็กเสมอ

## 2. ระบบพิกัดอ้างอิง (CRS)

**CRS (Coordinate Reference System)** บอกว่าตัวเลขพิกัดหมายถึงตำแหน่งใดบนโลก ข้อมูลเดียวกันที่ CRS ต่างกันจะมีตัวเลขต่างกันโดยสิ้นเชิง

| CRS | หน่วย | ใช้เมื่อ |
|---|---|---|
| **EPSG:4326** (WGS 84, lat/lon) | องศา | เก็บข้อมูล, GPS, แผนที่เว็บ (Folium, Plotly), GeoJSON |
| **EPSG:32647** (WGS 84 / UTM zone 47N) | เมตร | คำนวณระยะทาง/พื้นที่/buffer สำหรับพื้นที่ส่วนใหญ่ของไทย (ลองจิจูด 96°–102°E) |
| **EPSG:32648** (WGS 84 / UTM zone 48N) | เมตร | พื้นที่ทางตะวันออกของ 102°E เช่น อุบลราชธานี มุกดาหาร นครพนม |

ทำไมห้ามคำนวณระยะทางด้วยองศา: 1 องศาลองจิจูดที่เส้นศูนย์สูตรยาวราว 111 กม. แต่ยิ่งไปทางขั้วโลกยิ่งสั้นลง และระยะ "0.5 องศา" ไม่ได้มีความหมายเป็นกิโลเมตร ดังนั้น **เก็บและแสดงผลใน 4326 แต่คำนวณใน projected CRS** ถ้าวิเคราะห์ทั้งประเทศ ให้เลือก zone เดียว (เช่น 32647) และยอมรับความคลาดเคลื่อนเล็กน้อยที่ขอบ

```python
import geopandas as gpd

print(gdf.crs)                     # ตรวจ CRS เสมอก่อนทำอะไร
gdf_m = gdf.to_crs(epsg=32647)     # แปลงพิกัด (reproject) เป็นเมตร
```

> `to_crs()` แปลงพิกัดจริง ส่วน `set_crs()` แค่ *ประกาศ* ว่าข้อมูลอยู่ใน CRS ใด ใช้ `set_crs` เฉพาะเมื่อข้อมูลไม่มี CRS ติดมาและเรารู้แน่ว่ามันคืออะไร

## 3. จาก lat/lon สู่ GeoDataFrame

**GeoDataFrame** คือ pandas DataFrame ที่มีคอลัมน์ `geometry` (จุด เส้น หรือ polygon) และมี CRS กำกับ

```python
import duckdb

con = duckdb.connect("data/pm25.duckdb", read_only=True)
st = con.sql("SELECT * FROM stations WHERE lat IS NOT NULL AND lon IS NOT NULL").df()

stations = gpd.GeoDataFrame(
    st, geometry=gpd.points_from_xy(st["lon"], st["lat"]), crs="EPSG:4326"
)
stations.head()
```

ข้อผิดพลาดที่พบบ่อยที่สุดคือ **สลับ lat กับ lon** `points_from_xy` รับ x = ลองจิจูด (~97–106 สำหรับไทย) ก่อน y = ละติจูด (~5–21) ตรวจด้วย `stations.total_bounds` ทุกครั้ง

## 4. ขอบเขตจังหวัดและ spatial join

### แหล่งข้อมูลขอบเขตจังหวัด

ใช้ **ไฟล์ GeoJSON ขอบเขตจังหวัดจากผู้สอน** (วางไว้ที่ `data/geo/`) หรือเลือกจากแหล่งเปิดที่รู้จัก เช่น geoBoundaries (ระดับ ADM1), Humanitarian Data Exchange (HDX) ของ OCHA หรือ GADM แต่ละแหล่งมีสัญญาอนุญาตต่างกัน (บางแหล่งห้ามใช้เชิงพาณิชย์หรือต้องระบุที่มา) **ต้องอ่านและบันทึกสัญญาอนุญาต แหล่งที่มา และวันที่ดาวน์โหลดไว้ใน README ของโครงการเสมอ** และเนื่องจาก `data/` ไม่ถูก commit ต้องเขียนวิธีได้ไฟล์มาไว้ด้วย

```python
prov = gpd.read_file("data/geo/thailand_provinces.geojson")
print(prov.crs, len(prov))     # ควรได้ 77 จังหวัด (ขึ้นกับแหล่งข้อมูล)
print(prov.columns.tolist())   # ตรวจชื่อคอลัมน์จริง อย่าเดา
```

ชื่อคอลัมน์ชื่อจังหวัดต่างกันในแต่ละแหล่ง (บางแหล่งเป็นภาษาอังกฤษ บางแหล่งมีทั้งไทยและอังกฤษ) ให้ดูจากผลจริงแล้วตั้งชื่อใหม่ เช่น `prov = prov.rename(columns={"<ชื่อคอลัมน์จริง>": "prov_name"})`

### Spatial join

**Spatial join** เชื่อมตารางด้วยความสัมพันธ์เชิงพื้นที่แทน key เช่น "จุดนี้อยู่ใน polygon ไหน"

```python
prov = prov.to_crs(stations.crs)           # CRS ต้องตรงกันก่อน join
joined = gpd.sjoin(stations, prov[["prov_name", "geometry"]],
                   how="left", predicate="within")
```

ประโยชน์สองอย่าง

1. **ได้จังหวัดจากพิกัด** สำหรับข้อมูลที่ไม่มีคอลัมน์จังหวัด
2. **ตรวจคุณภาพข้อมูล** เทียบ `province` ในตาราง `stations` กับ `prov_name` จาก spatial join ถ้าไม่ตรงกัน อาจเป็นพิกัดผิด สะกดชื่อต่างกัน หรือสถานีอยู่ติดเขตแดน สถานีที่ได้ `NaN` อาจอยู่นอกทุก polygon (เช่น พิกัดในทะเลหรือสลับ lat/lon)

## 5. Choropleth และข้อควรระวัง

**Choropleth** ระบายสีพื้นที่ตามค่าสถิติ เช่น ค่าเฉลี่ย PM2.5 รายจังหวัด

```python
agg = con.sql("""
    SELECT s.province, count(DISTINCT s.station_id) AS n_stations,
           avg(d.pm25_mean) AS pm25_mean,
           avg((d.pm25_mean > 37.5)::INT) AS share_over_std
    FROM daily_pm25_clean d JOIN stations s USING (station_id)
    GROUP BY s.province
""").df()

m = prov.merge(agg, left_on="prov_name", right_on="province", how="left")
ax = m.plot(column="share_over_std", cmap="YlOrRd", legend=True,
            missing_kwds={"color": "lightgrey", "label": "ไม่มีสถานี"})
```

| ข้อควรระวัง | ปัญหา | วิธีลด |
|---|---|---|
| **จังหวัดที่มีสถานีน้อย** | จังหวัดใหญ่ที่มีสถานีเดียวในตัวเมือง ถูกระบายสีทั้งจังหวัดตามสถานีนั้น ทั้งที่พื้นที่ส่วนใหญ่ไม่ได้วัด | แสดง `n_stations` ใน tooltip, ใช้สีเทาเมื่อไม่มีสถานี, พิจารณาใช้แผนที่จุดแทน |
| **จังหวัดไม่มีข้อมูล** | ถ้าเติม 0 จะดูเหมือนอากาศดี | ใช้ `missing_kwds` แยกสี "ไม่มีข้อมูล" ชัดเจน |
| **ขนาดพื้นที่หลอกตา** | จังหวัดใหญ่ (เช่น นครราชสีมา) ดึงสายตามากกว่ากรุงเทพฯ ที่มีสถานีหนาแน่น | ใช้คู่กับกราฟแท่งหรือแผนที่จุด |
| **MAUP** | ผลสรุปเปลี่ยนตามวิธีแบ่งหน่วยพื้นที่ (จังหวัด vs อำเภอ vs กริด) และระดับการรวม | ลองอย่างน้อย 2 ระดับ (ภาค/จังหวัด) และระบุในข้อจำกัด |
| **ค่าเฉลี่ยของค่าเฉลี่ย** | เฉลี่ยรายวันทุกสถานีรวมกัน สถานีที่มีข้อมูลมากจะมีน้ำหนักมาก | ระบุวิธีรวมให้ชัด เช่น เฉลี่ยรายสถานีก่อนแล้วจึงเฉลี่ยรายจังหวัด |

**Modifiable Areal Unit Problem (MAUP)** คือปรากฏการณ์ที่ข้อสรุปเชิงพื้นที่ขึ้นกับขนาดและขอบเขตของหน่วยที่เลือกรวมข้อมูล เช่น ระดับจังหวัดอาจดูว่าภาคอีสานอากาศดี แต่ระดับสถานีอาจมีจุดร้อนบางจุดที่ถูกเฉลี่ยกลบไป

## 6. แผนที่ interactive ด้วย Folium (เสริม)

**Folium** สร้างแผนที่ Leaflet ที่ซูมได้ ใส่ popup ได้ และบันทึกเป็นไฟล์ HTML

```python
import folium

fmap = folium.Map(location=[13.5, 101.0], zoom_start=6, tiles="OpenStreetMap")
for r in stations.itertuples():
    folium.CircleMarker(
        location=[r.lat, r.lon], radius=5, fill=True,
        tooltip=r.name_th,
        popup=folium.Popup(f"<b>{r.name_th}</b><br>{r.province}<br>{r.station_id}", max_width=250),
    ).add_to(fmap)
fmap.save("outputs/stations_map.html")
```

- Folium รับพิกัดเป็น `[lat, lon]` (กลับลำดับกับ `points_from_xy`)
- แผนที่พื้นหลัง OpenStreetMap ต้องระบุที่มา (Folium ใส่ attribution ให้อัตโนมัติ) ถ้าเปลี่ยน tiles ต้องตรวจเงื่อนไขของผู้ให้บริการ
- ทางเลือก: `stations.explore()` ของ GeoPandas สร้างแผนที่ Folium ให้ในบรรทัดเดียว เหมาะกับการสำรวจเร็ว ๆ

## 7. ข้อมูลลำดับชั้น: treemap และ sunburst

ข้อมูลของเรามีลำดับชั้นตามธรรมชาติ

```text
ประเทศไทย → ภาค (region) → จังหวัด (province) → สถานี (station)
```

ลำดับชั้นนี้คือ **ระดับ drill-down ของแดชบอร์ดสัปดาห์ที่ 14** การวาด treemap/sunburst ตอนนี้ช่วยตรวจว่าข้อมูลลำดับชั้นสะอาด (เช่น จังหวัดหนึ่งอยู่ได้ภาคเดียว ชื่อสะกดตรงกัน) ก่อนสร้างแดชบอร์ด

```python
import plotly.express as px

h = con.sql("""
    SELECT s.region, s.province, s.name_th, count(*) AS n_days,
           avg(d.pm25_mean) AS pm25_mean
    FROM daily_pm25_clean d JOIN stations s USING (station_id)
    GROUP BY ALL
""").df()

fig = px.treemap(h, path=[px.Constant("ประเทศไทย"), "region", "province", "name_th"],
                 values="n_days", color="pm25_mean",
                 color_continuous_scale="YlOrRd", color_continuous_midpoint=37.5)
fig.show()
```

| | Treemap | Sunburst |
|---|---|---|
| รูปแบบ | สี่เหลี่ยมซ้อนกัน | วงแหวนซ้อนกันจากศูนย์กลาง |
| อ่านขนาดเปรียบเทียบ | ง่ายกว่า (พื้นที่สี่เหลี่ยม) | ยากกว่า (มุมและวงนอกใหญ่กว่า) |
| เห็นโครงสร้างลำดับชั้น | พอใช้ | ชัดเจน |
| คลิกเพื่อ drill-down | ได้ทั้งสองแบบ | ได้ทั้งสองแบบ |

ข้อควรระวัง: `values` คือ *ขนาด* ของช่อง ควรเป็นสิ่งที่บวกกันได้ (เช่น จำนวนวันที่มีข้อมูล หรือจำนวนสถานี) ส่วนค่าเฉลี่ย PM2.5 บวกกันไม่ได้ จึงควรใช้เป็น *สี* ไม่ใช่ขนาด ค่าสีของระดับบน Plotly คำนวณเป็นค่าเฉลี่ยถ่วงน้ำหนักด้วย `values` โดยอัตโนมัติ

ถ้าข้อมูลมีแถวที่ `region` หรือ `province` เป็นค่าว่าง Plotly จะ error เรื่อง non-leaf rows ให้เติมค่า เช่น `"ไม่ระบุ"` หรือตัดออกพร้อมบันทึกไว้

## สรุป

- ตรวจ CRS เสมอ: เก็บและแสดงผลใน EPSG:4326 คำนวณระยะทาง/พื้นที่ใน UTM 47N/48N (EPSG:32647/32648)
- `points_from_xy(lon, lat)` สร้างจุดจากพิกัด, `sjoin` เชื่อมจุดกับ polygon และช่วยตรวจคุณภาพคอลัมน์จังหวัด
- choropleth ต้องแสดงจำนวนสถานีและพื้นที่ไม่มีข้อมูลอย่างตรงไปตรงมา และระวัง MAUP
- ใช้ข้อมูลขอบเขตจากแหล่งที่ระบุได้ และบันทึกสัญญาอนุญาต
- treemap/sunburst แสดงลำดับชั้น ภาค → จังหวัด → สถานี ซึ่งเป็นโครงของ drill-down ในสัปดาห์หน้า

## คำถามทบทวน

1. ทำไมการคำนวณ buffer 10 กม. รอบสถานีต้องแปลงเป็น EPSG:32647 ก่อน ถ้าทำใน EPSG:4326 จะเกิดอะไรขึ้น
2. สถานีหนึ่งในตาราง `stations` ระบุจังหวัดอุบลราชธานี แต่ spatial join ให้ผลเป็นศรีสะเกษ เป็นไปได้จากสาเหตุอะไรบ้าง
3. จังหวัด A มีสถานี 1 แห่ง จังหวัด B มี 8 แห่ง choropleth ระบายสีทั้งสองจังหวัดด้วยค่าเฉลี่ย ผู้อ่านควรถูกเตือนเรื่องอะไร
4. ยกตัวอย่าง MAUP จากข้อมูล PM2.5 ของตนเอง
5. ทำไมจึงไม่ควรใช้ค่าเฉลี่ย PM2.5 เป็น `values` ใน treemap

## อ่านเพิ่มเติม

- GeoPandas User Guide: *Managing Projections*, *Spatial Joins*, *Mapping and Plotting Tools*
- Lovelace, R., Nowosad, J., & Muenchow, J. *Geocomputation with R* บท Reprojecting geographic data (แนวคิดใช้ได้กับ Python)
- เอกสาร Folium: Quickstart
- Plotly: *Treemap Charts* และ *Sunburst Charts* in Python
- Openshaw, S. (1984). *The Modifiable Areal Unit Problem*

➡️ [คู่มือปฏิบัติการสัปดาห์ที่ 13](lab.md)
