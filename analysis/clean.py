"""数据清洗入库：合并爬虫结果与备用数据，统一口径，落盘 CSV + SQLite。"""
import glob
import json
import os
import sqlite3

import numpy as np
import pandas as pd

from config import RAW_DIR, PROCESSED_DIR, DB_PATH


def load_crawled_items():
    """从 data/raw/*.json 汇总真实抓取到的商品（不含 crawl_report.json）。"""
    items = []
    for f in glob.glob(os.path.join(RAW_DIR, "*.json")):
        if f.endswith("crawl_report.json"):
            continue
        with open(f, encoding="utf-8") as fp:
            report = json.load(fp)
        for it in report.get("items", []):
            it = dict(it)
            it["data_source"] = "crawled"
            items.append(it)
    return items


def load_reference_items():
    ref_csv = os.path.join(RAW_DIR, "reference_data.csv")
    if not os.path.exists(ref_csv):
        return []
    return pd.read_csv(ref_csv).to_dict("records")


def clean(df):
    """统一数值口径并剔除异常。"""
    for col in ("price", "original_price", "sales", "comments"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["price"].notna() & (df["price"] > 0)].copy()
    # 价格极端异常裁剪（1% / 99% 分位）
    lo, hi = df["price"].quantile([0.01, 0.99])
    df = df[(df["price"] >= lo) & (df["price"] <= hi)].copy()

    df["sales"] = df["sales"].fillna(0).astype(int)
    df["comments"] = df["comments"].fillna(0).astype(int)
    df["original_price"] = df["original_price"].fillna(df["price"])
    df["log_sales"] = np.log10(df["sales"].clip(lower=1))

    # 价格带分箱（20 元一档）
    bins = list(range(0, 420, 20))
    labels = [f"{b}-{b + 19}" for b in bins[:-1]]
    df["price_band"] = pd.cut(
        df["price"], bins=bins, labels=labels, include_lowest=True
    ).astype(str)
    return df


def main():
    rows = load_reference_items() + load_crawled_items()
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("无任何数据，请先运行 generate_reference_data")

    df = clean(df)
    df = df.drop_duplicates(subset=["title", "platform", "price"], keep="first")

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    csv_path = os.path.join(PROCESSED_DIR, "products_clean.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    con = sqlite3.connect(DB_PATH)
    df.to_sql("products", con, if_exists="replace", index=False)
    con.close()

    print(f"清洗完成: {len(df)} 条 SKU")
    print(f"  CSV  -> {csv_path}")
    print(f"  DB   -> {DB_PATH}")
    print("数据来源分布:\n", df["data_source"].value_counts().to_string())
    return df


if __name__ == "__main__":
    main()
