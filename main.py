"""一键执行：抓取 -> 备用数据 -> 清洗入库 -> MySQL ETL -> 分析 -> A/B 测试 -> 可视化 -> 报告。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawlers.generate_reference_data import generate as gen_reference
from crawlers.run_crawlers import run_all as run_crawlers
from analysis.clean import main as clean_main
from analysis.etl_mysql import main as etl_mysql
from analysis.analyze import main as analyze_main
from analysis.ab_test import run as run_ab_test
from analysis.visualize import plot_all
from analysis.analyze import price_band_distribution
from analysis.report import build_report
from analysis.export_excel import main as export_excel
from analysis.export_tableau import main as export_tableau


def main():
    print("=" * 50)
    print("STEP 1/6 真实抓取尝试（淘宝/拼多多/抖音）")
    print("=" * 50)
    run_crawlers()

    print("\n" + "=" * 50)
    print("STEP 2/6 生成备用参考数据（兜底）")
    print("=" * 50)
    gen_reference()

    print("\n" + "=" * 50)
    print("STEP 3/6 清洗 + MySQL 入库")
    print("=" * 50)
    df = clean_main()
    etl_mysql(df)

    print("\n" + "=" * 50)
    print("STEP 4/6 分析 + A/B 测试")
    print("=" * 50)
    result = analyze_main(df)
    ab_result = run_ab_test()

    print("\n" + "=" * 50)
    print("STEP 5/6 可视化")
    print("=" * 50)
    plot_all(df, price_band_distribution(df))

    print("\n" + "=" * 50)
    print("STEP 6/6 生成报告 + 成果 Excel + Tableau 提取")
    print("=" * 50)
    build_report(result, ab_result)
    export_excel(result, ab_result)
    export_tableau()

    print("\n全部完成。报告: output/report.md　成果: output/项目成果分析.xlsx　Tableau: tableau/ecommerce_prices.hyper")


if __name__ == "__main__":
    main()
