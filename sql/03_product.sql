-- 商品与品类分析
-- 粒度：英译品类 + 中文名；销量 = 订单行数；均价 = GMV / 销量
-- 仅有效订单

CREATE OR REPLACE TABLE category_sales AS
WITH totals AS (
    SELECT SUM(gmv) AS total_gmv
    FROM fact_sales
    WHERE is_valid_order
),
mapped AS (
    SELECT
        s.*,
        CASE s.product_category_name_english
            WHEN 'health_beauty' THEN '健康美容'
            WHEN 'watches_gifts' THEN '手表礼品'
            WHEN 'bed_bath_table' THEN '床上浴室用品'
            WHEN 'sports_leisure' THEN '运动休闲'
            WHEN 'computers_accessories' THEN '电脑配件'
            WHEN 'furniture_decor' THEN '家具装饰'
            WHEN 'housewares' THEN '家居日用'
            WHEN 'cool_stuff' THEN '趣味用品'
            WHEN 'auto' THEN '汽车用品'
            WHEN 'garden_tools' THEN '园艺工具'
            WHEN 'toys' THEN '玩具'
            WHEN 'baby' THEN '母婴'
            WHEN 'perfumery' THEN '香水'
            WHEN 'telephony' THEN '手机通讯'
            WHEN 'office_furniture' THEN '办公家具'
            WHEN 'stationery' THEN '文具'
            WHEN 'computers' THEN '电脑'
            WHEN 'pet_shop' THEN '宠物'
            WHEN 'small_appliances' THEN '小家电'
            WHEN 'musical_instruments' THEN '乐器'
            WHEN 'unknown' THEN '未知品类'
            WHEN 'electronics' THEN '电子产品'
            WHEN 'consoles_games' THEN '游戏主机'
            WHEN 'fashion_bags_accessories' THEN '箱包配饰'
            WHEN 'construction_tools_construction' THEN '建筑工具'
            WHEN 'luggage_accessories' THEN '旅行配件'
            WHEN 'home_appliances_2' THEN '大家电'
            WHEN 'home_construction' THEN '家装建材'
            WHEN 'home_appliances' THEN '家用电器'
            WHEN 'agro_industry_and_commerce' THEN '农工贸易'
            WHEN 'furniture_living_room' THEN '客厅家具'
            WHEN 'home_confort' THEN '家居舒适'
            WHEN 'fixed_telephony' THEN '固定电话'
            WHEN 'air_conditioning' THEN '空调'
            WHEN 'audio' THEN '音响'
            WHEN 'small_appliances_home_oven_and_coffee' THEN '烤箱咖啡机'
            WHEN 'kitchen_dining_laundry_garden_furniture' THEN '厨卫花园家具'
            WHEN 'books_general_interest' THEN '大众图书'
            WHEN 'construction_tools_lights' THEN '施工照明'
            WHEN 'industry_commerce_and_business' THEN '工商业'
            WHEN 'construction_tools_safety' THEN '安全施工'
            WHEN 'food' THEN '食品'
            WHEN 'market_place' THEN '集市商品'
            WHEN 'costruction_tools_garden' THEN '园艺施工'
            WHEN 'art' THEN '艺术品'
            WHEN 'fashion_shoes' THEN '鞋履'
            WHEN 'drinks' THEN '饮料'
            WHEN 'signaling_and_security' THEN '安防标识'
            WHEN 'furniture_bedroom' THEN '卧室家具'
            WHEN 'books_technical' THEN '技术图书'
            WHEN 'costruction_tools_tools' THEN '五金工具'
            WHEN 'food_drink' THEN '食品饮料'
            WHEN 'fashion_male_clothing' THEN '男装'
            WHEN 'fashion_underwear_beach' THEN '内衣泳装'
            WHEN 'christmas_supplies' THEN '圣诞用品'
            WHEN 'tablets_printing_image' THEN '平板打印影像'
            WHEN 'cine_photo' THEN '摄影摄像'
            WHEN 'music' THEN '音乐'
            WHEN 'books_imported' THEN '进口图书'
            WHEN 'dvds_blu_ray' THEN '影碟'
            WHEN 'party_supplies' THEN '派对用品'
            WHEN 'furniture_mattress_and_upholstery' THEN '床垫软装'
            WHEN 'kitchen_portable_and_food_preparers' THEN '厨房小电器'
            WHEN 'fashio_female_clothing' THEN '女装'
            WHEN 'fashion_sport' THEN '运动服饰'
            WHEN 'la_cuisine' THEN '厨具'
            WHEN 'arts_and_craftmanship' THEN '手工艺'
            WHEN 'diapers_and_hygiene' THEN '尿布卫生'
            WHEN 'pc_gamer' THEN '游戏电脑'
            WHEN 'flowers' THEN '花卉'
            WHEN 'home_comfort_2' THEN '家居舒适II'
            WHEN 'cds_dvds_musicals' THEN '音乐影碟'
            WHEN 'fashion_childrens_clothes' THEN '童装'
            WHEN 'security_and_services' THEN '安保服务'
            ELSE s.product_category_name_english
        END AS category_zh
    FROM fact_sales s
    WHERE s.is_valid_order
)
SELECT
    ROW_NUMBER() OVER (ORDER BY SUM(m.gmv) DESC) AS category_rank,
    m.product_category_name_english AS category,
    m.category_zh,
    COUNT(*) AS items,
    COUNT(DISTINCT m.order_id) AS orders,
    ROUND(SUM(m.gmv), 2) AS gmv,
    ROUND(SUM(m.gmv) / NULLIF(COUNT(*), 0), 2) AS avg_item_price,
    ROUND(SUM(m.gmv) / NULLIF((SELECT total_gmv FROM totals), 0), 4) AS gmv_share
FROM mapped m
GROUP BY m.product_category_name_english, m.category_zh
ORDER BY gmv DESC;
