# 踩坑记录

规划阶段已确认的数据硬约束先记在这里，避免后面按“真实今日 / 真实利润”去实现。

## [2026-09-06] pip 安装在写入脚本时失败，venv 只装上了一部分包

- 现象：`pip install -r requirements.txt` 下载完成后，在 `Installing collected packages` 阶段报 `ValueError: Unable to find resource t64.exe in package pip._vendor.distlib`，并出现 `Ignoring invalid distribution ~ip`。导入检查：`pandas` / `matplotlib` / `sklearn` / `openai` / `seaborn` 都没有，只有 `duckdb` 等少量包能 import。
- 原因：Windows 上升级/重装 pip 时 `pip.exe` 被占用（WinError 32），卸载不完整，包名残留成 `~ip`，自带的 distlib 缺少 `t64.exe`，后续装带控制台脚本的包就会中途崩掉。
- 解决：先 `deactivate`，删掉整个 `.venv`，重新 `python -m venv .venv`，激活后用 `python -m pip install -r requirements.txt`（不要用被锁的 `pip.exe` 去升级自己）。装完用 `python -c "import pandas, duckdb"` 确认。

## [2026-09-06] Olist 没有真实“今日”订单

- 现象：需求写“今日 / 本月 GMV”，但 Olist 订单时间约在 2016–2018，按系统当天过滤会得到全 0。
- 原因：这是公开历史数据集，不是实时数仓。
- 解决：业务当日取 **delivered 订单** 的 `max(order_purchase_timestamp)`（当前为 2018-08-29）；“今日”= 该日，“本月”= 2018-08。不要用全表 max：最晚单是 2018-10-17 的取消单，按那天过滤今日 GMV 为 0。口径写在 `meta_asof`。

## [2026-09-06] 数据集没有商品成本，无法算真实利润率

- 现象：需求要“利润率”，Olist 只有 `price` 和 `freight_value`，没有 COGS / 成本。
- 原因：公开订单表面向成交过程，不包含商家内部成本。
- 解决：约定估算毛利率 30%。`gmv = price`，`estimated_profit = price * 0.30`，`estimated_cost = price * 0.70`。运费单独留在 `freight_value`，不计入 GMV。Dashboard / SQL 必须标明“估算”。

## [2026-09-06] Olist 复购极低，Frequency 不能用五分位

- 现象：约 97% 客户只有 1 单，`NTILE(5) OVER (ORDER BY frequency)` 会把大量同分客户硬切成 1–5，分数没有业务含义。
- 原因：这是一次性购买为主的电商公开集，不是高频会员池。
- 解决：F 分改为 1 单→1、2 单→3、3 单及以上→5。规则分层里 Champions / Loyal 只会是复购客（合计约 2%），其余按 Recency 分为 Potential Loyalists / At Risk / Lost。

## [2026-09-06] KMeans 五簇和规则分层对不齐

- 现象：交叉表里所有 Champions、Loyal Customers 都进了 `Champions-like`；Potential / At Risk / Lost 被 Recency、Monetary 切开。
- 原因：Frequency 几乎没有方差，标准化后复购客在特征空间里单独成团；KMeans 对其余客户主要按 R/M 切，和业务规则的互斥优先级不同。
- 解决：看板正式标签用 `rfm_customers.segment`（规则）。`cluster_label` 只作对照，不替代规则分层。

## [2026-09-06] DuckDB 把 CTE 名 asof 解析成 AS OF

- 现象：执行 `04_rfm.sql` 报 `Parser Error: syntax error at or near "asof"`。
- 原因：DuckDB 支持 `AS OF` 时间旅行语法，`WITH asof AS (...)` 会被拆开解析。
- 解决：CTE 改名为 `as_of_meta`。

## [2026-09-06] 城市名和地理表对不齐，部分城市没有坐标

- 现象：`sales_by_city` 共 4299 个城市，其中 345 个 `city_lat` 为空；州级 `sales_by_state` 全部有坐标。
- 原因：客户表城市名和 `olist_geolocation` 的拼写、重音、空格不完全一致（如 `sao paulo` vs `são paulo` 的残留写法），按州+城市等值连接会丢点。
- 解决：地图主用州级 `customer_state` + 州中心坐标。城市表保留，缺坐标的城市不画点，不在 SQL 里做模糊匹配以免把不同城合并错。

## [2026-09-06] 两个品类没有官方英译

- 现象：`product_category_name_translation.csv` 覆盖不了 `pc_gamer` 和 `portateis_cozinha_e_preparadores_de_alimentos`。
- 原因：Olist 翻译表只有 71 行，产品表里还有这两类。
- 解决：在 `preprocess.py` 里写死英文兜底；其余空品类填 `unknown`（源表约 610 个商品本来就没有品类）。
