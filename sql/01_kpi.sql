-- 经营核心指标
-- 粒度：kpi_snapshot 一行；趋势按日 / 月
-- 口径：有效订单（非 canceled/unavailable）；GMV = price；利润率 = 估算 30%
-- 业务当日、当月来自 preprocess 写入的 is_as_of_day / is_as_of_month

CREATE OR REPLACE TABLE kpi_snapshot AS
WITH base AS (
    SELECT
        ROUND(SUM(gmv) FILTER (WHERE is_as_of_day), 2) AS today_gmv,
        COUNT(DISTINCT order_id) FILTER (WHERE is_as_of_day) AS today_orders,
        ROUND(SUM(estimated_profit) FILTER (WHERE is_as_of_day), 2) AS today_estimated_profit,
        ROUND(SUM(gmv) FILTER (WHERE is_as_of_month), 2) AS month_gmv,
        COUNT(DISTINCT order_id) FILTER (WHERE is_as_of_month) AS month_orders,
        ROUND(SUM(estimated_profit) FILTER (WHERE is_as_of_month), 2) AS month_estimated_profit
    FROM fact_sales
    WHERE is_valid_order
)
SELECT
    m.as_of_date,
    m.as_of_month,
    b.today_gmv,
    b.today_orders,
    ROUND(b.today_gmv / NULLIF(b.today_orders, 0), 2) AS today_aov,
    b.today_estimated_profit,
    ROUND(b.today_estimated_profit / NULLIF(b.today_gmv, 0), 4) AS today_estimated_margin,
    b.month_gmv,
    b.month_orders,
    ROUND(b.month_gmv / NULLIF(b.month_orders, 0), 2) AS month_aov,
    b.month_estimated_profit,
    ROUND(b.month_estimated_profit / NULLIF(b.month_gmv, 0), 4) AS month_estimated_margin
FROM base b
CROSS JOIN meta_asof m;

CREATE OR REPLACE TABLE sales_trend_daily AS
SELECT
    CAST(order_purchase_date AS DATE) AS order_date,
    COUNT(DISTINCT order_id) AS orders,
    COUNT(*) AS items,
    ROUND(SUM(gmv), 2) AS gmv,
    ROUND(SUM(gmv) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS aov,
    ROUND(SUM(estimated_profit), 2) AS estimated_profit
FROM fact_sales
WHERE is_valid_order
GROUP BY 1
ORDER BY 1;

CREATE OR REPLACE TABLE sales_trend_monthly AS
SELECT
    order_purchase_month AS order_month,
    COUNT(DISTINCT order_id) AS orders,
    COUNT(*) AS items,
    ROUND(SUM(gmv), 2) AS gmv,
    ROUND(SUM(gmv) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS aov,
    ROUND(SUM(estimated_profit), 2) AS estimated_profit
FROM fact_sales
WHERE is_valid_order
GROUP BY 1
ORDER BY 1;
