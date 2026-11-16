"""สร้างรูปประกอบบทที่ 13 (ข้อมูลสังเคราะห์ ไม่ใช่ข้อมูล Air4Thai จริง)

รัน: python book/images/13/make_figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

OUT = Path(__file__).parent
THAI_FONTS = ["Sarabun", "Tahoma", "Leelawadee UI", "Noto Sans Thai", "Loma", "Garuda"]
RNG = np.random.default_rng(2026)


def set_font() -> None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next((f for f in THAI_FONTS if f in available), "DejaVu Sans")
    plt.rcParams["axes.unicode_minus"] = False


def skew_and_log() -> None:
    """การแจกแจงเบ้ขวาของค่าเฉลี่ยรายวัน และเมื่อแปลงด้วย log"""
    x = np.exp(RNG.normal(3.1, 0.5, 8000))
    fig, axes = plt.subplots(1, 2, figsize=(16, 5), dpi=100)
    axes[0].hist(x, bins=80, color="0.45")
    for value, label, style in [(np.mean(x), "ค่าเฉลี่ย", "-"), (np.median(x), "มัธยฐาน", "--")]:
        axes[0].axvline(value, color="tab:orange", linestyle=style, lw=2, label=f"{label} {value:.1f}")
    axes[0].legend()
    axes[0].set(title="สเกลเดิม: เบ้ขวา ค่าเฉลี่ยมากกว่ามัธยฐาน",
                xlabel="PM2.5 เฉลี่ยรายวัน (µg/m³)", ylabel="จำนวนสถานี-วัน")
    axes[1].hist(np.log(x), bins=80, color="0.45")
    axes[1].set(title="หลังแปลงด้วย log: ใกล้สมมาตร",
                xlabel="log(PM2.5 เฉลี่ยรายวัน)", ylabel="จำนวนสถานี-วัน")
    fig.tight_layout()
    fig.savefig(OUT / "skew_log.png", dpi=100)
    plt.close(fig)


def bootstrap_distribution() -> None:
    """การแจกแจง bootstrap ของผลต่างมัธยฐานระหว่างสองกลุ่ม"""
    a = RNG.normal(44, 2, 12)
    b = RNG.normal(33, 1.2, 8)
    boots = np.array([
        np.median(RNG.choice(a, a.size)) - np.median(RNG.choice(b, b.size)) for _ in range(9999)
    ])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    fig, ax = plt.subplots(figsize=(16, 5), dpi=100)
    ax.hist(boots, bins=60, color="0.6")
    ax.axvspan(lo, hi, color="tab:blue", alpha=0.15, label=f"ช่วง percentile 95%: {lo:.1f} ถึง {hi:.1f}")
    ax.axvline(np.median(a) - np.median(b), color="black", lw=2, label="ผลต่างจากตัวอย่างจริง")
    ax.legend(loc="upper left")
    ax.set(title="การแจกแจง bootstrap ของผลต่างมัธยฐาน (สุ่มซ้ำ 9,999 ครั้ง)",
           xlabel="ผลต่างมัธยฐาน (µg/m³)", ylabel="จำนวนครั้ง")
    fig.tight_layout()
    fig.savefig(OUT / "bootstrap.png", dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    set_font()
    skew_and_log()
    bootstrap_distribution()
