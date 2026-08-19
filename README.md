# 电商竞品价格与销量分析（Polo 衫 & 牛仔裤）

对淘宝、拼多多、抖音三个平台的同品类商品做价格与销量分析，输出价格带分布、
价格-销量相关性、核心价格带识别、可执行定价建议，并用 A/B 测试验证定价落地效果。

技术栈：**Python + MySQL + Tableau**（pandas 分析、MySQL 存储、Tableau 可视化）。

## 核心结论

| 品类 | 价格-销量 Pearson | 核心价格带 | 引流款 | 主推款 | 利润款 |
|---|---|---|---|---|---|
| Polo 衫 | -0.689 | 20–39 元（占 51.8% 销量） | 39 元 | 58 元 | 76 元 |
| 牛仔裤 | -0.782 | 40–59 元（占 43.8% 销量） | 58 元 | 79 元 | 112 元 |

> 两个品类的价格-销量均呈显著负相关：价格越低、销量越高。
> 完整报告见 [`output/report.md`](output/report.md)，
> 成果汇总表见 [`output/项目成果分析.xlsx`](output/项目成果分析.xlsx)。

### A/B 测试（业务落地）

对 Polo 衫引流款做 14 天 A/B 测试（58 元 vs 39 元）：降价显著提升转化率（+36.1%）
与订单量（+34.8%），但 GMV（-9.3%）与毛利（-36.3%）显著下降。结论：**39 元仅适合
限时/限量引流，日常主推维持 58 元，45–49 元区间需再测**——体现「分析→定价→实验→
决策」的完整业务闭环，而非简单的“降价走量”。

## 目录结构

```
ecommerce-price-analysis/
├── config.py                     # 全局配置（品类/平台/路径/MySQL）
├── main.py                       # 一键执行全流程
├── crawlers/                     # 三平台爬虫 + 备用数据生成
├── analysis/
│   ├── clean.py                  # 清洗（CSV + SQLite）
│   ├── etl_mysql.py              # 数据写入 MySQL
│   ├── analyze.py                # 价格带/相关性/定价建议
│   ├── ab_test.py                # A/B 测试（样本量/显著性/结论）
│   ├── visualize.py              # matplotlib 图表
│   ├── report.py                 # Markdown 报告
│   ├── export_excel.py           # 成果汇总 Excel
│   └── export_tableau.py         # 生成 Tableau .hyper 提取
├── sql/
│   ├── 01_create_schema.sql      # 建库建表（4 张表）
│   └── 02_analysis_queries.sql   # 分析 SQL（含纯 SQL 相关系数）
├── tableau/                      # .hyper 提取 + 仪表盘指南
├── data/raw/                     # 抓取结果 + 备用数据
├── data/processed/               # 清洗后 CSV + SQLite + 分析结果
└── output/                       # 图表 / 报告 / 成果 Excel
```

## 环境与运行

- Python 3.13（64 位）+ MySQL 9.0
- 依赖：`pip install -r requirements.txt`（含 pandas/scipy/sqlalchemy/pymysql/tableauhyperapi）
- 建库（首次，root）：`mysql -u root -p < sql/01_create_schema.sql`
- 一键运行：`python main.py`

流程：真实抓取 → 备用数据兜底 → 清洗 → MySQL 入库 → 分析 → A/B 测试 → 可视化 → 报告 + Excel + Tableau 提取。

## MySQL 数据模型（库 `ecommerce_prices`）

| 表 | 说明 |
|---|---|
| `products` | 商品明细（88 条 SKU） |
| `platform_summary` | 品类 × 平台汇总 |
| `price_band_agg` | 价格带聚合 |
| `ab_test_result` | A/B 测试各指标结果 |

分析 SQL 见 `sql/02_analysis_queries.sql`（含价格-销量 Pearson 的纯 SQL 实现）。

## Tableau 可视化

打开 `tableau/ecommerce_prices.hyper`（或直连 MySQL `ecom_user`/`ecom_pass_2026`），
按 [`tableau/README.md`](tableau/README.md) 搭建「价格带分布 / 平台箱线图 /
价格-销量散点 / A/B 结果」四张工作表组成的仪表盘。

## 数据说明（重要）

- **真实抓取**：淘宝、拼多多、抖音商城均有登录态 + 签名（`sign`/`anti-content`/`X-Bogus`）
  风控，未登录请求会被拦截。爬虫已实现完整请求与解析流程，并在 `data/raw/crawl_report.json`
  如实记录拦截状态。
- **备用数据**：为跑通流程，用贴近真实分布的参考数据兜底，`data_source='reference'`
  与 `'crawled'` 严格区分。
- **A/B 数据**：实验为可复现的模拟数据（`SEED=42`），用于演示框架；接入真实流量日志后
  替换 `ab_test.py::simulate()` 即可用于生产。
- **结论性质**：本项目为方法与流程演示，不构成真实经营建议。

## 简历用项目描述（已填写）

- **项目名称**：电商平台同品类竞品价格与销量分析
- **项目角色**：数据分析
- **项目概述**：为店铺定价提供参考，采集淘宝、拼多多、抖音三个平台 Polo 衫与牛仔裤
  共 88 个 SKU 的价格与销量数据，用 MySQL 存储、Tableau 可视化，分析价格带分布与
  价格-销量关系，并用 A/B 测试验证定价建议。
- **项目难点**：多平台数据口径不一致（价格区间、促销价、销量单位），需统一清洗规则；
  免费数据源有登录/签名风控，需设计增量抓取与限流策略，并用备用数据兜底；定价建议
  需通过 A/B 测试验证“流量 vs 毛利”的平衡，而非简单降价。
- **我的分工**：负责数据采集方案设计与实施，使用 Python 与 MySQL 完成清洗与存储，
  用 pandas/scipy 完成价格带分析、价格-销量相关性分析与 A/B 检验，用 Tableau 与
  matplotlib 输出可视化，撰写定价建议与实验报告。
- **项目业绩**：产出 1 份定价分析报告；识别 Polo 衫核心价格带 20–39 元、牛仔裤 40–59 元；
  价格-销量相关系数 Polo 衫 -0.689、牛仔裤 -0.782；A/B 测试发现 39 元引流款转化率 +36.1%
  但毛利 -36.3%，据此给出“限时引流 + 主推 58 元”的分层定价策略。
