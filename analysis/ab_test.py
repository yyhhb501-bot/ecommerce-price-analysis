"""A/B 测试：引流款定价实验的业务落地框架。

场景：分析建议 Polo 衫引流款由 58 元下调到 39 元。用 A/B 测试验证降价能否
显著提升转化率与 GMV/毛利，从而支持「全量上线」的决策。

说明：本模块提供完整的实验设计（样本量/显著性检验/结论）框架，并用可复现的
模拟数据演示。接入真实流量日志后，替换 simulate() 即可直接用于生产。
"""
import json
import os

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import create_engine

from config import MYSQL, PROCESSED_DIR

OUT_JSON = os.path.join(PROCESSED_DIR, "ab_test_result.json")

# 业务参数
CONTROL_PRICE = 58        # A 组（对照组）价格
TREATMENT_PRICE = 39      # B 组（实验组）价格
UNIT_COST = 22            # 单品成本（估算）
P0 = 0.08                 # A 组预期转化率
P1 = 0.11                 # B 组预期转化率（降价后提升）
ALPHA = 0.05
POWER = 0.8
DURATION_DAYS = 14
DAILY_TRAFFIC = 10000     # 每组每日曝光/访客
SEED = 42


def sample_size_proportion(p0, p1, alpha=ALPHA, power=POWER):
    """两样本比例检验的最小样本量（每组）。"""
    za = stats.norm.ppf(1 - alpha / 2)
    zb = stats.norm.ppf(power)
    p = (p0 + p1) / 2
    n = (za + zb) ** 2 * 2 * p * (1 - p) / (p1 - p0) ** 2
    return int(np.ceil(n))


def ztest_proportion(x1, n1, x2, n2):
    """两样本比例 z 检验，返回 (z, p_value)。"""
    p1 = x1 / n1
    p2 = x2 / n2
    p = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    return z, p_value


def simulate(days=DURATION_DAYS, traffic=DAILY_TRAFFIC, seed=SEED):
    """模拟 14 天两组日级数据，返回 DataFrame。"""
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(days):
        for group, p, price in (("A", P0, CONTROL_PRICE), ("B", P1, TREATMENT_PRICE)):
            visits = int(rng.normal(traffic, traffic * 0.05))
            orders = int(rng.binomial(visits, p))
            gmv = orders * price
            profit = orders * (price - UNIT_COST)
            rows.append({"day": d, "group": group, "visits": visits,
                         "orders": orders, "gmv": gmv, "profit": profit})
    return pd.DataFrame(rows)


def run():
    n = sample_size_proportion(P0, P1)

    df = simulate()
    g = df.groupby("group").agg(
        visits=("visits", "sum"), orders=("orders", "sum"),
        gmv=("gmv", "sum"), profit=("profit", "sum"),
    )

    # 1) 转化率：比例 z 检验
    z, p_conv = ztest_proportion(
        int(g.loc["B", "orders"]), int(g.loc["B", "visits"]),
        int(g.loc["A", "orders"]), int(g.loc["A", "visits"]),
    )
    conv_a = g.loc["A", "orders"] / g.loc["A", "visits"]
    conv_b = g.loc["B", "orders"] / g.loc["B", "visits"]

    results = []
    results.append({
        "metric": "转化率", "test": "两样本比例 z 检验",
        "control_value": round(conv_a, 4), "treatment_value": round(conv_b, 4),
        "lift_pct": round((conv_b - conv_a) / conv_a * 100, 2),
        "p_value": round(float(p_conv), 6),
        "significant": int(p_conv < ALPHA),
    })

    # 2) 日订单量 / GMV / 毛利：Welch t 检验
    for metric in ("orders", "gmv", "profit"):
        a = df.loc[df["group"] == "A", metric].values
        b = df.loc[df["group"] == "B", metric].values
        t, p = stats.ttest_ind(b, a, equal_var=False)
        results.append({
            "metric": {"orders": "日订单量", "gmv": "日GMV", "profit": "日毛利"}[metric],
            "test": "Welch t 检验",
            "control_value": round(float(a.mean()), 2),
            "treatment_value": round(float(b.mean()), 2),
            "lift_pct": round((b.mean() - a.mean()) / a.mean() * 100, 2),
            "p_value": round(float(p), 6),
            "significant": int(p < ALPHA),
        })

    gmv_lift = (g.loc["B", "gmv"] - g.loc["A", "gmv"]) / g.loc["A", "gmv"] * 100
    profit_lift = (g.loc["B", "profit"] - g.loc["A", "profit"]) / g.loc["A", "profit"] * 100

    conclusion = (
        f"降价({CONTROL_PRICE}->{TREATMENT_PRICE}元)后转化率 {'显著' if p_conv < ALPHA else '不显著'}提升，"
        f"累计 GMV 变化 {gmv_lift:+.1f}%、毛利变化 {profit_lift:+.1f}%。"
    )
    if p_conv < ALPHA and profit_lift > 0:
        conclusion += " 建议：全量上线 39 元引流款，并持续观察毛利红线。"
    else:
        conclusion += " 建议：暂不扩量，缩小毛利损失后复测。"

    result = {
        "scenario": "Polo 衫引流款定价 A/B 测试（58 元 vs 39 元）",
        "design": {
            "metric": "转化率",
            "control_price": CONTROL_PRICE,
            "treatment_price": TREATMENT_PRICE,
            "unit_cost": UNIT_COST,
            "alpha": ALPHA,
            "power": POWER,
            "sample_size_per_group": n,
            "duration_days": DURATION_DAYS,
            "daily_traffic_per_group": DAILY_TRAFFIC,
        },
        "group_totals": g.reset_index().to_dict("records"),
        "results": results,
        "conclusion": conclusion,
    }

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    _save_to_mysql(result)
    return result


def _save_to_mysql(result):
    url = (f"mysql+pymysql://{MYSQL['user']}:{MYSQL['password']}@"
           f"{MYSQL['host']}:{MYSQL['port']}/{MYSQL['database']}?charset={MYSQL['charset']}")
    engine = create_engine(url)
    exp_id = "AB_POLO_58_vs_39"
    rows = []
    for r in result["results"]:
        rows.append({
            "experiment_id": exp_id,
            "category": "polo衫",
            "metric": r["metric"],
            "control_value": r["control_value"],
            "treatment_value": r["treatment_value"],
            "lift_pct": r["lift_pct"],
            "p_value": r["p_value"],
            "sample_size_per_group": result["design"]["sample_size_per_group"],
            "significant": r["significant"],
            "conclusion": result["conclusion"],
        })
    pd.DataFrame(rows).to_sql("ab_test_result", engine, if_exists="replace", index=False)
    engine.dispose()
    print(f"A/B 测试结果已写入 MySQL ab_test_result ({len(rows)} 条)")

    print("\n=== A/B 测试结果 ===")
    for r in result["results"]:
        flag = "显著" if r["significant"] else "不显著"
        print(f"{r['metric']}: A={r['control_value']} B={r['treatment_value']} "
              f"lift={r['lift_pct']}% p={r['p_value']} [{flag}]")
    print(f"结论: {result['conclusion']}")


if __name__ == "__main__":
    run()
