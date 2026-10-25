"""สร้างรูปประกอบบทที่ 18: เปรียบเทียบอัลกอริทึมจัดวาง treemap (ตัวเลขสมมุติ)

ต้องติดตั้ง squarify: pip install squarify
รัน: python book/images/18/make_figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import squarify
from matplotlib import font_manager

OUT = Path(__file__).parent
THAI_FONTS = ["Sarabun", "Tahoma", "Leelawadee UI", "Noto Sans Thai", "Loma", "Garuda"]
# จำนวนสถานี-วันสมมุติของ 10 จังหวัด เรียงจากมากไปน้อย
VALUES = [10700, 5600, 4100, 2800, 2700, 1400, 1350, 1300, 700, 650]
LABELS = [f"จ.{i + 1}" for i in range(len(VALUES))]


def set_font() -> None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next((f for f in THAI_FONTS if f in available), "DejaVu Sans")
    plt.rcParams["axes.unicode_minus"] = False


def slice_and_dice(values: list[float], x: float, y: float, w: float, h: float) -> list[dict]:
    """แบ่งสี่เหลี่ยมตามแนวนอนครั้งเดียว (ระดับเดียวของ slice-and-dice)"""
    total = sum(values)
    rects, cx = [], x
    for v in values:
        dx = w * v / total
        rects.append({"x": cx, "y": y, "dx": dx, "dy": h})
        cx += dx
    return rects


def aspect(r: dict) -> float:
    return max(r["dx"] / r["dy"], r["dy"] / r["dx"])


def layouts() -> None:
    w, h = 160, 100
    norm = squarify.normalize_sizes(VALUES, w, h)
    layouts_ = [("slice-and-dice", slice_and_dice(norm, 0, 0, w, h)),
                ("squarified", squarify.squarify(norm, 0, 0, w, h))]
    fig, axes = plt.subplots(1, 2, figsize=(16, 5.6), dpi=100)
    colors = plt.cm.tab10(np.arange(len(VALUES)))
    for ax, (name, rects) in zip(axes, layouts_):
        for r, label, c in zip(rects, LABELS, colors):
            ax.add_patch(plt.Rectangle((r["x"], r["y"]), r["dx"], r["dy"], fc=c, ec="white", lw=2, alpha=0.85))
            if r["dx"] > 9 and r["dy"] > 9:
                ax.text(r["x"] + r["dx"] / 2, r["y"] + r["dy"] / 2, label, ha="center", va="center",
                        fontsize=11, color="white")
        mean_aspect = np.mean([aspect(r) for r in rects])
        ax.set(xlim=(0, w), ylim=(0, h), aspect="equal", xticks=[], yticks=[],
               title=f"{name} (อัตราส่วนด้านเฉลี่ย {mean_aspect:.1f})")
    fig.suptitle("ข้อมูลชุดเดียวกัน จัดวางด้วยอัลกอริทึมต่างกัน (ตัวเลขสมมุติ)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "treemap_layouts.png", dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    set_font()
    layouts()
