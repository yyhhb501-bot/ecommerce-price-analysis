"""分析模块：价格带分布、价格-销量相关性、核心价格带与定价建议。"""
import json
import os

import numpy as np
import pandas as pd

from config import PROCESSED_DIR

OUT_JSON = os.path.join(PROCESSED_DIR, "analysis_result.json")


def summarize(df):
    """按品类 × 平台的基础统计。"""
    g = df.groupby(["category", "platform"], observed=True).agg(
        sku_count=("price", "count"),
        min_price=("price", "min"),
        median_price=("price", "median"),
        max_price=("price", "max"),
        mean_sales=("sales", "mean"),
        total_sales=("sales", "sum"),
    ).round(1)
    return g


def price_band_distribution(df):
    """价格带分布：每个价格带的 SKU 数、平均销量、总销量。"""
    band = (
        df.groupby(["category", "price_band"], observed=True)
        .agg(sku_count=("price", "count"), total_sales=("sales", "sum"),
             mean_sales=("sales", "mean"))
        .reset_index()
    )
    return band


def price_sales_correlation(df):
    """价格与销量（log）的 Pearson / Spearman 相关系数。"""
    out = {}
    for category, sub in df.groupby("category", observed=True):
        x, y = sub["price"], sub["log_sales"]
        # Spearman = 秩的 Pearson 相关，避免额外依赖 scipy
        spearman = x.rank().corr(y.rank())
        out[category] = {
            "pearson": round(x.corr(y), 3),
            "spearman": round(float(spearman), 3),
            "n": int(len(sub)),
        }
    return out


def core_price_band(df):
    """核心价格带：按总销量占比确定（累计销量贡献最大、SKU 最密集的价格带）。"""
    result = {}
    for category, sub in df.groupby("category", observed=True):
        band = sub.groupby("price_band", observed=True).agg(
            sku_count=("price", "count"),
            total_sales=("sales", "sum"),
            mean_sales=("sales", "mean"),
        ).reset_index().sort_values("total_sales", ascending=False)

        total = band["total_sales"].sum()
        band["sales_share"] = (band["total_sales"] / total * 100).round(1)
        top = band.iloc[0]

        result[category] = {
            "core_band": top["price_band"],
            "core_band_sales_share": top["sales_share"],
            "core_band_mean_sales": round(top["mean_sales"], 0),
            "core_band_sku_count": int(top["sku_count"]),
            "band_detail": band.to_dict("records"),
        }
    return result


def recommend_pricing(df, core):
    """形成可执行定价建议：引流款(P25) / 主推款(中位数) / 利润款(P75)。"""
    recs = {}
    for category, sub in df.groupby("category", observed=True):
        q25 = int(round(sub["price"].quantile(0.25)))
        q50 = int(round(sub["price"].quantile(0.50)))
        q75 = int(round(sub["price"].quantile(0.75)))

        recs[category] = {
            "引流款建议价": q25,
            "主推款建议价": q50,
            "利润款建议价": q75,
            "参考区间": f"{q25}–{q75} 元",
        }
    return recs


def main(df):
    summary = summarize(df)
    band = price_band_distribution(df)
    corr = price_sales_correlation(df)
    core = core_price_band(df)
    recs = recommend_pricing(df, core)

    result = {
        "summary": summary.reset_index().to_dict("records"),
        "price_band": band.to_dict("records"),
        "correlation": corr,
        "core_price_band": {k: v for k, v in core.items()},
        "recommendations": recs,
    }
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    print("=== 价格-销量相关性 ===")
    for k, v in corr.items():
        print(f"{k}: Pearson={v['pearson']} Spearman={v['spearman']} (n={v['n']})")
    print("\n=== 定价建议 ===")
    for k, v in recs.items():
        print(f"{k}: {v}")
    print(f"\n结果已写入 {OUT_JSON}")
    return result


if __name__ == "__main__":
    from analysis.clean import main as clean_main
    main(clean_main())
