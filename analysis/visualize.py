"""可视化：价格带分布、平台箱线图、价格-销量散点、核心价格带柱状图。"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import FIG_DIR

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

CATEGORY_COLORS = {"polo衫": "#1f77b4", "牛仔裤": "#d62728"}


def _save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path}")


def plot_price_distribution(df):
    """价格带直方图（分品类）。"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, (cat, sub) in zip(axes, df.groupby("category", observed=True)):
        ax.hist(sub["price"], bins=20, color=CATEGORY_COLORS[cat], alpha=0.75,
                edgecolor="white")
        ax.axvline(sub["price"].median(), color="black", linestyle="--", lw=1)
        ax.set_title(f"{cat} 价格分布（中位数 {sub['price'].median():.0f} 元）")
        ax.set_xlabel("价格（元）")
        ax.set_ylabel("SKU 数量")
    fig.suptitle("价格带分布", fontsize=14, y=1.02)
    _save(fig, "01_price_distribution.png")


def plot_platform_boxplot(df):
    """各平台价格箱线图。"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, (cat, sub) in zip(axes, df.groupby("category", observed=True)):
        sub.boxplot(column="price", by="platform", ax=ax, patch_artist=True)
        ax.set_title(f"{cat} 分平台价格")
        ax.set_xlabel("平台")
        ax.set_ylabel("价格（元）")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    fig.suptitle("各平台价格水平对比", fontsize=14, y=1.02)
    _save(fig, "02_platform_price_boxplot.png")


def plot_price_sales(df):
    """价格-销量散点（log 销量）与趋势线。"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, (cat, sub) in zip(axes, df.groupby("category", observed=True)):
        x, y = sub["price"], sub["log_sales"]
        ax.scatter(x, y, s=22, alpha=0.55, color=CATEGORY_COLORS[cat])
        k, b = np.polyfit(x, y, 1)
        ax.plot(np.sort(x), k * np.sort(x) + b, color="black", lw=1.5)
        ax.set_title(f"{cat}：价格 vs 销量（Pearson {x.corr(y):.2f}）")
        ax.set_xlabel("价格（元）")
        ax.set_ylabel("销量 log10(件)")
    fig.suptitle("价格与销量关系", fontsize=14, y=1.02)
    _save(fig, "03_price_sales_scatter.png")


def plot_core_band(band_df):
    """核心价格带：各价格带总销量柱状图（标注核心带）。"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
    for ax, (cat, sub) in zip(axes, band_df.groupby("category", observed=True)):
        sub = sub.sort_values("price_band")
        colors = [CATEGORY_COLORS[cat]] * len(sub)
        top_idx = sub["total_sales"].idxmax()
        top_pos = list(sub["price_band"]).index(sub.loc[top_idx, "price_band"])
        colors[top_pos] = "#ff7f0e"
        ax.bar(sub["price_band"], sub["total_sales"], color=colors, alpha=0.85)
        ax.set_title(f"{cat} 各价格带销量（橙色=核心带）")
        ax.set_xlabel("价格带（元）")
        ax.set_ylabel("总销量（件）")
        ax.tick_params(axis="x", rotation=60)
    fig.suptitle("核心价格带识别", fontsize=14, y=1.02)
    _save(fig, "04_core_price_band.png")


def plot_all(df, band_df):
    plot_price_distribution(df)
    plot_platform_boxplot(df)
    plot_price_sales(df)
    plot_core_band(band_df)
    print("图表已输出到 output/figures/")


if __name__ == "__main__":
    import pandas as pd
    from config import PROCESSED_DIR
    from analysis.analyze import price_band_distribution

    df = pd.read_csv(os.path.join(PROCESSED_DIR, "products_clean.csv"))
    plot_all(df, price_band_distribution(df))
