-- RFM 分层
-- Recency：业务当日距离最近一次有效下单的天数（越小越好）
-- Frequency：有效订单数。Olist 约 97% 只有 1 单，不用 NTILE，改为 1/2/3+ → 1/3/5
-- Monetary：有效订单 GMV（price）合计，五分位 1–5
-- 分段互斥：Champions → Loyal Customers → Potential Loyalists → At Risk → Lost Customers

CREATE OR REPLACE TABLE rfm_customers AS
WITH as_of_meta AS (
    SELECT CAST(as_of_date AS DATE) AS as_of_date
    FROM meta_asof
),
base AS (
    SELECT
        s.customer_unique_id,
        DATE_DIFF(
            'day',
            CAST(MAX(s.order_purchase_date) AS DATE),
            a.as_of_date
        ) AS recency_days,
        COUNT(DISTINCT s.order_id) AS frequency,
        ROUND(SUM(s.gmv), 2) AS monetary,
        MIN(s.order_purchase_timestamp) AS first_purchase_ts,
        MAX(s.order_purchase_timestamp) AS last_purchase_ts
    FROM fact_sales s
    CROSS JOIN as_of_meta a
    WHERE s.is_valid_order
    GROUP BY s.customer_unique_id, a.as_of_date
),
scored AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        CASE
            WHEN frequency >= 3 THEN 5
            WHEN frequency = 2 THEN 3
            ELSE 1
        END AS f_score,
        NTILE(5) OVER (ORDER BY monetary) AS m_score
    FROM base
)
SELECT
    customer_unique_id,
    recency_days,
    frequency,
    monetary,
    first_purchase_ts,
    last_purchase_ts,
    r_score,
    f_score,
    m_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 4 THEN 'Champions'
        WHEN f_score >= 3 AND r_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 THEN 'Potential Loyalists'
        WHEN r_score >= 2 THEN 'At Risk'
        ELSE 'Lost Customers'
    END AS segment
FROM scored;

CREATE OR REPLACE TABLE rfm_segment_summary AS
SELECT
    segment,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS customer_share_pct,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(frequency), 2) AS avg_frequency,
    ROUND(AVG(monetary), 2) AS avg_monetary,
    ROUND(SUM(monetary), 2) AS total_gmv,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 2) AS gmv_share_pct
FROM rfm_customers
GROUP BY 1
ORDER BY total_gmv DESC;

CREATE OR REPLACE TABLE rfm_score_heatmap AS
SELECT
    r_score,
    m_score,
    COUNT(*) AS customers,
    ROUND(SUM(monetary), 2) AS total_gmv
FROM rfm_customers
GROUP BY 1, 2
ORDER BY 1, 2;
