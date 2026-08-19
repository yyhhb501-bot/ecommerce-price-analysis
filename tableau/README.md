# Tableau 仪表盘搭建指南

本项目已准备好 Tableau 数据源，两种方式任选：

## 方式一：直接打开 .hyper 提取（推荐）

打开 `tableau/ecommerce_prices.hyper`（Tableau Desktop / Tableau Public 均支持）。
内含 3 张表：

| 表 | 说明 |
|---|---|
| `products` | 88 条 SKU 明细（平台/品类/价格/销量/价格带） |
| `platform_summary` | 品类 × 平台汇总 |
| `price_band_agg` | 价格带聚合（销量占比） |

也可用 `tableau/*.csv` 作为备选数据源。

## 方式二：直连 MySQL（实时）

| 项 | 值 |
|---|---|
| 连接器 | MySQL |
| 服务器 | `localhost` |
| 端口 | `3306` |
| 数据库 | `ecommerce_prices` |
| 用户名 | `ecom_user` |
| 密码 | `ecom_pass_2026` |

## 建议仪表盘（4 张工作表 + 1 仪表盘）

1. **价格带分布**（柱状图）：`price_band_agg`，X=价格带，Y=总销量，颜色=品类。
2. **各平台价格水平**（箱线图）：`products`，维度=平台，度量=价格。
3. **价格-销量关系**（散点图）：`products`，X=price，Y=log_sales，颜色=品类，加趋势线。
4. **A/B 测试结果**（对照表/条形图）：连接 `ab_test_result` 表，展示各指标提升%与显著性。
5. **仪表盘**：把 1~4 组合，加「品类」和「平台」筛选器，标题《电商竞品价格与销量分析》。

## 分析查询参考

如需自定义口径，可用 `sql/02_analysis_queries.sql` 中的 7 条 SQL 在 MySQL 中
直接计算（含价格-销量 Pearson 相关系数的纯 SQL 实现）。
