"""ตรวจและประกอบหนังสือจากบทที่เขียนแยกกัน

    python scripts/assemble.py               # ตรวจทุกบทที่ไม่ใช่ todo + สร้าง glossary.qmd และ book-index.qmd
    python scripts/assemble.py --chapter 07  # ตรวจเฉพาะบทที่ 07 (ผู้เขียนใช้ก่อนส่ง review) ไม่สร้างไฟล์
    python scripts/assemble.py --check       # ตรวจทุกบท ไม่สร้างไฟล์

รันจากโฟลเดอร์ book/ หรือที่ใดก็ได้ (script หาโฟลเดอร์ book/ เอง) ออกด้วย exit code 1 ถ้ามี error
กฎทั้งหมดมาจาก AUTHORING.md
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

BOOK = Path(__file__).resolve().parent.parent
THAI_LETTER = {"a": "ก", "b": "ข", "c": "ค", "d": "ง", "e": "จ", "f": "ฉ", "g": "ช", "h": "ซ"}
FIXED = ["วัตถุประสงค์การเรียนรู้", "กรณีศึกษา", "ข้อผิดพลาดที่พบบ่อย", "สรุป", "แบบฝึกหัด", "อ่านเพิ่มเติม"]
IDX_RE = re.compile(r"\[([^\]]+)\]\{\.(idx(?:-tool|-data)?)\}")
LABEL_RE = re.compile(r"\{[^}]*#((?:sec|fig|tbl|eq)-[A-Za-z0-9_-]+)[^}]*\}")
H_RE = re.compile(r"^(#{1,3})\s+(.*?)\s*(\{[^}]*\})?\s*$")


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, msg: str):
        self.errors.append(f"ERROR  {where}: {msg}")

    def warn(self, where: str, msg: str):
        self.warnings.append(f"WARN   {where}: {msg}")


def norm(title: str) -> str:
    """ทำชื่อหัวข้อให้อยู่ในรูปเดียวกันก่อนเทียบกับ toc.md"""
    t = title.replace("★", "").replace("`", "")
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def strip_number(title: str) -> str:
    return re.sub(r"^([0-9]+|[ก-ฮ])\.[0-9]+\s+", "", title)


def thai_sort_key(s: str) -> str:
    """เรียงคำไทยตามพยัญชนะต้น (ย้ายสระหน้า เ แ โ ใ ไ ไปไว้หลังพยัญชนะ)"""
    s = s.strip("`").casefold()
    if len(s) > 1 and s[0] in "เแโใไ":
        s = s[1] + s[0] + s[2:]
    return s


def parse_toc() -> dict[str, list[str]]:
    """คืนค่า {รหัส: [หัวข้อย่อยตามลำดับ]} รหัสเป็น '07' สำหรับบท และ 'c' สำหรับภาคผนวก"""
    toc: dict[str, list[str]] = {}
    key = None
    for line in (BOOK / "toc.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#{2,3} บทที่ (\d+) ", line)
        if m:
            key = f"{int(m.group(1)):02d}"
            toc[key] = []
            continue
        m = re.match(r"^### ภาคผนวก ([ก-ฮ]) ", line)
        if m:
            key = {v: k for k, v in THAI_LETTER.items()}[m.group(1)]
            toc[key] = []
            continue
        if line.startswith("#"):
            key = None
            continue
        m = re.match(r"^(?:[0-9]+|[ก-ฮ])\.[0-9]+\s+(.+)$", line)
        if key and m:
            toc[key].append(norm(m.group(1)))
    return toc


def front_matter(text: str) -> dict:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def book_files() -> list[tuple[str, Path]]:
    files = [(p.name[:2], p) for p in sorted((BOOK / "chapters").glob("[0-9][0-9]-*.qmd"))]
    files += [(p.name[0], p) for p in sorted((BOOK / "appendices").glob("[a-h]-*.qmd")) if p.name[0] != "g"]
    return files


def headings(text: str):
    """คืนรายการ (ระดับ, ชื่อ, attrs, เลขบรรทัด) โดยข้าม code block"""
    out, in_code = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = H_RE.match(line)
        if m:
            out.append((len(m.group(1)), m.group(2), m.group(3) or "", i))
    return out


def check_file(code: str, path: Path, toc: dict, rep: Report):
    text = path.read_text(encoding="utf-8")
    where = path.relative_to(BOOK).as_posix()
    is_chapter = code.isdigit()
    manual_numbers = code == "00" or not is_chapter   # บทที่ 0 และภาคผนวกพิมพ์เลขเอง

    h2 = [h for h in headings(text) if h[0] == 2]
    content = [h for h in h2 if not any(h[1].startswith(f) for f in FIXED)]
    fixed = [h for h in h2 if any(h[1].startswith(f) for f in FIXED)]

    # 1) หัวข้อย่อยตรงกับ toc.md ทั้งชื่อและลำดับ
    want = toc.get(code, [])
    got = [norm(strip_number(h[1])) for h in content]
    for i, w in enumerate(want):
        if i >= len(got):
            rep.error(where, f"ขาดหัวข้อ '{w}' (ลำดับที่ {i + 1} ตาม toc.md)")
        elif got[i] != w:
            rep.error(where, f"บรรทัด {content[i][3]}: หัวข้อ '{got[i]}' ไม่ตรงกับ toc.md ลำดับที่ {i + 1} '{w}'")
    for h in content[len(want):]:
        rep.error(where, f"บรรทัด {h[3]}: หัวข้อ '{h[1]}' ไม่มีใน toc.md")

    # 2) กฎการใส่เลข
    for h in content:
        numbered_by_hand = re.match(r"^([0-9]+|[ก-ฮ])\.[0-9]+\s", h[1])
        if manual_numbers:
            if not numbered_by_hand:
                rep.error(where, f"บรรทัด {h[3]}: บทที่ 0/ภาคผนวกต้องพิมพ์เลขหัวข้อเอง เช่น '0.3 ...'")
            if ".unnumbered" not in h[2]:
                rep.error(where, f"บรรทัด {h[3]}: ต้องใส่ {{.unnumbered}}")
        elif numbered_by_hand:
            rep.error(where, f"บรรทัด {h[3]}: ห้ามพิมพ์เลขหัวข้อเอง (Quarto ใส่ให้)")
        if "#sec-" not in h[2]:
            rep.warn(where, f"บรรทัด {h[3]}: หัวข้อ '{h[1]}' ไม่มี label {{#sec-...}} (ดัชนีและการอ้างอิงจะชี้มาที่หัวข้อนี้ไม่ได้)")
        if "★" in h[1] and "★ เนื้อหาเชิงลึก" not in text:
            rep.error(where, f"บรรทัด {h[3]}: หัวข้อ ★ ต้องมี callout '★ เนื้อหาเชิงลึก'")

    # 3) หัวข้อประจำบท
    for h in fixed:
        if ".unnumbered" not in h[2]:
            rep.error(where, f"บรรทัด {h[3]}: หัวข้อประจำบท '{h[1]}' ต้องใส่ .unnumbered")
    if is_chapter and code != "00":
        for f in FIXED:
            if not any(h[1].startswith(f) for h in fixed):
                rep.error(where, f"ขาดหัวข้อประจำบท '{f}'")

    # 4) สิ่งที่ห้ามมี
    for i, line in enumerate(text.splitlines(), 1):
        if "VERIFY" in line:
            rep.error(where, f"บรรทัด {i}: ยังมี VERIFY ค้างอยู่")
        if re.match(r"^\s*```\{(python|r|julia|ojs)", line):
            rep.error(where, f"บรรทัด {i}: ห้ามใช้ code chunk ที่รันได้ ให้ใช้ ```python")
        if re.search(r"<[^<>\n]{2,40}>", line) and not line.lstrip().startswith(("<!--", "<", "|")) and "{{<" not in line:
            if re.search(r"<(ชื่อ|เนื้อหา|บทนำ|NN|อธิบาย|ใช้|ประเมิน|เปรียบเทียบ|\.\.\.)", line):
                rep.error(where, f"บรรทัด {i}: ยังมีข้อความแม่แบบ <...> ค้างอยู่")

    # 5) label ควรขึ้นต้นด้วยรหัสของบท
    prefix = f"ch{code}" if is_chapter else f"app{code}"
    for lab in LABEL_RE.findall(text):
        if not lab.split("-", 1)[1].startswith(prefix):
            rep.warn(where, f"label '{lab}' ควรขึ้นต้นด้วย '{lab.split('-')[0]}-{prefix}-'")


def scan_labels(files) -> dict[str, tuple[Path, str]]:
    """label → (ไฟล์, ชื่อหัวข้อ)"""
    labels = {}
    for _, p in files + [(None, q) for q in sorted((BOOK / "appendices" / "answers").glob("*.qmd"))]:
        for _, title, attrs, _ in headings(p.read_text(encoding="utf-8")):
            m = re.search(r"#((?:sec)-[A-Za-z0-9_-]+)", attrs)
            if m:
                labels[m.group(1)] = (p, title)
    return labels


def check_shared(files, rep: Report):
    # label ซ้ำข้ามไฟล์
    seen = defaultdict(list)
    for _, p in files + [(None, q) for q in sorted((BOOK / "appendices" / "answers").glob("*.qmd"))]:
        for lab in LABEL_RE.findall(p.read_text(encoding="utf-8")):
            seen[lab].append(p.relative_to(BOOK).as_posix())
    for lab, where in seen.items():
        if len(where) > 1:
            rep.error(", ".join(where), f"label '{lab}' ซ้ำกัน")
    # BibTeX key ซ้ำข้ามบท
    keys = defaultdict(list)
    for bib in sorted((BOOK / "refs").glob("*.bib")):
        for k in re.findall(r"^@\w+\{([^,\s]+),", bib.read_text(encoding="utf-8"), re.M):
            keys[k].append(bib.name)
    for k, where in keys.items():
        if len(where) > 1:
            rep.error(", ".join(where), f"BibTeX key '{k}' ซ้ำกัน ให้ใช้ key เดิมจากไฟล์แรก")


def load_glossary(rep: Report) -> list[dict]:
    entries, owner = [], {}
    for f in sorted((BOOK / "glossary").glob("*.yml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or []
        for e in data:
            where = f"glossary/{f.name}"
            if not isinstance(e, dict) or not e.get("term") or not e.get("definition"):
                rep.error(where, f"รายการต้องมี term และ definition: {e!r}")
                continue
            k = e["term"].casefold()
            if k in owner:
                rep.error(where, f"ศัพท์ '{e['term']}' ซ้ำกับ {owner[k]} ให้ใช้ see_also แทน")
                continue
            owner[k] = where
            entries.append(e)
    return entries


def link(labels, lab: str | None) -> str:
    if not lab or lab not in labels:
        return ""
    p, title = labels[lab]
    rel = p.relative_to(BOOK).as_posix()
    title = re.sub(r"\s*★\s*", " ", title).strip()
    return f"[{title}]({rel}#{lab})"


def write_glossary(entries, labels):
    out = ["# อภิธานศัพท์ {.unnumbered}", "",
           "<!-- สร้างโดย scripts/assemble.py จาก glossary/*.yml ห้ามแก้ไฟล์นี้โดยตรง -->", ""]
    if not entries:
        out.append("ยังไม่มีศัพท์ในอภิธานศัพท์")
    for e in sorted(entries, key=lambda e: e["term"].casefold()):
        th = f" ({e['th']})" if e.get("th") else ""
        out.append(f"**{e['term']}**{th}")
        out.append(f": {' '.join(str(e['definition']).split())}")
        extra = []
        if link(labels, e.get("section")):
            extra.append(f"อธิบายใน {link(labels, e['section'])}")
        if e.get("see_also"):
            extra.append("ดูเพิ่ม " + ", ".join(e["see_also"]))
        if extra:
            out.append(f"  {' · '.join(extra)}")
        out.append("")
    (BOOK / "glossary.qmd").write_text("\n".join(out) + "\n", encoding="utf-8")


def write_index(files, labels):
    groups = {"idx": defaultdict(set), "idx-tool": defaultdict(set), "idx-data": defaultdict(set)}
    for _, p in files:
        current = None
        for line in p.read_text(encoding="utf-8").splitlines():
            m = H_RE.match(line)
            if m and m.group(3):
                lm = re.search(r"#(sec-[A-Za-z0-9_-]+)", m.group(3))
                if lm:
                    current = lm.group(1)
            for term, kind in IDX_RE.findall(line):
                groups[kind][term].add(current)
    titles = {"idx": "ดัชนีหัวเรื่อง", "idx-tool": "ดัชนีเครื่องมือและฟังก์ชัน", "idx-data": "ดัชนีชุดข้อมูลและกรณีศึกษา"}
    out = ["# ดัชนี {.unnumbered}", "",
           "<!-- สร้างโดย scripts/assemble.py จากเครื่องหมาย .idx ในทุกบท ห้ามแก้ไฟล์นี้โดยตรง -->", ""]
    for kind, title in titles.items():
        out += [f"## {title} {{.unnumbered}}", ""]
        if not groups[kind]:
            out += ["ยังไม่มีรายการ", ""]
        for term in sorted(groups[kind], key=thai_sort_key):
            order = list(labels)               # เรียงตามลำดับที่หัวข้อปรากฏในเล่ม
            labs = sorted((lab for lab in groups[kind][term] if lab in labels), key=order.index)
            refs = [link(labels, lab) for lab in labs]
            out.append(f"- {term} — {' · '.join(refs) if refs else '(ไม่มี label ของหัวข้อ)'}")
        out.append("")
    (BOOK / "book-index.qmd").write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chapter", help="ตรวจเฉพาะบทนี้ เช่น 07 หรือภาคผนวก c")
    ap.add_argument("--check", action="store_true", help="ตรวจอย่างเดียว ไม่สร้างไฟล์")
    args = ap.parse_args()

    toc, rep = parse_toc(), Report()
    files = book_files()
    active = []
    for code, p in files:
        status = front_matter(p.read_text(encoding="utf-8")).get("status", "todo")
        if args.chapter and code != args.chapter.lower().zfill(2 if args.chapter.isdigit() else 1):
            continue
        if status == "todo" and not args.chapter:
            continue
        active.append((code, p))
        check_file(code, p, toc, rep)
    if args.chapter and not active:
        sys.exit(f"ไม่พบบท/ภาคผนวก '{args.chapter}'")

    check_shared(files, rep)
    entries = load_glossary(rep)
    labels = scan_labels(files)
    for e in entries:
        if e.get("section") and e["section"] not in labels:
            rep.warn("glossary", f"ศัพท์ '{e['term']}' อ้าง section '{e['section']}' ที่ยังไม่มี")

    generate = not args.check and not args.chapter
    if generate:
        write_glossary(entries, labels)
        write_index(files, labels)

    for line in rep.warnings + rep.errors:
        print(line)
    scope = f"บท {args.chapter}" if args.chapter else f"{len(active)} บท/ภาคผนวกที่ไม่ใช่ todo"
    print(f"\nตรวจ {scope}: {len(rep.errors)} error, {len(rep.warnings)} warning"
          + (" · สร้าง glossary.qmd และ book-index.qmd แล้ว" if generate else ""))
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
