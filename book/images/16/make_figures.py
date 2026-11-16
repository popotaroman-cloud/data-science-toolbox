"""สร้างรูปประกอบบทที่ 16 (ข้อมูลสังเคราะห์ ไม่ใช่ข้อมูล Air4Thai จริง)

รัน: python book/images/16/make_figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from scipy import stats

OUT = Path(__file__).parent
THAI_FONTS = ["Sarabun", "Tahoma", "Leelawadee UI", "Noto Sans Thai", "Loma", "Garuda"]
RNG = np.random.default_rng(16)


def set_font() -> None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next((f for f in THAI_FONTS if f in available), "DejaVu Sans")
    plt.rcParams["axes.unicode_minus"] = False


def original_data(n: int = 1400) -> pd.DataFrame:
    """ค่าเฉลี่ยและค่าสูงสุดรายวันของสถานีหนึ่ง (สร้างขึ้นเพื่อเป็นตัวแทนข้อมูลต้นฉบับ)"""
    mean = np.exp(RNG.normal(3.05, 0.45, n))
    ratio = np.exp(RNG.normal(0.5, 0.12, n))
    return pd.DataFrame({"pm25_mean": mean.round(1), "pm25_max": (mean * ratio).round(1)})


def gaussian_copula(df: pd.DataFrame, n: int) -> pd.DataFrame:
    u = df.rank(method="average") / (len(df) + 1)
    corr = np.corrcoef(stats.norm.ppf(u), rowvar=False)
    us = stats.norm.cdf(RNG.multivariate_normal(np.zeros(df.shape[1]), corr, size=n))
    return pd.DataFrame({c: np.quantile(df[c], us[:, j]) for j, c in enumerate(df.columns)})


def real_vs_synthetic() -> None:
    real = original_data()
    syn = gaussian_copula(real, len(real))
    fig, axes = plt.subplots(1, 2, figsize=(16, 5.5), dpi=100, sharex=True, sharey=True)
    for ax, data, title in [(axes[0], real, "ข้อมูลต้นฉบับ"), (axes[1], syn, "ข้อมูลสังเคราะห์จาก Gaussian copula")]:
        ax.scatter(data["pm25_mean"], data["pm25_max"], s=8, alpha=0.5, color="0.3")
        ax.axvline(real["pm25_mean"].max(), color="tab:red", linestyle="--", lw=1)
        ax.set(title=title, xlabel="PM2.5 เฉลี่ยรายวัน (µg/m³)")
    axes[0].set_ylabel("PM2.5 สูงสุดรายชั่วโมง (µg/m³)")
    axes[1].text(real["pm25_mean"].max(), 5, "ค่าสูงสุดของต้นฉบับ ", color="tab:red", va="bottom", ha="right")
    fig.suptitle("ข้อมูลสังเคราะห์รักษารูปร่างโดยรวม แต่ไม่สร้างค่าที่สุดโต่งกว่าข้อมูลต้นฉบับ", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "real_vs_synthetic.png", dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    set_font()
    real_vs_synthetic()
