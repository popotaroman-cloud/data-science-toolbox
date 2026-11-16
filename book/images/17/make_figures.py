"""สร้างรูปประกอบบทที่ 17 (ข้อมูลและพื้นที่สังเคราะห์ ไม่ใช่ข้อมูลหรือขอบเขตจริง)

รัน: python book/images/17/make_figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.colors import Normalize

OUT = Path(__file__).parent
THAI_FONTS = ["Sarabun", "Tahoma", "Leelawadee UI", "Noto Sans Thai", "Loma", "Garuda"]
RNG = np.random.default_rng(17)


def set_font() -> None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next((f for f in THAI_FONTS if f in available), "DejaVu Sans")
    plt.rcParams["axes.unicode_minus"] = False


def field(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """ค่าฝุ่นเฉลี่ยฤดูแล้งสมมุติ: สูงทางเหนือ มีแหล่งร้อนทางตะวันตกเฉียงเหนือและกลางพื้นที่"""
    return (18 + 0.03 * y + 30 * np.exp(-((x - 150) ** 2 + (y - 850) ** 2) / 2 / 120 ** 2)
            + 14 * np.exp(-((x - 420) ** 2 + (y - 380) ** 2) / 2 / 80 ** 2))


def maup() -> None:
    """ข้อมูลจุดชุดเดียวกัน รวมด้วยการแบ่งพื้นที่สองแบบ"""
    n = 400
    x, y = RNG.uniform(0, 600, n), RNG.uniform(0, 1000, n)
    v = field(x, y) + RNG.normal(0, 4, n)
    fig, axes = plt.subplots(1, 3, figsize=(16, 7), dpi=100)
    norm = Normalize(vmin=15, vmax=55)
    axes[0].scatter(x, y, c=v, cmap="YlOrRd", norm=norm, s=14)
    axes[0].set_title("ค่าที่จุดตรวจวัด")
    for ax, (nx, ny), title in [(axes[1], (2, 3), "รวมเป็น 6 เขต (2 × 3)"),
                                (axes[2], (3, 2), "รวมเป็น 6 เขต (3 × 2)")]:
        xe, ye = np.linspace(0, 600, nx + 1), np.linspace(0, 1000, ny + 1)
        for i in range(nx):
            for j in range(ny):
                inside = (x >= xe[i]) & (x < xe[i + 1]) & (y >= ye[j]) & (y < ye[j + 1])
                mean = v[inside].mean()
                ax.add_patch(plt.Rectangle((xe[i], ye[j]), xe[i + 1] - xe[i], ye[j + 1] - ye[j],
                                           color=plt.cm.YlOrRd(norm(mean)), ec="white", lw=3))
                ax.text((xe[i] + xe[i + 1]) / 2, (ye[j] + ye[j + 1]) / 2, f"{mean:.1f}",
                        ha="center", va="center", fontsize=13)
        ax.set_title(title)
    for ax in axes:
        ax.set(xlim=(0, 600), ylim=(0, 1000), aspect="equal", xticks=[], yticks=[])
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap="YlOrRd"), ax=axes, shrink=0.7,
                 label="PM2.5 เฉลี่ย (µg/m³)")
    fig.suptitle("MAUP: จุดชุดเดียวกัน การแบ่งเขตต่างกัน ให้ภาพต่างกัน", fontsize=14)
    fig.savefig(OUT / "maup.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def idw_surface() -> None:
    """พื้นผิวจาก IDW เทียบกับพื้นผิวจริงที่สมมุติ"""
    n = 30
    x, y = RNG.uniform(0, 600, n), RNG.uniform(0, 1000, n)
    v = field(x, y) + RNG.normal(0, 2, n)
    gx, gy = np.meshgrid(np.linspace(0, 600, 120), np.linspace(0, 1000, 200))
    truth = field(gx, gy)
    d = np.sqrt((gx[..., None] - x) ** 2 + (gy[..., None] - y) ** 2)
    w = 1 / np.maximum(d, 1e-9) ** 2
    est = (w * v).sum(axis=-1) / w.sum(axis=-1)
    norm = Normalize(vmin=15, vmax=55)
    fig, axes = plt.subplots(1, 2, figsize=(12, 9), dpi=100)
    for ax, surface, title in [(axes[0], truth, "พื้นผิวจริง (สมมุติ)"),
                               (axes[1], est, f"ประมาณด้วย IDW จาก {n} สถานี (power = 2)")]:
        ax.imshow(surface, origin="lower", extent=(0, 600, 0, 1000), cmap="YlOrRd", norm=norm)
        ax.scatter(x, y, c="black", s=12)
        ax.set(title=title, xticks=[], yticks=[])
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap="YlOrRd"), ax=axes, shrink=0.6,
                 label="PM2.5 เฉลี่ย (µg/m³)")
    fig.savefig(OUT / "idw.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    set_font()
    maup()
    idw_surface()
