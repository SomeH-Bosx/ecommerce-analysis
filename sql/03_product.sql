-- 商品与品类分析
-- 粒度：英译品类；销量 = 订单行数；均价 = GMV / 销量
-- 仅有效订单

CREATE OR REPLACE TABLE category_sales AS
WITH totals AS (
    SELECT SUM(gmv) AS total_gmv
    FROM fact_sales
    WHERE is_valid_order
)
SELECT
    ROW_NUMBER() OVER (ORDER BY SUM(s.gmv) DESC) AS category_rank,
    s.product_category_name_english AS category,
    COUNT(*) AS items,
    COUNT(DISTINCT s.order_id) AS orders,
    ROUND(SUM(s.gmv), 2) AS gmv,
    ROUND(SUM(s.gmv) / NULLIF(COUNT(*), 0), 2) AS avg_item_price,
    ROUND(SUM(s.gmv) / NULLIF((SELECT total_gmv FROM totals), 0), 4) AS gmv_share
FROM fact_sales s
WHERE s.is_valid_order
GROUP BY s.product_category_name_english
ORDER BY gmv DESC;
