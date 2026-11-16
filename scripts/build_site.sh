#!/usr/bin/env bash
# สร้างเว็บไซต์รายวิชาพร้อมหนังสือใน _site/
# ลำดับสำคัญ: render เว็บไซต์ทั้งหมดจะล้าง _site/ ก่อน จึงต้องคัดลอกหนังสือ (book/_book/) เข้า _site/book/ ทีหลัง
set -euo pipefail
cd "$(dirname "$0")/.."

python book/scripts/assemble.py      # ตรวจเล่มและสร้างอภิธานศัพท์/ดัชนีใหม่
quarto render                        # เว็บไซต์: index, syllabus, weeks, slides → _site/
quarto render book                   # หนังสือ → book/_book/
rm -rf _site/book && cp -r book/_book _site/book
echo "เสร็จแล้ว: เปิด _site/index.html หรือเผยแพร่ด้วย quarto publish gh-pages --no-render"
