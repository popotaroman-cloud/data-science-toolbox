---
title: "กระดานสถานะการเขียนหนังสือ"
---

# กระดานสถานะ

แก้เฉพาะแถวของบทที่ตนจองหรือรับผิดชอบ สถานะที่ใช้ได้: `todo` · `drafting` · `review` · `revising` · `done` (ดู [AUTHORING.md](AUTHORING.md#ขั้นตอนการทำงาน))

ผู้ดูแลเล่ม (book maintainer): อาจารย์วาโย ปุยะติ

## บท

| บท | ไฟล์ | ผู้เขียน | ผู้ตรวจ | สถานะ | วันที่ | สัปดาห์ที่เกี่ยวข้อง |
|---|---|---|---|---|---|---|
| 0 | `chapters/00-overview.qmd` | | | todo | | 1 |
| 1 | `chapters/01-data-science-eda.qmd` | | | todo | | 1 |
| 2 | `chapters/02-reproducible-environment.qmd` | | | todo | | 1 |
| 3 | `chapters/03-version-control.qmd` | | | todo | | 1 |
| 4 | `chapters/04-questions-hypotheses.qmd` | | | todo | | 2 |
| 5 | `chapters/05-data-acquisition.qmd` | | | todo | | 3 |
| 6 | `chapters/06-analytical-databases.qmd` | | | todo | | 4 |
| 7 | `chapters/07-sql-analysis.qmd` | | | todo | | 4 |
| 8 | `chapters/08-data-wrangling.qmd` | | | todo | | 5 |
| 9 | `chapters/09-data-quality.qmd` | | | todo | | 6 |
| 10 | `chapters/10-missing-data.qmd` | | | todo | | 7 |
| 11 | `chapters/11-visual-perception.qmd` | | | todo | | 9 |
| 12 | `chapters/12-interactive-viz.qmd` | | | todo | | 10 |
| 13 | `chapters/13-exploratory-statistics.qmd` | | | todo | | 11 |
| 14 | `chapters/14-time-series.qmd` | | | todo | | 11 |
| 15 | `chapters/15-multivariate.qmd` | | | todo | | 12 |
| 16 | `chapters/16-synthetic-privacy.qmd` | | | todo | | 12 |
| 17 | `chapters/17-spatial-data.qmd` | | | todo | | 13 |
| 18 | `chapters/18-hierarchical-data.qmd` | | | todo | | 13 |
| 19 | `chapters/19-storytelling-reports.qmd` | | | todo | | 14 |
| 20 | `chapters/20-dashboards.qmd` | | | todo | | 14 |
| 21 | `chapters/21-case-study-pm25.qmd` | | | todo | | 15 |
| 22 | `chapters/22-ethics-ai.qmd` | | | todo | | 1, 15 |

## ส่วนหน้าและส่วนท้ายเล่ม

| ส่วน | ไฟล์ | ผู้เขียน | ผู้ตรวจ | สถานะ | วันที่ |
|---|---|---|---|---|---|
| คำนำ + ข้อตกลงการเขียน + การเตรียมเครื่อง | `index.qmd` | ผู้ดูแลเล่ม | | todo | |
| ภาคผนวก ก Python | `appendices/a-python.qmd` | | | todo | |
| ภาคผนวก ข shell และ Git | `appendices/b-shell-git.qmd` | | | todo | |
| ภาคผนวก ค SQL ฉบับอ้างอิง | `appendices/c-sql-reference.qmd` | | | todo | |
| ภาคผนวก ง Air4Thai และข้อมูลเปิด | `appendices/d-air4thai-open-data.qmd` | | | todo | |
| ภาคผนวก จ คณิตศาสตร์พื้นฐาน | `appendices/e-math.qmd` | | | todo | |
| ภาคผนวก ฉ การแก้ปัญหา | `appendices/f-troubleshooting.qmd` | | | todo | |
| ภาคผนวก ช แนวคำตอบ | `appendices/answers/NN.qmd` (รวมผ่าน `appendices/g-answers.qmd`) | ผู้เขียนแต่ละบท | | — | |
| ภาคผนวก ซ ชุดเครื่องมือฉบับอ้างอิงเร็ว | `appendices/h-toolbox-reference.qmd` | | | todo | |
| อภิธานศัพท์ | `glossary/NN.yml` (รวมอัตโนมัติ) | ผู้เขียนแต่ละบท | ผู้ดูแลเล่ม | — | |
| บรรณานุกรม | `refs/NN.bib` (รวมอัตโนมัติ) | ผู้เขียนแต่ละบท | ผู้ดูแลเล่ม | — | |
| ดัชนี | เครื่องหมาย `.idx*` ในเนื้อหา (สร้างอัตโนมัติ) | ผู้ดูแลเล่ม | | — | |

## ลำดับการเขียนที่แนะนำ

1. **บทนำร่อง:** บท 0 และบท 7 (ใช้กำหนดมาตรฐานรูปแบบและความลึก ต้องเป็น `done` ก่อนเปิดให้เขียนบทอื่นพร้อมกัน)
2. **ระลอกที่ 1:** บท 1–6, 8 (ขึ้นต่อกันน้อย)
3. **ระลอกที่ 2:** บท 9–16
4. **ระลอกที่ 3:** บท 17–20 และภาคผนวก ก–ฉ, ซ
5. **ระลอกสุดท้าย:** บท 21–22 (ต้องอ้างถึงทุกบท) แล้วผู้ดูแลเล่มรวมอภิธานศัพท์ บรรณานุกรม และดัชนี
