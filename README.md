# 1145100 ชุดเครื่องมือสำหรับวิทยาการข้อมูล (Data Science Toolbox)

**เว็บไซต์รายวิชา:** <https://popotaroman-cloud.github.io/data-science-toolbox/>

เอกสารประกอบการสอนและคู่มือปฏิบัติการ ภาคการศึกษาที่ 2 ปีการศึกษา 2569
หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการข้อมูลและนวัตกรรมซอฟต์แวร์ มหาวิทยาลัยอุบลราชธานี

ผู้สอน: อาจารย์วาโย ปุยะติ · หน่วยกิต 3(2-2-5) · 15 สัปดาห์

## แนวคิดของรายวิชา

ผู้เรียนสร้าง **ระบบสำรวจข้อมูลระบบเดียวตลอดภาคการศึกษา** ใน repository ของตนเอง ผลงานแต่ละสัปดาห์เป็น input ของสัปดาห์ถัดไป จนได้ระบบที่ข้อมูลไหลจากแหล่งต้นทางถึงแดชบอร์ด

```text
แหล่งข้อมูล (API / เว็บ) → DuckDB (ไฟล์เดียว) → pandas → Plotly → Streamlit dashboard
```

โจทย์ตัวอย่างคือ **ระบบสำรวจคุณภาพอากาศ PM2.5 ของประเทศไทย** ผู้เรียนเลือกโดเมนอื่นได้ แต่ใช้สถาปัตยกรรมเดียวกัน

หลักการสอน: ตั้งคำถามก่อนใช้เครื่องมือ · สอนเครื่องมือเมื่อจำเป็นต้องใช้ (just-in-time) · ใช้ AI ช่วยเขียนโค้ดได้ แต่ต้องอธิบายและตรวจสอบผลได้

## โครงสร้าง repository

```text
.
├── README.md               ← ไฟล์นี้
├── syllabus.md             ← สรุปรายวิชา ผลการเรียนรู้ แผนการสอน และการประเมินผล
├── environment.yml         ← สภาพแวดล้อม conda ของรายวิชา
├── pyproject.toml          ← สภาพแวดล้อมสำหรับผู้ใช้ uv
├── _quarto.yml             ← render เอกสารทั้งหมดเป็นเว็บไซต์ด้วย Quarto
├── index.qmd               ← หน้าแรกของเว็บไซต์ (ดึงเนื้อหาจากไฟล์นี้)
├── weeks/
│   ├── week01/
│   │   ├── index.md        ← เอกสารประกอบการสอน
│   │   └── lab.md          ← คู่มือปฏิบัติการ
│   └── ... week15/
├── slides/
│   ├── week01.qmd          ← สไลด์ (Quarto revealjs)
│   └── ... week15.qmd
├── book/                   ← หนังสือประกอบการสอน (Quarto book) ดู book/AUTHORING.md
│   ├── chapters/           ← บทที่ 0–22
│   └── appendices/         ← ภาคผนวก ก–ซ
└── scripts/build_site.sh   ← สร้างเว็บไซต์พร้อมหนังสือใน _site/
```

## แผนการสอน

| สัปดาห์ | หัวข้อ | CLO | ปฏิบัติการ | สไลด์ |
|---|---|---|---|---|
| [1](weeks/week01/index.md) | ภาพรวม EDA, สภาพแวดล้อมการทำงาน และ Git/GitHub | 1 | [lab](weeks/week01/lab.md) | [slides](slides/week01.qmd) |
| [2](weeks/week02/index.md) | การตั้งคำถามเชิงวิเคราะห์และสมมติฐาน | 4, 6 | [lab](weeks/week02/lab.md) | [slides](slides/week02.qmd) |
| [3](weeks/week03/index.md) | การได้มาซึ่งข้อมูลจาก API และเว็บไซต์ | 2 | [lab](weeks/week03/lab.md) | [slides](slides/week03.qmd) |
| [4](weeks/week04/index.md) | การจัดเก็บและสืบค้นข้อมูลด้วย DuckDB, SQL และ Parquet | 2 | [lab](weeks/week04/lab.md) | [slides](slides/week04.qmd) |
| [5](weeks/week05/index.md) | การจัดการข้อมูลและการเชื่อม SQL กับ Python | 2 | [lab](weeks/week05/lab.md) | [slides](slides/week05.qmd) |
| [6](weeks/week06/index.md) | Data profiling และการตรวจคุณภาพข้อมูล | 3 | [lab](weeks/week06/lab.md) | [slides](slides/week06.qmd) |
| [7](weeks/week07/index.md) | การวิเคราะห์ข้อมูลสูญหาย (MCAR / MAR / MNAR) | 3 | [lab](weeks/week07/lab.md) | [slides](slides/week07.qmd) |
| [8](weeks/week08/index.md) | **Checkpoint 1:** นำเสนอ data pipeline | 1–3 | [lab](weeks/week08/lab.md) | [slides](slides/week08.qmd) |
| [9](weeks/week09/index.md) | หลักการ visualization และ grammar of graphics | 4 | [lab](weeks/week09/lab.md) | [slides](slides/week09.qmd) |
| [10](weeks/week10/index.md) | Interactive visualization และข้อมูลขนาดใหญ่ | 4 | [lab](weeks/week10/lab.md) | [slides](slides/week10.qmd) |
| [11](weeks/week11/index.md) | สถิติเชิงสำรวจและ time series | 4 | [lab](weeks/week11/lab.md) | [slides](slides/week11.qmd) |
| [12](weeks/week12/index.md) | ข้อมูลหลายมิติ, outlier และข้อมูลสังเคราะห์ (PDPA) | 4, 6 | [lab](weeks/week12/lab.md) | [slides](slides/week12.qmd) |
| [13](weeks/week13/index.md) | ข้อมูลเชิงพื้นที่และข้อมูลลำดับชั้น | 4 | [lab](weeks/week13/lab.md) | [slides](slides/week13.qmd) |
| [14](weeks/week14/index.md) | สื่อสารข้อค้นพบและ reproducibility | 5 | [lab](weeks/week14/lab.md) | [slides](slides/week14.qmd) |
| [15](weeks/week15/index.md) | **นำเสนอโครงการสุดท้าย** | 1–6 | [lab](weeks/week15/lab.md) | [slides](slides/week15.qmd) |

## หนังสือประกอบการสอน

**ชุดเครื่องมือสำหรับวิทยาการข้อมูล: การสำรวจข้อมูลเชิงลึกด้วย Python และ SQL ตั้งแต่แหล่งข้อมูลถึงแดชบอร์ด** (โฟลเดอร์ [`book/`](book/)) มี 23 บทและภาคผนวก 8 ภาค ใช้กรณีศึกษา PM2.5 เดียวกับรายวิชา เอกสารรายสัปดาห์ตอบว่า *ทำอย่างไร* ส่วนหนังสือตอบเพิ่มว่า *ทำไม* เอกสารแต่ละสัปดาห์มีลิงก์ "อ่านประกอบในหนังสือ" ไปยังบทที่เกี่ยวข้อง อ่านฉบับเว็บได้ที่ <https://popotaroman-cloud.github.io/data-science-toolbox/book/> ความคืบหน้าของแต่ละบทอยู่ใน [`book/STATUS.md`](book/STATUS.md)

## เริ่มต้นใช้งาน

```bash
conda env create -f environment.yml
conda activate dstoolbox
jupyter lab
```

หรือใช้ uv:

```bash
uv sync
uv run jupyter lab
```

ดูรายละเอียดการติดตั้งใน [คู่มือปฏิบัติการสัปดาห์ที่ 1](weeks/week01/lab.md)

## Render เป็นเว็บไซต์

```bash
quarto preview              # ดูตัวอย่างเว็บไซต์ (ไม่รวมหนังสือ)
quarto preview book         # ดูตัวอย่างหนังสือ
./scripts/build_site.sh     # สร้างเว็บไซต์พร้อมหนังสือใน _site/ (หนังสืออยู่ที่ _site/book/)
```

ต้อง render เว็บไซต์ก่อนหนังสือเสมอ เพราะการ render เว็บไซต์ทั้งหมดจะล้างโฟลเดอร์ `_site/` script ข้างต้นทำตามลำดับนี้ให้

## Publish เว็บไซต์

เว็บไซต์อยู่บน GitHub Pages (branch `gh-pages`) หลังแก้เอกสาร ให้สร้างเว็บไซต์พร้อมหนังสือก่อน แล้ว publish โดยไม่ render ซ้ำ (ถ้าให้ `quarto publish` render เอง หนังสือจะหายไปจากเว็บไซต์)

```bash
./scripts/build_site.sh
quarto publish gh-pages --no-render
```
