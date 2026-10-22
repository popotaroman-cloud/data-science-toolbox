# ประมวลรายวิชา 1145100 Data Science Toolbox

## ผลลัพธ์การเรียนรู้ระดับรายวิชา (CLOs)

เมื่อจบรายวิชา ผู้เรียนสามารถ

| รหัส | ผลลัพธ์การเรียนรู้ |
|---|---|
| CLO1 | ตั้งค่าสภาพแวดล้อมการทำงานและใช้ Git/GitHub จัดการโครงการข้อมูลร่วมกับผู้อื่นได้ |
| CLO2 | รวบรวม จัดเก็บ และสืบค้นข้อมูลจากหลายแหล่งด้วย Python และ SQL ได้ |
| CLO3 | ประเมินคุณภาพข้อมูลและเลือกวิธีจัดการข้อมูลสูญหายได้อย่างมีเหตุผล |
| CLO4 | สำรวจข้อมูลด้วยภาพและสถิติ เพื่อตอบคำถามเชิงวิเคราะห์ที่ตั้งไว้ได้ |
| CLO5 | สื่อสารข้อค้นพบผ่านรายงานและแดชบอร์ดแบบโต้ตอบที่ผู้อื่นทำซ้ำได้ |
| CLO6 | ใช้ข้อมูลอย่างมีจริยธรรม คำนึงถึงความเป็นส่วนตัวตาม PDPA และตรวจสอบผลลัพธ์จากเครื่องมือ AI ได้ |

## Toolbox ของรายวิชา

| ขั้นตอน | เครื่องมือหลัก | เครื่องมือเสริม |
|---|---|---|
| Environment & workflow | conda/uv, VS Code, Jupyter, Git/GitHub | Google Colab |
| ได้มาซึ่งข้อมูล | requests | BeautifulSoup |
| จัดเก็บและสืบค้น | DuckDB, SQL, Parquet | Apache Arrow (แนวคิด) |
| จัดการข้อมูล | pandas | Polars |
| Profiling & คุณภาพข้อมูล | ydata-profiling, pandera | skimpy, Sweetviz |
| ข้อมูลสูญหาย | missingno | — |
| Visualization | seaborn, Plotly | Altair, PyGWalker, Datashader |
| สถิติเชิงสำรวจ | SciPy, statsmodels | pingouin |
| สำรวจหลายมิติ | scikit-learn (PCA, clustering) | UMAP, PyOD |
| ข้อมูลสังเคราะห์ | Faker | SDV, SMOTE |
| ข้อมูลเชิงพื้นที่ | GeoPandas | Folium |
| สื่อสารผล | Quarto, Streamlit | Power BI / Looker Studio |

## แผนการสอน

ทุกสัปดาห์: บรรยาย 2 ชั่วโมง · ปฏิบัติการ 2 ชั่วโมง · ศึกษาด้วยตนเอง 5 ชั่วโมง

| สัปดาห์ | หัวข้อ | เครื่องมือ | ผลงานที่เพิ่มในระบบ | CLO |
|---|---|---|---|---|
| 1 | ภาพรวม EDA และ data lifecycle, สภาพแวดล้อมการทำงาน, Git/GitHub | conda/uv, VS Code, Jupyter, terminal, Git, GitHub | สภาพแวดล้อมพร้อมใช้ + repo โครงการ | 1 |
| 2 | การตั้งคำถามเชิงวิเคราะห์และสมมติฐาน | pandas (first look), Markdown | `questions.md` + first look notebook | 4, 6 |
| 3 | การได้มาซึ่งข้อมูล | requests, BeautifulSoup | script ดึงข้อมูล | 2 |
| 4 | การจัดเก็บและสืบค้นข้อมูล | DuckDB, SQL, Parquet | ฐานข้อมูล DuckDB | 2 |
| 5 | การจัดการข้อมูลและการเชื่อม SQL กับ Python | pandas, Polars, DuckDB | ชุดข้อมูลที่แปลงรูปแล้ว | 2 |
| 6 | Data profiling และการตรวจคุณภาพข้อมูล | ydata-profiling, skimpy, pandera | รายงาน profiling + กฎตรวจข้อมูล | 3 |
| 7 | การวิเคราะห์ข้อมูลสูญหาย (MCAR / MAR / MNAR) | missingno, pandas | ชุดข้อมูลสะอาด + data dictionary | 3 |
| 8 | **Checkpoint 1:** นำเสนอ data pipeline | — | pipeline ทำงานครบ (demo) | 1–3 |
| 9 | หลักการ visualization และ grammar of graphics | seaborn, Altair | กราฟ univariate / bivariate | 4 |
| 10 | Interactive visualization และข้อมูลขนาดใหญ่ | Plotly, PyGWalker, Datashader | กราฟ interactive | 4 |
| 11 | สถิติเชิงสำรวจและ time series | SciPy, pingouin, statsmodels | ผลทดสอบสมมติฐาน, trend/seasonality | 4 |
| 12 | ข้อมูลหลายมิติ, outlier และข้อมูลสังเคราะห์ (PDPA) | scikit-learn, UMAP, PyOD, Faker, SDV | การจัดกลุ่ม / outlier / ชุดข้อมูลทดสอบ | 4, 6 |
| 13 | ข้อมูลเชิงพื้นที่และข้อมูลลำดับชั้น | GeoPandas, Folium, Plotly treemap/sunburst | แผนที่และกราฟลำดับชั้น | 4 |
| 14 | สื่อสารข้อค้นพบและ reproducibility | Quarto, Streamlit, DuckDB (read-only + cache) | data story report + dashboard drill-down | 5 |
| 15 | **นำเสนอโครงการสุดท้าย** | — | ระบบที่ทำงานจริง + repo ที่ทำซ้ำได้ | 1–6 |

## การประเมินผล

| วิธีการประเมิน | สัปดาห์ | สัดส่วน | CLO |
|---|---|---|---|
| แบบฝึกปฏิบัติรายสัปดาห์ (commit ใน repo) | 1–14 | 25% | 1–4 |
| Checkpoint 1: data pipeline | 8 | 20% | 1–3 |
| Data story report (Quarto) | 14 | 15% | 4, 5 |
| โครงการสุดท้าย: ระบบและแดชบอร์ด | 15 | 30% | 1–6 |
| Peer review / code review บน GitHub | ตลอดภาค | 10% | 1, 6 |

## นโยบายการใช้ AI

อนุญาตให้ใช้ LLM ช่วยเขียนโค้ดได้ทุกงาน โดยมีเงื่อนไข

1. ผู้เรียนต้องอธิบายโค้ดทุกบรรทัดที่ส่งได้ หากอธิบายไม่ได้ถือว่าไม่ใช่ผลงานของตนเอง
2. ระบุใน commit message หรือ `AI_USAGE.md` ว่าใช้ AI ช่วยส่วนใด
3. ตรวจผลลัพธ์จาก AI กับข้อมูลจริงทุกครั้ง โดยเฉพาะชื่อคอลัมน์ ชื่อฟังก์ชัน และ endpoint ของ API ซึ่ง AI มักสร้างขึ้นเองโดยไม่มีอยู่จริง

## ไฟล์ตัวอย่างจากผู้สอน

ใช้แทนข้อมูลจริงเมื่อ API ของ Air4Thai ใช้งานไม่ได้ ผู้สอนแจกผ่านระบบส่งงาน (ไม่อยู่ใน repo นี้) ให้วางไว้ที่ `data/sample/` ของโครงการ

| ไฟล์ | ใช้ในสัปดาห์ |
|---|---|
| `air4thai_sample.json` | 2–3 (first look, ทดสอบ script ดึงข้อมูล) |
| `stations_sample.csv` | 3–5, 13 |
| `pm25_hourly_sample.csv` | 4–7 |
| `pm25_sample.duckdb` | 9 เป็นต้นไป (ฐานข้อมูลที่ผ่านสัปดาห์ 7 แล้ว) |

## แหล่งข้อมูลและตำรา

- data.go.th — ศูนย์กลางข้อมูลเปิดภาครัฐ
- Air4Thai — ข้อมูลคุณภาพอากาศ กรมควบคุมมลพิษ
- Kaggle
- McKinney, W. *Python for Data Analysis*. O'Reilly Media.
- Wickham, H., Çetinkaya-Rundel, M., & Grolemund, G. *R for Data Science*. O'Reilly Media.
