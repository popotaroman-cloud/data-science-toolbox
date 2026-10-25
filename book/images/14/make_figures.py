"""สร้างรูปประกอบบทที่ 14 (ข้อมูลสังเคราะห์ ไม่ใช่ข้อมูล Air4Thai จริง)

รัน: python book/images/14/make_figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.nonparametric.smoothers_lowess import lowess
from statsmodels.tsa.seasonal import STL

OUT = Path(__file__).parent
THAI_FONTS = ["Sarabun", "Tahoma", "Leelawadee UI", "Noto Sans Thai", "Loma", "Garuda"]


def set_font() -> None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next((f for f in THAI_FONTS if f in available), "DejaVu Sans")
    plt.rcParams["axes.unicode_minus"] = False


def synthetic_daily(seed: int = 2026) -> pd.Series:
    """ค่าเฉลี่ยรายวันสังเคราะห์ของสถานีภาคเหนือ: ฤดูกาลรายปี + AR(1) ในสเกล log"""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", "2023-12-31", freq="D")
    doy = idx.dayofyear.to_numpy()
    seasonal = 0.55 * np.exp(-0.5 * ((doy - 75) / 28) ** 2) - 0.12
    noise = np.zeros(len(idx))
    for t in range(1, len(idx)):
        noise[t] = 0.75 * noise[t - 1] + rng.normal(0, 0.16)
    return pd.Series(np.exp(3.05 + seasonal + noise), index=idx, name="pm25_mean")


def stl_figure(s: pd.Series) -> None:
    monthly = np.log(s.resample("MS").mean())
    res = STL(monthly, period=12, robust=True).fit()
    parts = [("ข้อมูล (log)", monthly), ("แนวโน้ม", res.trend),
             ("ฤดูกาล", res.seasonal), ("ส่วนเหลือ", res.resid)]
    fig, axes = plt.subplots(4, 1, figsize=(16, 9), dpi=100, sharex=True)
    for ax, (label, series) in zip(axes, parts):
        ax.plot(series.index, series.to_numpy(), color="0.25", marker="o" if label == "ส่วนเหลือ" else None,
                lw=1.4, ms=3)
        ax.set_ylabel(label)
    axes[0].set_title("STL ของค่าเฉลี่ยรายเดือน (สเกล log) สถานีสังเคราะห์ ค.ศ. 2020–2023")
    fig.tight_layout()
    fig.savefig(OUT / "stl.png", dpi=100)
    plt.close(fig)


def acf_figure(s: pd.Series) -> None:
    x = np.log(s)
    fig, axes = plt.subplots(1, 2, figsize=(16, 4.8), dpi=100)
    plot_acf(x, lags=40, ax=axes[0], title="ACF ของ log(ค่าเฉลี่ยรายวัน)")
    plot_pacf(x, lags=40, ax=axes[1], method="ywm", title="PACF ของ log(ค่าเฉลี่ยรายวัน)")
    for ax in axes:
        ax.set_xlabel("lag (วัน)")
    fig.tight_layout()
    fig.savefig(OUT / "acf_pacf.png", dpi=100)
    plt.close(fig)


def smoothing_figure(s: pd.Series) -> None:
    year = s["2023"]
    ma7 = year.rolling(7, center=True, min_periods=5).mean()
    ma30 = year.rolling(30, center=True, min_periods=20).mean()
    lo = lowess(year.to_numpy(), np.arange(len(year)), frac=0.08, return_sorted=False)
    fig, ax = plt.subplots(figsize=(16, 5), dpi=100)
    ax.plot(year.index, year.to_numpy(), color="0.75", lw=0.8, label="ค่ารายวัน")
    ax.plot(ma7.index, ma7.to_numpy(), color="tab:blue", lw=1.6, label="moving average 7 วัน")
    ax.plot(ma30.index, ma30.to_numpy(), color="tab:orange", lw=1.6, label="moving average 30 วัน")
    ax.plot(year.index, lo, color="black", lw=2, linestyle="--", label="LOESS (frac = 0.08)")
    ax.axhline(37.5, color="tab:red", lw=1, linestyle=":", label="มาตรฐาน 37.5 µg/m³")
    ax.set(ylabel="PM2.5 เฉลี่ยรายวัน (µg/m³)", title="การทำให้เรียบแบบต่าง ๆ ของข้อมูลสังเคราะห์หนึ่งปี")
    ax.legend(ncol=3, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT / "smoothing.png", dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    set_font()
    series = synthetic_daily()
    stl_figure(series)
    acf_figure(series)
    smoothing_figure(series)
