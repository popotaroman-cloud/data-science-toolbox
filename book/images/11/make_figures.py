"""สร้างรูปประกอบบทที่ 11 (รันจากโฟลเดอร์ book/: python images/11/make_figures.py)

รูปในบทนี้เป็นภาพแนวคิดที่ใช้ตัวเลขสมมุติ ไม่ได้ใช้ข้อมูล PM2.5 จริง
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

OUT = Path(__file__).resolve().parent
THAI_CANDIDATES = ["Sarabun", "Tahoma", "Leelawadee UI", "Noto Sans Thai", "Loma", "Garuda"]
available = {f.name for f in font_manager.fontManager.ttflist}
THAI_FONT = next((f for f in THAI_CANDIDATES if f in available), None)
if THAI_FONT:
    plt.rcParams["font.family"] = THAI_FONT
plt.rcParams["axes.unicode_minus"] = False
DPI = 200            # figsize กว้าง 8 นิ้ว × 200 dpi = 1600 px


def pie_vs_bar():
    labels = ["ก", "ข", "ค", "ง", "จ"]
    values = [23, 21, 20, 19, 17]               # ตัวเลขสมมุติ ต่างกันเล็กน้อย
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8, 3.6))
    a1.pie(values, labels=labels, startangle=90, counterclock=False,
           colors=plt.cm.Greys(np.linspace(0.25, 0.75, 5)))
    a1.set_title("มุม (pie chart)")
    a2.bar(labels, values, color="0.45")
    a2.set_ylim(0, 25)
    a2.set_title("ความยาวบนแกนร่วม (bar chart)")
    a2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "pie_vs_bar.png", dpi=DPI)
    plt.close(fig)


def relative_luminance(rgb):
    def lin(c):
        return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = lin(rgb[:, 0]), lin(rgb[:, 1]), lin(rgb[:, 2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def colormap_lightness():
    x = np.linspace(0, 1, 256)
    fig, axes = plt.subplots(2, 2, figsize=(8, 3.6),
                             gridspec_kw={"height_ratios": [1, 3]})
    for col, name in enumerate(["jet", "viridis"]):
        cmap = plt.get_cmap(name)
        axes[0, col].imshow(x[None, :], aspect="auto", cmap=cmap)
        axes[0, col].set_axis_off()
        axes[0, col].set_title(name)
        lum = relative_luminance(cmap(x)[:, :3])
        axes[1, col].plot(x, lum, color="black")
        axes[1, col].set_ylim(0, 1)
        axes[1, col].set_xlabel("ตำแหน่งในชุดสี (ค่าข้อมูล)")
        axes[1, col].set_ylabel("ความสว่างสัมพัทธ์")
    fig.tight_layout()
    fig.savefig(OUT / "colormap_lightness.png", dpi=DPI)
    plt.close(fig)


def truncated_axis():
    names, vals = ["เมือง ก", "เมือง ข"], [35, 45]       # ตัวเลขสมมุติ
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8, 3.6))
    for ax, bottom, title in [(a1, 30, "แกนเริ่มที่ 30: ข ดูสูงกว่า ก สามเท่า"),
                              (a2, 0, "แกนเริ่มที่ 0: ข สูงกว่า ก ประมาณ 29%")]:
        ax.bar(names, vals, color="0.45")
        ax.set_ylim(bottom, 50)
        ax.set_ylabel("PM2.5 (µg/m³)")
        ax.set_title(title, fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "truncated_axis.png", dpi=DPI)
    plt.close(fig)


def thai_font_demo():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8, 2.6))
    for ax, family, title in [(a1, "DejaVu Sans", "ฟอนต์เริ่มต้น (DejaVu Sans)"),
                              (a2, THAI_FONT or "DejaVu Sans", f"ฟอนต์ที่มีอักษรไทย ({THAI_FONT})")]:
        ax.bar(["ภาคเหนือ", "ภาคกลาง"], [3, 2], color="0.6")
        for lab in ax.get_xticklabels():
            lab.set_fontfamily(family)
        ax.set_title(title, fontsize=10)
        ax.set_yticks([])
        ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "thai_font.png", dpi=DPI)
    plt.close(fig)


if __name__ == "__main__":
    pie_vs_bar()
    colormap_lightness()
    truncated_axis()
    thai_font_demo()
    print("ใช้ฟอนต์:", THAI_FONT)
