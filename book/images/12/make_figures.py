"""สร้างรูปประกอบบทที่ 12 (ข้อมูลสังเคราะห์ ไม่ใช่ข้อมูล Air4Thai จริง)

รัน: python book/images/12/make_figures.py
"""
from pathlib import Path

import datashader as ds
import datashader.transfer_functions as tf
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

OUT = Path(__file__).parent
THAI_FONTS = ["Sarabun", "Tahoma", "Leelawadee UI", "Noto Sans Thai", "Loma", "Garuda"]


def set_font() -> None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    font = next((f for f in THAI_FONTS if f in available), "DejaVu Sans")
    plt.rcParams["font.family"] = font
    plt.rcParams["axes.unicode_minus"] = False


def synthetic_hourly(n: int = 400_000, seed: int = 2026) -> tuple[np.ndarray, np.ndarray]:
    """ค่ารายชั่วโมงสังเคราะห์: x = PM2.5, y = PM10 ที่สัมพันธ์กันแบบ log-normal"""
    rng = np.random.default_rng(seed)
    log_pm25 = rng.normal(3.0, 0.55, n)
    pm25 = np.exp(log_pm25)
    pm10 = np.exp(np.log(pm25) * 0.95 + 0.45 + rng.normal(0, 0.18, n))
    return pm25, pm10


def overplotting() -> None:
    x, y = synthetic_hourly()
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2), dpi=100)
    axes[0].scatter(x, y, s=4, color="tab:blue")
    axes[0].set_title("scatter ทึบ 400,000 จุด")
    axes[1].scatter(x, y, s=1, alpha=0.02, color="tab:blue")
    axes[1].set_title("ลดความทึบ (alpha = 0.02)")
    cvs = ds.Canvas(plot_width=500, plot_height=400, x_range=(0, 150), y_range=(0, 220))
    agg = cvs.points(_frame(x, y), "x", "y")
    img = tf.shade(agg, cmap=["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"], how="log").to_pil()
    axes[2].imshow(img, extent=(0, 150, 0, 220), aspect="auto", origin="upper")
    axes[2].set_title("Datashader (นับจุดต่อพิกเซล สเกล log)")
    for ax in axes:
        ax.set(xlim=(0, 150), ylim=(0, 220), xlabel="PM2.5 (µg/m³)", ylabel="PM10 (µg/m³)")
    fig.suptitle("ข้อมูลสังเคราะห์ชุดเดียวกันแสดงสามแบบ", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "overplotting.png", dpi=100)
    plt.close(fig)


def _frame(x: np.ndarray, y: np.ndarray):
    import pandas as pd

    return pd.DataFrame({"x": x, "y": y})


if __name__ == "__main__":
    set_font()
    overplotting()
