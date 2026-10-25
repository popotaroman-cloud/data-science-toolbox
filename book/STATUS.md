---
title: "กระดานสถานะการเขียนหนังสือ"
---

# กระดานสถานะ

แก้เฉพาะแถวของบทที่ตนจองหรือรับผิดชอบ สถานะที่ใช้ได้: `todo` · `drafting` · `review` · `revising` · `done` · `published`

แก้ STATUS.md ใน branch ของบทตน (ไม่ใช่ใน `main`) แต่ละบทแก้คนละแถว จึงรวมกันได้โดยไม่ชน (ดู [AUTHORING.md](AUTHORING.md#ขั้นตอนการทำงาน))

ผู้ดูแลเล่ม (book maintainer): อาจารย์วาโย ปุยะติ

## บท

| บท | ไฟล์ | branch | ผู้เขียน | ผู้ตรวจ | สถานะ | วันที่ | สัปดาห์ |
|---|---|---|---|---|---|---|---|
| 0 | `chapters/00-overview.qmd` | `book/ch00-overview` | | | todo | | 1 |
| 1 | `chapters/01-data-science-eda.qmd` | `book/ch01-data-science-eda` | | | todo | | 1 |
| 2 | `chapters/02-reproducible-environment.qmd` | `book/ch02-reproducible-environment` | | | todo | | 1 |
| 3 | `chapters/03-version-control.qmd` | `book/ch03-version-control` | | | todo | | 1 |
| 4 | `chapters/04-questions-hypotheses.qmd` | `book/ch04-questions-hypotheses` | | | todo | | 2 |
| 5 | `chapters/05-data-acquisition.qmd` | `book/ch05-data-acquisition` | | | todo | | 3 |
| 6 | `chapters/06-analytical-databases.qmd` | `book/ch06-analytical-databases` | | | todo | | 4 |
| 7 | `chapters/07-sql-analysis.qmd` | `book/ch07-sql-analysis` | | | todo | | 4 |
| 8 | `chapters/08-data-wrangling.qmd` | `book/ch08-data-wrangling` | | | todo | | 5 |
| 9 | `chapters/09-data-quality.qmd` | `book/ch09-data-quality` | | | todo | | 6 |
| 10 | `chapters/10-missing-data.qmd` | `book/ch10-missing-data` | | | todo | | 7 |
| 11 | `chapters/11-visual-perception.qmd` | `book/ch11-visual-perception` | | | todo | | 9 |
| 12 | `chapters/12-interactive-viz.qmd` | `book/ch12-interactive-viz` | agent:claude | | drafting | 2026-10-25 | 10 |
| 13 | `chapters/13-exploratory-statistics.qmd` | `book/ch13-exploratory-statistics` | agent:claude | | drafting | 2026-10-25 | 11 |
| 14 | `chapters/14-time-series.qmd` | `book/ch14-time-series` | agent:claude | | drafting | 2026-10-25 | 11 |
| 15 | `chapters/15-multivariate.qmd` | `book/ch15-multivariate` | agent:claude | | drafting | 2026-10-25 | 12 |
| 16 | `chapters/16-synthetic-privacy.qmd` | `book/ch16-synthetic-privacy` | agent:claude | | drafting | 2026-10-25 | 12 |
| 17 | `chapters/17-spatial-data.qmd` | `book/ch17-spatial-data` | agent:claude | | drafting | 2026-10-25 | 13 |
| 18 | `chapters/18-hierarchical-data.qmd` | `book/ch18-hierarchical-data` | agent:claude | | drafting | 2026-10-25 | 13 |
| 19 | `chapters/19-storytelling-reports.qmd` | `book/ch19-storytelling-reports` | agent:claude | | drafting | 2026-10-25 | 14 |
| 20 | `chapters/20-dashboards.qmd` | `book/ch20-dashboards` | agent:claude | | drafting | 2026-10-25 | 14 |
| 21 | `chapters/21-case-study-pm25.qmd` | `book/ch21-case-study-pm25` | agent:claude | | drafting | 2026-10-25 | 15 |
| 22 | `chapters/22-ethics-ai.qmd` | `book/ch22-ethics-ai` | | | todo | | 1, 15 |

## ส่วนหน้าและส่วนท้ายเล่ม

| ส่วน | ไฟล์ | branch | ผู้เขียน | ผู้ตรวจ | สถานะ | วันที่ |
|---|---|---|---|---|---|---|
| คำนำ + ข้อตกลงการเขียน + การเตรียมเครื่อง | `index.qmd` | `book-assembly` (ผู้ดูแลเล่ม) | ผู้ดูแลเล่ม | | todo | |
| ภาคผนวก ก Python | `appendices/a-python.qmd` | `book/app-a-python` | | | todo | |
| ภาคผนวก ข shell และ Git | `appendices/b-shell-git.qmd` | `book/app-b-shell-git` | | | todo | |
| ภาคผนวก ค SQL ฉบับอ้างอิง | `appendices/c-sql-reference.qmd` | `book/app-c-sql-reference` | | | todo | |
| ภาคผนวก ง Air4Thai และข้อมูลเปิด | `appendices/d-air4thai-open-data.qmd` | `book/app-d-air4thai-open-data` | | | todo | |
| ภาคผนวก จ คณิตศาสตร์พื้นฐาน | `appendices/e-math.qmd` | `book/app-e-math` | | | todo | |
| ภาคผนวก ฉ การแก้ปัญหา | `appendices/f-troubleshooting.qmd` | `book/app-f-troubleshooting` | | | todo | |
| ภาคผนวก ช แนวคำตอบ | `appendices/answers/NN.qmd` (รวมผ่าน `appendices/g-answers.qmd`) | branch ของแต่ละบท / `assemble.py` | ผู้เขียนแต่ละบท | | — | |
| ภาคผนวก ซ ชุดเครื่องมือฉบับอ้างอิงเร็ว | `appendices/h-toolbox-reference.qmd` | `book/app-h-toolbox-reference` | | | todo | |
| อภิธานศัพท์ | `glossary.qmd` จาก `glossary/NN.yml` (สร้างอัตโนมัติ) | branch ของแต่ละบท / `assemble.py` | ผู้เขียนแต่ละบท | ผู้ดูแลเล่ม | — | |
| บรรณานุกรม | `refs/NN.bib` (รวมอัตโนมัติ) | branch ของแต่ละบท / `assemble.py` | ผู้เขียนแต่ละบท | ผู้ดูแลเล่ม | — | |
| ดัชนี | `book-index.qmd` จากเครื่องหมาย `.idx*` (สร้างอัตโนมัติ) | branch ของแต่ละบท / `assemble.py` | ผู้ดูแลเล่ม | | — | |

## ลำดับการเขียนที่แนะนำ

1. **บทนำร่อง:** บท 0 และบท 7 (ใช้กำหนดมาตรฐานรูปแบบและความลึก ต้องเป็น `done` ก่อนเปิดให้เขียนบทอื่นพร้อมกัน)
2. **ระลอกที่ 1:** บท 1–6, 8 (ขึ้นต่อกันน้อย)
3. **ระลอกที่ 2:** บท 9–16
4. **ระลอกที่ 3:** บท 17–20 และภาคผนวก ก–ฉ, ซ
5. **ระลอกสุดท้าย:** บท 21–22 (ต้องอ้างถึงทุกบท) แล้วผู้ดูแลเล่มรวมอภิธานศัพท์ บรรณานุกรม และดัชนี
