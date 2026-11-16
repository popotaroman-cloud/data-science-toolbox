"""สร้างรูปประกอบบทที่ 15 (ข้อมูลสังเคราะห์ ไม่ใช่ข้อมูล Air4Thai จริง)

สร้างโปรไฟล์รายเดือนของ 50 สถานีสังเคราะห์จากรูปแบบฤดูกาลหกแบบ แล้ววาดรูปของ PCA,
k-means และ t-SNE
รัน: python book/images/15/make_figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

OUT = Path(__file__).parent
THAI_FONTS = ["Sarabun", "Tahoma", "Leelawadee UI", "Noto Sans Thai", "Loma", "Garuda"]
RNG = np.random.default_rng(7)
MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def set_font() -> None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next((f for f in THAI_FONTS if f in available), "DejaVu Sans")
    plt.rcParams["axes.unicode_minus"] = False


def synthetic_profiles() -> tuple[pd.DataFrame, pd.Series]:
    """โปรไฟล์ค่าเฉลี่ยรายเดือน (µg/m³) ของสถานีสังเคราะห์ พร้อมภาค"""
    month_mid = np.arange(12) * 30.4 + 15

    def bump(center: float, width: float) -> np.ndarray:
        return np.exp(-((((month_mid - center) + 182) % 365 - 182) / width) ** 2)

    patterns = {  # ภาค (ระบบ 4 ภาค), ระดับพื้นฐาน, ฤดูกาล, จำนวนสถานี
        "เหนือ": ("เหนือ", 22, 45 * bump(80, 28), 15),
        "อีสาน": ("ตะวันออกเฉียงเหนือ", 22, 22 * bump(45, 35), 7),
        "กลาง": ("กลาง", 24, 18 * bump(25, 40), 15),
        "ตะวันออก": ("กลาง", 18, 12 * bump(25, 40), 5),
        "ตะวันตก": ("กลาง", 20, 22 * bump(60, 35), 2),
        "ใต้": ("ใต้", 12, 6 * bump(260, 25), 6),
    }
    rows, regions = [], []
    for region, base, seasonal, n in patterns.values():
        for _ in range(n):
            level = base * np.exp(RNG.normal(0, 0.12))
            amp = np.exp(RNG.normal(0, 0.2))
            rows.append(level + amp * seasonal + RNG.normal(0, 1.2, 12))
            regions.append(region)
    profile = pd.DataFrame(rows, columns=[f"m{m:02d}" for m in range(1, 13)])
    return profile, pd.Series(regions, name="region")


def pca_loadings(profile: pd.DataFrame) -> None:
    X = StandardScaler().fit_transform(profile)
    pca = PCA(n_components=2).fit(X)
    fig, ax = plt.subplots(figsize=(16, 5), dpi=100)
    for i, style in enumerate(["-o", "--s"]):
        ax.plot(MONTHS, pca.components_[i], style, lw=2,
                label=f"PC{i + 1} ({pca.explained_variance_ratio_[i]:.0%} ของความแปรปรวน)")
    ax.axhline(0, color="0.6", lw=1)
    ax.set(ylabel="loading", title="loading ของ PC1 และ PC2 จากโปรไฟล์รายเดือนที่ปรับสเกลแล้ว")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "pca_loadings.png", dpi=100)
    plt.close(fig)


def cluster_profiles(profile: pd.DataFrame) -> None:
    X = StandardScaler().fit_transform(profile)
    labels = KMeans(n_clusters=4, n_init=10, random_state=42).fit_predict(X)
    fig, ax = plt.subplots(figsize=(16, 5), dpi=100)
    for k in range(4):
        members = profile[labels == k]
        for _, row in members.iterrows():
            ax.plot(MONTHS, row.to_numpy(), color=f"C{k}", alpha=0.15, lw=1)
        ax.plot(MONTHS, members.mean().to_numpy(), color=f"C{k}", lw=3,
                label=f"กลุ่ม {k} ({len(members)} สถานี)")
    ax.axhline(37.5, color="black", linestyle="--", lw=1, label="มาตรฐาน 37.5 µg/m³")
    ax.set(ylabel="PM2.5 เฉลี่ยรายเดือน (µg/m³)",
           title="โปรไฟล์รายเดือนของสถานีแต่ละกลุ่มจาก k-means (k = 4) เส้นหนาคือค่าเฉลี่ยของกลุ่ม")
    ax.legend(ncol=5, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT / "cluster_profiles.png", dpi=100)
    plt.close(fig)


def tsne_perplexity(profile: pd.DataFrame, regions: pd.Series) -> None:
    X = StandardScaler().fit_transform(profile)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=100)
    for ax, perplexity in zip(axes, [3, 10, 30]):
        emb = TSNE(perplexity=perplexity, random_state=0, init="pca").fit_transform(X)
        for j, region in enumerate(regions.unique()):
            mask = (regions == region).to_numpy()
            ax.scatter(emb[mask, 0], emb[mask, 1], s=30, color=f"C{j}", label=region)
        ax.set(title=f"t-SNE perplexity = {perplexity}", xticks=[], yticks=[])
    axes[0].legend(loc="best", fontsize=9)
    fig.suptitle("ข้อมูลชุดเดียวกัน ค่า perplexity ต่างกัน ให้ภาพต่างกัน", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "tsne_perplexity.png", dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    set_font()
    profiles, region_labels = synthetic_profiles()
    pca_loadings(profiles)
    cluster_profiles(profiles)
    tsne_perplexity(profiles, region_labels)
