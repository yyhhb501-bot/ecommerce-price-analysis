-- =====================================================================
-- 电商竞品价格分析 - MySQL 建库建表脚本
-- 目标：淘宝/拼多多/抖音 三平台 Polo 衫、牛仔裤 价格与销量分析
-- =====================================================================

CREATE DATABASE IF NOT EXISTS ecommerce_prices
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 专用分析账号（最小权限，只授权本项目库）
CREATE USER IF NOT EXISTS 'ecom_user'@'localhost' IDENTIFIED BY 'ecom_pass_2026';
GRANT SELECT, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, INDEX
    ON ecommerce_prices.* TO 'ecom_user'@'localhost';
FLUSH PRIVILEGES;

USE ecommerce_prices;

-- 1) 商品明细表（清洗后 SKU）
DROP TABLE IF EXISTS products;
CREATE TABLE products (
    sku_id         VARCHAR(20)  NOT NULL,
    platform       VARCHAR(20)  NOT NULL COMMENT '淘宝/拼多多/抖音',
    category       VARCHAR(20)  NOT NULL COMMENT 'polo衫/牛仔裤',
    title          VARCHAR(200),
    brand          VARCHAR(40),
    price          DECIMAL(10,2) NOT NULL COMMENT '实际成交价(元)',
    original_price DECIMAL(10,2) COMMENT '划线价(元)',
    sales          INT          NOT NULL DEFAULT 0 COMMENT '近30天销量(件)',
    sales_unit     VARCHAR(20)  COMMENT '销量口径',
    comments       INT          NOT NULL DEFAULT 0 COMMENT '评价数(替代指标)',
    shop_name      VARCHAR(100),
    data_source    VARCHAR(20)  COMMENT 'crawled/reference',
    crawl_time     VARCHAR(40),
    price_band     VARCHAR(20)  COMMENT '价格带分箱',
    log_sales      DOUBLE       COMMENT 'log10(sales)',
    PRIMARY KEY (sku_id),
    KEY idx_cat_platform (category, platform),
    KEY idx_price (price),
    KEY idx_band (category, price_band)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) 品类×平台汇总表
DROP TABLE IF EXISTS platform_summary;
CREATE TABLE platform_summary (
    category      VARCHAR(20) NOT NULL,
    platform      VARCHAR(20) NOT NULL,
    sku_count     INT,
    min_price     DECIMAL(10,2),
    median_price  DECIMAL(10,2),
    max_price     DECIMAL(10,2),
    mean_sales    DECIMAL(12,2),
    total_sales   BIGINT,
    PRIMARY KEY (category, platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) 价格带聚合表
DROP TABLE IF EXISTS price_band_agg;
CREATE TABLE price_band_agg (
    category    VARCHAR(20) NOT NULL,
    price_band  VARCHAR(20) NOT NULL,
    sku_count   INT,
    total_sales BIGINT,
    mean_sales  DECIMAL(12,2),
    sales_share DECIMAL(6,2) COMMENT '销量占比%',
    PRIMARY KEY (category, price_band)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4) A/B 测试结果表
DROP TABLE IF EXISTS ab_test_result;
CREATE TABLE ab_test_result (
    experiment_id         VARCHAR(40) NOT NULL,
    category              VARCHAR(20) NOT NULL,
    metric                VARCHAR(40) COMMENT '指标名',
    control_value         DOUBLE      COMMENT '对照组(A)',
    treatment_value       DOUBLE      COMMENT '实验组(B)',
    lift_pct              DECIMAL(10,4) COMMENT '提升幅度%',
    p_value               DECIMAL(10,6) COMMENT '显著性p值',
    sample_size_per_group INT,
    significant           TINYINT     COMMENT '是否显著(0/1)',
    conclusion            VARCHAR(200),
    PRIMARY KEY (experiment_id, metric)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
