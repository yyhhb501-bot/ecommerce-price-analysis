-- =====================================================================
-- 分析查询：在 MySQL 中完成价格带、相关性、核心价格带等分析
-- 运行：mysql -u ecom_user -pecom_pass_2026 ecommerce_prices < 02_analysis_queries.sql
-- =====================================================================

-- 1) 品类 × 平台 汇总
SELECT category, platform, sku_count, min_price, median_price, max_price,
       ROUND(mean_sales, 0) AS mean_sales, total_sales
FROM platform_summary
ORDER BY category, total_sales DESC;

-- 2) 价格带分布（按销量占比降序）
SELECT category, price_band, sku_count, total_sales,
       ROUND(mean_sales, 0) AS mean_sales, sales_share
FROM price_band_agg
ORDER BY category, total_sales DESC;

-- 3) 核心价格带：每个品类销量占比最高的价格带
SELECT category, price_band, sku_count, total_sales, sales_share
FROM price_band_agg p
WHERE sales_share = (
    SELECT MAX(sales_share) FROM price_band_agg q WHERE q.category = p.category
);

-- 4) 各平台价格水平对比（中位数、四分位）
SELECT platform, category,
       MIN(price) AS p_min,
       ROUND(AVG(price), 1) AS p_mean,
       ROUND(MAX(price), 0) AS p_max
FROM products
GROUP BY platform, category
ORDER BY category, p_mean;

-- 5) 价格-销量 Pearson 相关系数（纯 SQL 计算，价格 vs log10 销量）
SELECT p.category,
       ROUND(
         SUM((p.price - a.avg_price) * (p.log_sales - a.avg_log)) /
         (SQRT(SUM(POWER(p.price - a.avg_price, 2))) *
          SQRT(SUM(POWER(p.log_sales - a.avg_log, 2)))),
       3) AS pearson_r
FROM products p
JOIN (
    SELECT category, AVG(price) AS avg_price, AVG(log_sales) AS avg_log
    FROM products GROUP BY category
) a ON p.category = a.category
GROUP BY p.category;

-- 6) 低价高销量 TOP10（引流款候选）
SELECT platform, category, title, price, sales
FROM products
ORDER BY sales DESC
LIMIT 10;

-- 7) 利润款候选：价格高于品类 P75 且仍有一定销量
SELECT p.platform, p.category, p.title, p.price, p.sales
FROM products p
JOIN (
    SELECT category, MAX(price) AS hi
    FROM (SELECT category, price FROM products ORDER BY price) x
    GROUP BY category
) q ON p.category = q.category
WHERE p.price >= 0.75 * q.hi
ORDER BY p.sales DESC
LIMIT 10;
