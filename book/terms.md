---
title: "ศัพท์มาตรฐานของหนังสือ"
---

# ศัพท์มาตรฐาน

ทุกบทต้องใช้ศัพท์ตามตารางนี้ (ดูกฎการใช้ใน [AUTHORING.md](AUTHORING.md#ศัพท์เทคนิค))

| รูปแบบ | ความหมาย |
|---|---|
| **แปล** | ใช้คำไทย ครั้งแรกในบทวงเล็บภาษาอังกฤษ เช่น ข้อมูลสูญหาย (missing data) |
| **ทับศัพท์** | เขียนเป็นภาษาอังกฤษตลอด ไม่แปล เช่น commit |
| **ไทย** | ใช้คำไทยอย่างเดียว ไม่ต้องวงเล็บ |

ศัพท์ที่ยังไม่มีในตาราง ให้เสนอในส่วน [ศัพท์ที่รอพิจารณา](#ศัพท์ที่รอพิจารณา) ผ่าน PR ของบท

## แนวคิดทั่วไปและกระบวนการ

| English | ใช้ในหนังสือ | รูปแบบ |
|---|---|---|
| Data science | วิทยาการข้อมูล | แปล |
| Exploratory Data Analysis (EDA) | การสำรวจข้อมูล (EDA) | แปล · ใช้ตัวย่อ EDA ได้หลังครั้งแรก |
| Confirmatory analysis | การวิเคราะห์เชิงยืนยัน | แปล |
| Data lifecycle | วงจรชีวิตข้อมูล | แปล |
| Pipeline | pipeline | ทับศัพท์ |
| Reproducibility | การทำซ้ำได้ | แปล |
| Hypothesis | สมมติฐาน | ไทย |
| Analytical question | คำถามเชิงวิเคราะห์ | ไทย |
| Domain knowledge | ความรู้เชิงโดเมน | ไทย |
| Stakeholder | ผู้มีส่วนได้ส่วนเสีย | แปล |
| Garden of forking paths | garden of forking paths | ทับศัพท์ |
| HARKing | HARKing | ทับศัพท์ · อธิบายเต็มครั้งแรก |

## สภาพแวดล้อมและ version control

| English | ใช้ในหนังสือ | รูปแบบ |
|---|---|---|
| Environment (Python) | สภาพแวดล้อม | แปล |
| Virtual environment | virtual environment | ทับศัพท์ |
| Package | แพ็กเกจ | ไทย |
| Library | ไลบรารี | ไทย |
| Terminal / shell | terminal / shell | ทับศัพท์ |
| Notebook | notebook | ทับศัพท์ |
| Kernel | kernel | ทับศัพท์ |
| Repository (repo) | repository | ทับศัพท์ · ย่อเป็น repo ได้ |
| Commit | commit | ทับศัพท์ |
| Branch | branch | ทับศัพท์ |
| Merge / rebase | merge / rebase | ทับศัพท์ |
| Pull request (PR) | pull request | ทับศัพท์ · ย่อเป็น PR ได้ |
| Code review | การ review โค้ด | ไทย |
| Version control | version control | ทับศัพท์ |

## การได้มาและจัดเก็บข้อมูล

| English | ใช้ในหนังสือ | รูปแบบ |
|---|---|---|
| Data acquisition | การได้มาซึ่งข้อมูล | ไทย |
| API | API | ทับศัพท์ |
| Endpoint | endpoint | ทับศัพท์ |
| Request / response | request / response | ทับศัพท์ |
| Web scraping | web scraping | ทับศัพท์ |
| Rate limit | rate limit | ทับศัพท์ |
| Raw data | ข้อมูลดิบ | ไทย |
| Database | ฐานข้อมูล | ไทย |
| Table / view | ตาราง / view | ไทย / ทับศัพท์ |
| Primary key | primary key | ทับศัพท์ |
| Columnar storage | การจัดเก็บแบบ columnar | ไทย |
| Idempotent | idempotent | ทับศัพท์ · อธิบายครั้งแรกว่า "รันซ้ำได้ผลเท่าเดิม" |
| Upsert | upsert | ทับศัพท์ |
| Join | join | ทับศัพท์ |
| Aggregation | การรวมกลุ่ม (aggregation) | แปล |
| Window function | window function | ทับศัพท์ |
| Query | query | ทับศัพท์ |

## การจัดการและคุณภาพข้อมูล

| English | ใช้ในหนังสือ | รูปแบบ |
|---|---|---|
| DataFrame | DataFrame | ทับศัพท์ |
| Tidy data | tidy data | ทับศัพท์ |
| Wide / long format | รูปแบบกว้าง / รูปแบบยาว | แปล |
| Reshape | การปรับรูป (reshape) | แปล |
| Resample | resample | ทับศัพท์ |
| Timezone | เขตเวลา | แปล |
| Data quality | คุณภาพข้อมูล | ไทย |
| Data profiling | data profiling | ทับศัพท์ |
| Validation | การตรวจสอบความถูกต้อง (validation) | แปล |
| Schema | schema | ทับศัพท์ |
| Sentinel value | ค่าแทน (sentinel value) | แปล |
| Data dictionary | พจนานุกรมข้อมูล (data dictionary) | แปล |
| Missing data | ข้อมูลสูญหาย | แปล |
| Missing value | ค่าสูญหาย | แปล |
| MCAR / MAR / MNAR | MCAR / MAR / MNAR | ทับศัพท์ · อธิบายเต็มครั้งแรก |
| Imputation | การเติมค่า (imputation) | แปล |
| Multiple imputation | การเติมค่าแบบหลายชุด (multiple imputation) | แปล |
| Interpolation | การประมาณค่าในช่วง (interpolation) | แปล |
| Completeness | ความครบถ้วน | ไทย |
| Outlier | ค่าผิดปกติ (outlier) | แปล |

## การสำรวจด้วยภาพ

| English | ใช้ในหนังสือ | รูปแบบ |
|---|---|---|
| Visualization | การนำเสนอข้อมูลด้วยภาพ (visualization) | แปล · ใช้ "visualization" ได้หลังครั้งแรก |
| Chart / plot | กราฟ | ไทย |
| Grammar of graphics | grammar of graphics | ทับศัพท์ |
| Encoding (visual) | การเข้ารหัสภาพ | แปล |
| Aesthetic mapping | การจับคู่ตัวแปรกับคุณลักษณะภาพ | แปล |
| Facet / small multiples | facet / small multiples | ทับศัพท์ |
| Interactive | เชิงโต้ตอบ | ไทย |
| Overplotting | overplotting | ทับศัพท์ |
| Colormap / palette | ชุดสี (palette) | แปล |
| Dashboard | แดชบอร์ด | ไทย |
| Drill-down | drill-down | ทับศัพท์ |

## สถิติและหลายมิติ

| English | ใช้ในหนังสือ | รูปแบบ |
|---|---|---|
| Distribution | การแจกแจง | ไทย |
| Mean / median | ค่าเฉลี่ย / มัธยฐาน | ไทย |
| Interquartile range (IQR) | พิสัยระหว่างควอร์ไทล์ (IQR) | แปล |
| Robust statistics | สถิติแบบทนทาน (robust statistics) | แปล |
| Skewness | ความเบ้ | แปล |
| Confidence interval | ช่วงความเชื่อมั่น | แปล |
| p-value | p-value | ทับศัพท์ |
| Effect size | ขนาดอิทธิพล (effect size) | แปล |
| Statistical significance | นัยสำคัญทางสถิติ | ไทย |
| Multiple comparisons | การเปรียบเทียบหลายครั้ง | แปล |
| Bootstrap | bootstrap | ทับศัพท์ |
| Permutation test | permutation test | ทับศัพท์ |
| Correlation | สหสัมพันธ์ | แปล |
| Time series | อนุกรมเวลา | แปล |
| Trend / seasonality | แนวโน้ม (trend) / ฤดูกาล (seasonality) | แปล |
| Autocorrelation | สหสัมพันธ์ในตัว (autocorrelation) | แปล |
| Stationarity | stationarity | ทับศัพท์ |
| Decomposition | การแยกองค์ประกอบ | แปล |
| Principal Component Analysis (PCA) | การวิเคราะห์องค์ประกอบหลัก (PCA) | แปล |
| Clustering | การจัดกลุ่ม (clustering) | แปล |
| Scaling / standardization | การปรับสเกล / การทำให้เป็นมาตรฐาน | แปล |
| Synthetic data | ข้อมูลสังเคราะห์ | แปล |

## ความเป็นส่วนตัว เชิงพื้นที่ และการสื่อสาร

| English | ใช้ในหนังสือ | รูปแบบ |
|---|---|---|
| Personal data | ข้อมูลส่วนบุคคล | ไทย (ตาม พ.ร.บ.) |
| Sensitive data | ข้อมูลส่วนบุคคลที่มีความอ่อนไหว | ไทย (ตาม พ.ร.บ.) |
| PDPA | พ.ร.บ.คุ้มครองข้อมูลส่วนบุคคล พ.ศ. 2562 (PDPA) | แปล · ใช้ PDPA ได้หลังครั้งแรก |
| Anonymization | การทำให้เป็นข้อมูลนิรนาม (anonymization) | แปล |
| Pseudonymization | การแฝงข้อมูล (pseudonymization) | แปล |
| Re-identification | การระบุตัวตนซ้ำ | แปล |
| Differential privacy | differential privacy | ทับศัพท์ |
| Coordinate Reference System (CRS) | ระบบพิกัดอ้างอิง (CRS) | แปล |
| Projection | เส้นโครงแผนที่ | แปล |
| Spatial join | spatial join | ทับศัพท์ |
| Choropleth map | แผนที่ choropleth | ทับศัพท์ |
| Data storytelling | การเล่าเรื่องด้วยข้อมูล | แปล |
| Literate programming | literate programming | ทับศัพท์ |
| Caching | caching | ทับศัพท์ |

## ชื่อที่ต้องเขียนให้ถูก

| ถูก | ห้ามเขียน |
|---|---|
| PM2.5 | PM 2.5, pm2.5, PM25 (ในเนื้อหา) |
| µg/m³ | ug/m3, มคก./ลบ.ม. |
| Air4Thai | air4thai, Air 4 Thai |
| กรมควบคุมมลพิษ | คพ. (ใช้ตัวย่อได้หลังครั้งแรก) |
| DuckDB, pandas, Polars, Plotly, seaborn, Altair, Streamlit, Quarto, GeoPandas, scikit-learn, Git, GitHub | Duckdb, Pandas, polar, plotly, Seaborn, git hub |
| Python 3.12 | python3.12 (ในเนื้อหา) |

## ศัพท์ที่รอพิจารณา

<!-- ผู้เขียนเพิ่มแถวที่นี่ใน PR ของบท ผู้ดูแลเล่มย้ายขึ้นตารางด้านบนเมื่อรับรอง -->

| English | เสนอให้ใช้ | รูปแบบ | เสนอโดย (บท) |
|---|---|---|---|
| Normalization / denormalization | normalization / denormalization | ทับศัพท์ | 6 |
| OLTP / OLAP | OLTP / OLAP | ทับศัพท์ · อธิบายเต็มครั้งแรก | 6 |
| Parquet | Parquet | ทับศัพท์ (ชื่อรูปแบบไฟล์) | 6 |
| CTE (Common Table Expression) | CTE | ทับศัพท์ · อธิบายเต็มครั้งแรก | 7 |
| Fan-out (join) | fan-out | ทับศัพท์ · อธิบายครั้งแรก | 8 |
| Preattentive attribute | preattentive attribute | ทับศัพท์ · อธิบายครั้งแรก | 11 |
| Lie factor | lie factor | ทับศัพท์ (ศัพท์ของ Tufte) | 11 |
| Data-ink ratio | อัตราส่วนหมึกข้อมูล (data-ink ratio) | แปล | 11 |
| Annotation | คำอธิบายประกอบ (annotation) | แปล | 11 |
| Trace (Plotly) | trace | ทับศัพท์ | 12 |
| Linked views | linked views | ทับศัพท์ | 12 |
| Brushing | brushing | ทับศัพท์ | 12 |
| Binning | binning | ทับศัพท์ | 12 |
| Accessibility | การเข้าถึงได้ (accessibility) | แปล | 12 |
| Alt text | ข้อความทางเลือก (alt text) | แปล | 12 |
| Median absolute deviation (MAD) | MAD | ทับศัพท์ · อธิบายเต็มครั้งแรก | 13 |
| Geometric mean | ค่าเฉลี่ยเรขาคณิต | ไทย | 13 |
| Effective sample size | ขนาดตัวอย่างที่มีผล (effective sample size) | แปล | 13 |
| Breakdown point | breakdown point | ทับศัพท์ | 13 |
| Simpson's paradox | Simpson's paradox | ทับศัพท์ | 13 |
| Ecological fallacy | ecological fallacy | ทับศัพท์ | 13 |
| ECDF | ECDF | ทับศัพท์ · อธิบายเต็มครั้งแรก | 13 |
| Residual (time series) | ส่วนเหลือ (residual) | แปล | 14 |
| Smoothing | การปรับให้เรียบ (smoothing) | แปล | 14 |
| Change point | จุดเปลี่ยน (change point) | แปล | 14 |
| ASOF join | ASOF join | ทับศัพท์ | 14 |
| Full grid | full grid | ทับศัพท์ | 14 |
| Loading | loading | ทับศัพท์ | 15 |
| Explained variance ratio | สัดส่วนความแปรปรวนที่อธิบายได้ (explained variance ratio) | แปล | 15 |
| Silhouette | silhouette | ทับศัพท์ | 15 |
| Dendrogram | dendrogram | ทับศัพท์ | 15 |
| Adjusted Rand index (ARI) | adjusted Rand index (ARI) | ทับศัพท์ | 15 |
| Mahalanobis distance | ระยะทาง Mahalanobis | ไทย | 15 |
| Isolation Forest / LOF | Isolation Forest / LOF | ทับศัพท์ | 15 |
| Quasi-identifier | ตัวระบุทางอ้อม (quasi-identifier) | แปล | 16 |
| Data controller / processor | ผู้ควบคุมข้อมูลส่วนบุคคล / ผู้ประมวลผลข้อมูลส่วนบุคคล | ไทย (ตาม พ.ร.บ.) | 16 |
| k-anonymity / l-diversity | k-anonymity / l-diversity | ทับศัพท์ | 16 |
| Privacy budget (ε) | งบประมาณความเป็นส่วนตัว (privacy budget) | แปล | 16 |
| Gaussian copula | Gaussian copula | ทับศัพท์ | 16 |
| Class imbalance | ข้อมูลไม่สมดุล (class imbalance) | แปล | 16 |
| Data leakage | การรั่วไหลของข้อมูล (data leakage) | แปล | 16 |
| Datum / ellipsoid / geoid | datum / ellipsoid / geoid | ทับศัพท์ | 17 |
| Spatial autocorrelation | สหสัมพันธ์เชิงพื้นที่ (spatial autocorrelation) | แปล | 17 |
| MAUP | MAUP | ทับศัพท์ · อธิบายเต็มครั้งแรก | 17 |
| Voronoi polygon | Voronoi polygon | ทับศัพท์ | 17 |
| Spatial interpolation | การประมาณค่าเชิงพื้นที่ (spatial interpolation) | แปล | 17 |
| IDW / kriging / semivariogram | IDW / kriging / semivariogram | ทับศัพท์ | 17 |
| Hierarchy | ลำดับชั้น | ไทย | 18 |
| Additive / semi-additive measure | ตัวชี้วัดที่รวมขึ้นได้ / รวมขึ้นได้บางส่วน | แปล | 18 |
| Roll-up / slice / dice | roll-up / slice / dice | ทับศัพท์ | 18 |
| OLAP / data cube | OLAP / data cube | ทับศัพท์ | 18 |
| Treemap / sunburst / icicle | treemap / sunburst / icicle | ทับศัพท์ | 18 |
| Breadcrumb | แถบเส้นทาง (breadcrumb) | แปล | 18 |
| Finding first / pyramid principle | ข้อค้นพบก่อน / หลักการพีระมิด | แปล | 19 |
| Big idea | big idea | ทับศัพท์ | 19 |
| Martini glass structure | โครงสร้างแก้วมาร์ตินี (martini glass) | แปล | 19 |
| Inline code (Quarto) | inline code | ทับศัพท์ | 19 |
| Parameterized report | รายงานแบบมีพารามิเตอร์ (parameterized report) | แปล | 19 |
| Replicability | การทำซ้ำผลได้ (replicability) | แปล | 19 |
| Fresh-clone test | fresh-clone test | ทับศัพท์ | 19 |
| Sensitivity analysis | การวิเคราะห์ความไว (sensitivity analysis) | แปล | 19 |
| Operational / analytical / strategic dashboard | แดชบอร์ดเชิงปฏิบัติการ / เชิงวิเคราะห์ / เชิงกลยุทธ์ | แปล | 20 |
| KPI | ตัวชี้วัดหลัก (KPI) | แปล | 20 |
| Session state / callback / rerun | session state / callback / rerun | ทับศัพท์ | 20 |
| Deploy | deploy | ทับศัพท์ | 20 |
| Business intelligence (BI) | business intelligence (BI) | ทับศัพท์ | 20 |
| Architecture decision record (ADR) | บันทึกการตัดสินใจออกแบบ (ADR) | แปล | 21 |
| Data lineage | ลำดับวงศ์ของข้อมูล (data lineage) | แปล | 21 |
| Data ethics | จริยธรรมข้อมูล | ไทย | 22 |
| Bias | อคติ (bias) | แปล | 22 |
| Automation bias | การเชื่อระบบอัตโนมัติ (automation bias) | แปล | 22 |
| Hallucination | hallucination | ทับศัพท์ | 22 |
| License | สัญญาอนุญาต (license) | แปล | 22 |
| Copyleft / permissive | copyleft / permissive | ทับศัพท์ | 22 |
| Questionable research practices | แนวปฏิบัติการวิจัยที่น่าสงสัย | แปล | 22 |
| Environmental justice | ความยุติธรรมเชิงสิ่งแวดล้อม (environmental justice) | แปล | 22 |
