# /// script
# requires-python = ">=3.12"
# dependencies = ["requests", "truststore", "pandas"]
# ///
"""สร้างไฟล์ตัวอย่างของรายวิชา (sample-data/) จาก Air4Thai กรมควบคุมมลพิษ

    uv run scripts/build_sample_data.py --start 2026-09-01 --end 2026-11-17 --cache <โฟลเดอร์เก็บ response ดิบ>

ผลลัพธ์ใน --out (ค่าเริ่มต้น sample-data/)
  stations_sample.csv       ตาราง stations (province และ region เติมจากข้อความพื้นที่)
  pm25_hourly_sample.csv    ตาราง measurements รายชั่วโมง (คอลัมน์ตรงกับสัปดาห์ที่ 4)
  air4thai_sample.json      response ของ API ค่าปัจจุบัน ณ เวลาที่รันสคริปต์

หมายเหตุ: API ย้อนหลังเก็บข้อมูลประมาณ 3 เดือน วันที่เก่ากว่านั้นจะได้ผลว่าง ตรวจสอบ endpoint ล่าสุดก่อนรัน
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import truststore

truststore.inject_into_ssl()          # server ของ Air4Thai ส่ง certificate chain ไม่ครบ ห้ามใช้ verify=False
sys.stdout.reconfigure(encoding="utf-8")

CUR = "https://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
HIST = "https://air4thai.com/forweb/getHistoryData.php"
HEADERS = {"User-Agent": "dstoolbox-course/0.1 (Ubon Ratchathani University, education)"}
PARAM_SETS = ("PM25,PM10,O3,CO,NO2,SO2", "PM25,PM10", "PM25")   # บางสถานีไม่มีบางพารามิเตอร์ API จะตอบ error ที่ไม่ใช่ JSON
POLLUTANTS = ["pm25", "pm10", "o3", "co", "no2", "so2"]

# 6 ภาคตามราชบัณฑิตยสถาน ชื่อภาคไม่มีคำว่า "ภาค" นำหน้า
REGIONS = {
    "เหนือ": "เชียงราย เชียงใหม่ น่าน พะเยา แพร่ แม่ฮ่องสอน ลำปาง ลำพูน อุตรดิตถ์",
    "ตะวันออกเฉียงเหนือ": "กาฬสินธุ์ ขอนแก่น ชัยภูมิ นครพนม นครราชสีมา บึงกาฬ บุรีรัมย์ มหาสารคาม มุกดาหาร ยโสธร ร้อยเอ็ด เลย ศรีสะเกษ สกลนคร สุรินทร์ หนองคาย หนองบัวลำภู อำนาจเจริญ อุดรธานี อุบลราชธานี",
    "กลาง": "กรุงเทพฯ กำแพงเพชร ชัยนาท นครนายก นครปฐม นครสวรรค์ นนทบุรี ปทุมธานี พระนครศรีอยุธยา พิจิตร พิษณุโลก เพชรบูรณ์ ลพบุรี สมุทรปราการ สมุทรสงคราม สมุทรสาคร สิงห์บุรี สุโขทัย สุพรรณบุรี สระบุรี อ่างทอง อุทัยธานี",
    "ตะวันออก": "จันทบุรี ฉะเชิงเทรา ชลบุรี ตราด ปราจีนบุรี ระยอง สระแก้ว",
    "ตะวันตก": "กาญจนบุรี ตาก ประจวบคีรีขันธ์ เพชรบุรี ราชบุรี",
    "ใต้": "กระบี่ ชุมพร ตรัง นครศรีธรรมราช นราธิวาส ปัตตานี พังงา พัทลุง ภูเก็ต ยะลา ระนอง สงขลา สตูล สุราษฎร์ธานี",
}
PROV2REG = {p: r for r, ps in REGIONS.items() for p in ps.split()}
ALIASES = {"ประจวบคิรีขันธ์": "ประจวบคีรีขันธ์"}      # สะกดผิดในข้อมูลต้นทาง (พบเมื่อ ต.ค. 2569)


def get_json(url: str, params: dict | None = None, tries: int = 3):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=90)
            r.raise_for_status()
            return r.json()
        except Exception as e:                        # เครือข่ายล้ม หรือไม่ใช่ JSON: รอแล้วลองใหม่
            print(f"  retry {i + 1}: {type(e).__name__}", flush=True)
            time.sleep(2 * (i + 1))
    return None


def province_of(area: str, station_type: str) -> str:
    if station_type == "BKK" or "กรุงเทพ" in area or "กทม" in area:
        return "กรุงเทพฯ"
    last = ALIASES.get(re.sub(r"^(จ\.|จังหวัด)\s*", "", area.split(",")[-1].strip()), "")
    last = last or re.sub(r"^(จ\.|จังหวัด)\s*", "", area.split(",")[-1].strip())
    for p in PROV2REG:
        if last.endswith(p):
            return p
    for p in PROV2REG:
        if p in area:
            return p
    return last


def month_ranges(start: date, end: date):
    d = start.replace(day=1)
    while d <= end:
        nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        yield max(d, start), min(date.fromordinal(nxt.toordinal() - 1), end)
        d = nxt


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", required=True, type=date.fromisoformat)
    ap.add_argument("--end", required=True, type=date.fromisoformat)
    ap.add_argument("--out", default="sample-data", type=Path)
    ap.add_argument("--cache", required=True, type=Path, help="โฟลเดอร์เก็บ response ดิบ (อย่าให้อยู่ใน repo)")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    a.cache.mkdir(parents=True, exist_ok=True)

    cur = get_json(CUR)
    if not cur:
        sys.exit("ดึง API ค่าปัจจุบันไม่ได้")
    (a.out / "air4thai_sample.json").write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")

    rows_st = []
    for s in cur["stations"]:
        prov = province_of(s.get("areaTH", ""), s.get("stationType", ""))
        rows_st.append(dict(station_id=s["stationID"], name_th=(s.get("nameTH") or "").strip(),
                            name_en=(s.get("nameEN") or "").strip(), province=prov, region=PROV2REG.get(prov),
                            lat=float(s["lat"]), lon=float(s["long"]), station_type=s.get("stationType")))
    stations = pd.DataFrame(rows_st)
    print("stations:", len(stations), "| province ไม่ตรงภาค:", sorted(stations.loc[stations.region.isna(), "province"].unique()))

    rows, skipped = [], []
    for i, sid in enumerate(stations.station_id, 1):
        for d0, d1 in month_ranges(a.start, a.end):
            f = a.cache / f"hist_{sid}_{d0:%Y-%m}.json"
            if f.exists():
                j = json.loads(f.read_text(encoding="utf-8"))
            else:
                j = None
                for params in PARAM_SETS:
                    j = get_json(HIST, dict(stationID=sid, param=params, type="hr", sdate=str(d0), edate=str(d1),
                                            stime="00", etime="23"), tries=1)
                    time.sleep(0.4)                   # ไม่ยิง API ถี่เกินไป
                    if j:
                        break
                if not j:
                    skipped.append(f"{sid} {d0:%Y-%m}")
                    continue
                f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
            for rec in (j.get("stations") or [{}])[0].get("data") or []:
                rows.append({"station_id": sid, "ts": rec["DATETIMEDATA"],
                             **{k.lower(): rec.get(k) for k in ("PM25", "PM10", "O3", "CO", "NO2", "SO2")}})
        if i % 25 == 0:
            print(f"  {i}/{len(stations)} สถานี, {len(rows):,} แถว", flush=True)

    m = pd.DataFrame(rows)
    m["ts"] = pd.to_datetime(m["ts"])
    for c in POLLUTANTS:
        m[c] = pd.to_numeric(m.get(c), errors="coerce")
        m.loc[m[c] < 0, c] = None                       # ค่าติดลบ = รหัสข้อมูลหาย
    m = m.drop_duplicates(["station_id", "ts"]).sort_values(["station_id", "ts"])
    m["ts"] = m["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")

    stations.to_csv(a.out / "stations_sample.csv", index=False, encoding="utf-8")
    m[["station_id", "ts", *POLLUTANTS]].to_csv(a.out / "pm25_hourly_sample.csv", index=False, encoding="utf-8")
    print(f"เขียน {len(stations)} สถานี, {len(m):,} แถว, ช่วง {m.ts.min()} ถึง {m.ts.max()}")
    print(f"ข้ามเพราะ API ตอบไม่ถูกต้อง: {len(skipped)} รายการ", skipped[:5])


if __name__ == "__main__":
    main()
