-- 客户与地区分析
-- 粒度：customer_overview 一行；州 / 城市销售供地图使用
-- 客户用 customer_unique_id；复购 = 有效订单数 >= 2

CREATE OR REPLACE TABLE customer_overview AS
WITH order_cust AS (
    SELECT DISTINCT
        order_id,
        customer_unique_id
    FROM fact_sales
    WHERE is_valid_order
),
cust AS (
    SELECT
        customer_unique_id,
        COUNT(*) AS order_cnt
    FROM order_cust
    GROUP BY 1
)
SELECT
    COUNT(*) AS customers,
    COUNT(*) FILTER (WHERE order_cnt >= 2) AS repeat_customers,
    ROUND(COUNT(*) FILTER (WHERE order_cnt >= 2) * 1.0 / NULLIF(COUNT(*), 0), 4) AS repeat_rate,
    ROUND(AVG(order_cnt), 4) AS avg_orders_per_customer
FROM cust;

CREATE OR REPLACE TABLE sales_by_state AS
WITH sales AS (
    SELECT
        customer_state,
        COUNT(DISTINCT order_id) AS orders,
        COUNT(DISTINCT customer_unique_id) AS customers,
        COUNT(*) AS items,
        ROUND(SUM(gmv), 2) AS gmv,
        ROUND(SUM(estimated_profit), 2) AS estimated_profit
    FROM fact_sales
    WHERE is_valid_order
    GROUP BY 1
),
geo AS (
    SELECT
        geolocation_state,
        AVG(geolocation_lat) AS state_lat,
        AVG(geolocation_lng) AS state_lng
    FROM dim_geolocation
    GROUP BY 1
)
SELECT
    s.customer_state,
    s.orders,
    s.customers,
    s.items,
    s.gmv,
    ROUND(s.gmv / NULLIF(s.orders, 0), 2) AS aov,
    s.estimated_profit,
    g.state_lat,
    g.state_lng
FROM sales s
LEFT JOIN geo g
    ON s.customer_state = g.geolocation_state
ORDER BY s.gmv DESC;

CREATE OR REPLACE TABLE sales_by_city AS
WITH sales AS (
    SELECT
        customer_state,
        customer_city,
        COUNT(DISTINCT order_id) AS orders,
        COUNT(DISTINCT customer_unique_id) AS customers,
        COUNT(*) AS items,
        ROUND(SUM(gmv), 2) AS gmv
    FROM fact_sales
    WHERE is_valid_order
    GROUP BY 1, 2
),
geo AS (
    SELECT
        geolocation_state,
        geolocation_city,
        AVG(geolocation_lat) AS city_lat,
        AVG(geolocation_lng) AS city_lng
    FROM dim_geolocation
    GROUP BY 1, 2
)
SELECT
    s.customer_state,
    s.customer_city,
    s.orders,
    s.customers,
    s.items,
    s.gmv,
    ROUND(s.gmv / NULLIF(s.orders, 0), 2) AS aov,
    g.city_lat,
    g.city_lng
FROM sales s
LEFT JOIN geo g
    ON s.customer_state = g.geolocation_state
    AND s.customer_city = g.geolocation_city
ORDER BY s.gmv DESC;
