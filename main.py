"""一键执行：抓取 -> 备用数据 -> 清洗入库 -> 分析 -> 可视化 -> 报告。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawlers.generate_reference_data import generate as gen_reference
from crawlers.run_crawlers import run_all as run_crawlers
from analysis.clean import main as clean_main
from analysis.analyze import main as analyze_main
from analysis.visualize import plot_all
from analysis.analyze import price_band_distribution
from analysis.report import build_report


def main():
    print("=" * 50)
    print("STEP 1/5 真实抓取尝试（淘宝/拼多多/抖音）")
    print("=" * 50)
    run_crawlers()

    print("\n" + "=" * 50)
    print("STEP 2/5 生成备用参考数据（兜底）")
    print("=" * 50)
    gen_reference()

    print("\n" + "=" * 50)
    print("STEP 3/5 清洗与入库")
    print("=" * 50)
    df = clean_main()

    print("\n" + "=" * 50)
    print("STEP 4/5 分析与可视化")
    print("=" * 50)
    result = analyze_main(df)
    plot_all(df, price_band_distribution(df))

    print("\n" + "=" * 50)
    print("STEP 5/5 生成报告")
    print("=" * 50)
    build_report(result)

    print("\n全部完成。报告: output/report.md")


if __name__ == "__main__":
    main()
