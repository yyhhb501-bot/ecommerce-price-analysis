"""生成定价分析报告（Markdown）。"""
import json
import os
from datetime import datetime

from config import PROCESSED_DIR, REPORT_PATH, FIG_DIR, PLATFORMS

CATEGORY_NAME = {"polo衫": "Polo 衫", "牛仔裤": "牛仔裤"}


def _fmt_band(band):
    a, b = band.split("-")
    return f"{int(a)}–{int(b)} 元"


def build_report(result, ab_result=None):
    corr = result["correlation"]
    core = result["core_price_band"]
    recs = result["recommendations"]
    summary = result["summary"]

    lines = []
    lines.append("# 电商竞品价格与销量分析报告\n")
    lines.append(f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}\n")
    lines.append(f"> 品类：Polo 衫、牛仔裤　|　平台：{' / '.join(PLATFORMS)}\n")

    lines.append("## 一、数据说明\n")
    lines.append(
        f"- 采集范围：{len(CATEGORY_NAME)} 个品类 × {len(PLATFORMS)} 个平台，共 "
        f"**{sum(r['sku_count'] for r in summary)}** 个 SKU。\n"
    )
    lines.append(
        "- 数据来源：`crawled`（真实抓取）与 `reference`（参考估测，用于被风控拦截时的兜底），"
        "来源字段已在明细数据中标注，本报告结论仅供定价参考。\n"
    )

    lines.append("## 二、价格与销量相关性\n")
    lines.append("| 品类 | Pearson | Spearman | 样本数 |")
    lines.append("|---|---|---|---|")
    for cat, v in corr.items():
        lines.append(
            f"| {CATEGORY_NAME[cat]} | {v['pearson']} | {v['spearman']} | {v['n']} |"
        )
    lines.append("\n> 相关系数为负表示「价格越低、销量越高」，绝对值越大关系越强。\n")

    lines.append("## 三、核心价格带\n")
    lines.append("| 品类 | 核心价格带 | 销量占比 | 平均销量 | SKU 数 |")
    lines.append("|---|---|---|---|---|")
    for cat, v in core.items():
        lines.append(
            f"| {CATEGORY_NAME[cat]} | {_fmt_band(v['core_band'])} | "
            f"{v['core_band_sales_share']}% | {v['core_band_mean_sales']:.0f} 件 | "
            f"{v['core_band_sku_count']} |"
        )
    lines.append("")

    lines.append("## 四、定价建议（可执行）\n")
    for cat, v in recs.items():
        lines.append(f"### {CATEGORY_NAME[cat]}\n")
        lines.append(f"- **引流款**：定价 **{v['引流款建议价']} 元**（核心带下沿，冲销量、抢流量）。")
        lines.append(f"- **主推款**：定价 **{v['主推款建议价']} 元**（贴近品类中位数，走量兼利润）。")
        lines.append(f"- **利润款**：定价 **{v['利润款建议价']} 元**（核心带上沿，毛利空间更大）。")
        lines.append(f"- 整体参考区间：**{v['参考区间']}**。\n")

    lines.append("## 五、A/B 测试验证（业务落地）\n")
    if ab_result:
        d = ab_result["design"]
        actual = d["daily_traffic_per_group"] * d["duration_days"]
        lines.append(
            f"> 场景：{ab_result['scenario']}，{d['duration_days']} 天，"
            f"最小样本量 {d['sample_size_per_group']}/组（实际每组约 {actual:,} 访客），"
            f"α={d['alpha']}，power={d['power']}。\n"
        )
        lines.append("| 指标 | 对照组(A) | 实验组(B) | 提升 | p 值 | 结论 |")
        lines.append("|---|---|---|---|---|---|")
        for r in ab_result["results"]:
            lines.append(
                f"| {r['metric']} | {r['control_value']} | {r['treatment_value']} | "
                f"{r['lift_pct']:+.1f}% | {r['p_value']:.4g} | "
                f"{'显著' if r['significant'] else '不显著'} |"
            )
        lines.append("")
        lines.append(f"**结论**：{ab_result['conclusion']}\n")

    lines.append("## 六、图表\n")
    for f in sorted(os.listdir(FIG_DIR)):
        if f.endswith(".png"):
            lines.append(f"![{f}](figures/{f})")
    lines.append("")

    lines.append("## 七、局限与说明\n")
    lines.append(
        "- 抖音/淘宝/拼多多均有登录态与签名风控，真实抓取被拦截的部分已用参考估测数据补齐，"
        "结论为方法演示，不构成真实经营建议。\n"
    )
    lines.append(
        "- 销量口径在各平台不完全一致（件/月 vs 总销量），已统一按「近 30 天销量」近似处理。\n"
    )

    text = "\n".join(lines)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"报告已生成: {REPORT_PATH}")
    return text


if __name__ == "__main__":
    with open(os.path.join(PROCESSED_DIR, "analysis_result.json"), encoding="utf-8") as f:
        result = json.load(f)
    build_report(result)
