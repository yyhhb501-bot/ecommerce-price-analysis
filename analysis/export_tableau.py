"""Tableau 数据导出：生成 .hyper 提取（Tableau Desktop/Public 可直接打开）+ CSV 副本。"""
import math
import os

import numpy as np
import pandas as pd
from tableauhyperapi import (
    HyperProcess, Telemetry, Connection, CreateMode,
    TableDefinition, TableName, SqlType, Inserter,
)

from config import PROCESSED_DIR, BASE_DIR

TABLEAU_DIR = os.path.join(BASE_DIR, "tableau")
HYPER_PATH = os.path.join(TABLEAU_DIR, "ecommerce_prices.hyper")


def _sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return SqlType.big_int()
    if pd.api.types.is_float_dtype(dtype):
        return SqlType.double()
    return SqlType.text()


def _to_row(df, idx):
    row = []
    for v in df.iloc[idx]:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            row.append(None)
        else:
            row.append(v)
    return row


def _write_df(conn, schema, table_name, df):
    cols = [TableDefinition.Column(c, _sql_type(df[c].dtype)) for c in df.columns]
    table = TableDefinition(table_name=TableName(schema, table_name), columns=cols)
    conn.catalog.create_table(table)
    with Inserter(conn, table) as ins:
        for i in range(len(df)):
            ins.add_row(_to_row(df, i))
        ins.execute()


def main():
    os.makedirs(TABLEAU_DIR, exist_ok=True)

    products = pd.read_csv(os.path.join(PROCESSED_DIR, "products_clean.csv"))
    summary = pd.read_sql_table("platform_summary", _mysql_engine())
    band = pd.read_sql_table("price_band_agg", _mysql_engine())

    with HyperProcess(telemetry=Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(endpoint=hyper.endpoint, database=HYPER_PATH,
                        create_mode=CreateMode.CREATE_AND_REPLACE) as conn:
            conn.catalog.create_schema("Extract")
            _write_df(conn, "Extract", "products", products)
            _write_df(conn, "Extract", "platform_summary", summary)
            _write_df(conn, "Extract", "price_band_agg", band)

    for name, df in [("products", products), ("platform_summary", summary),
                     ("price_band_agg", band)]:
        df.to_csv(os.path.join(TABLEAU_DIR, f"{name}.csv"), index=False,
                  encoding="utf-8-sig")

    print(f"Tableau 提取已生成: {HYPER_PATH}")
    print(f"CSV 副本已生成: {TABLEAU_DIR}")


def _mysql_engine():
    from sqlalchemy import create_engine
    from config import MYSQL
    url = (f"mysql+pymysql://{MYSQL['user']}:{MYSQL['password']}@"
           f"{MYSQL['host']}:{MYSQL['port']}/{MYSQL['database']}?charset={MYSQL['charset']}")
    return create_engine(url)


if __name__ == "__main__":
    main()
