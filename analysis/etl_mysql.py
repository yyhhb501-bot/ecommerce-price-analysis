"""ETL：将清洗后的数据与分析结果写入 MySQL（表结构见 sql/01_create_schema.sql）。"""
import os

import pandas as pd
from sqlalchemy import create_engine

from config import MYSQL, PROCESSED_DIR


def _engine():
    url = (
        f"mysql+pymysql://{MYSQL['user']}:{MYSQL['password']}@"
        f"{MYSQL['host']}:{MYSQL['port']}/{MYSQL['database']}?charset={MYSQL['charset']}"
    )
    return create_engine(url)


def load_products(df):
    engine = _engine()
    df = df.copy()
    df = df[["sku_id", "platform", "category", "title", "brand", "price",
             "original_price", "sales", "sales_unit", "comments", "shop_name",
             "data_source", "crawl_time", "price_band", "log_sales"]]
    df.to_sql("products", engine, if_exists="replace", index=False)
    print(f"products 表已写入 {len(df)} 行")


def load_aggregates(df):
    engine = _engine()

    summary = (
        df.groupby(["category", "platform"], observed=True)
        .agg(sku_count=("price", "count"), min_price=("price", "min"),
             median_price=("price", "median"), max_price=("price", "max"),
             mean_sales=("sales", "mean"), total_sales=("sales", "sum"))
        .reset_index()
    )
    summary["mean_sales"] = summary["mean_sales"].round(2)
    summary.to_sql("platform_summary", engine, if_exists="replace", index=False)

    total_by_cat = df.groupby("category", observed=True)["sales"].sum()
    band = (
        df.groupby(["category", "price_band"], observed=True)
        .agg(sku_count=("price", "count"), total_sales=("sales", "sum"),
             mean_sales=("sales", "mean"))
        .reset_index()
    )
    band["mean_sales"] = band["mean_sales"].round(2)
    band["sales_share"] = band.apply(
        lambda r: round(r["total_sales"] / total_by_cat[r["category"]] * 100, 2),
        axis=1,
    )
    band.to_sql("price_band_agg", engine, if_exists="replace", index=False)

    print(f"platform_summary {len(summary)} 行, price_band_agg {len(band)} 行已写入")
    engine.dispose()


def main(df):
    load_products(df)
    load_aggregates(df)
    print("MySQL ETL 完成")


if __name__ == "__main__":
    from analysis.clean import main as clean_main
    main(clean_main())
