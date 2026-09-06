# 开发日志

## [2026-09-06] 记录新版卡片无法关闭「千」

- 做了什么：对照用户格式面板，确认新版 Card 没有可用的显示单位项，改为用 FORMAT 度量值出原值。
- 修改文件：
  - `error.md`：记录 1.55 千与 FORMAT 绕过办法
  - `dev-log.md`：本步日志

## [2026-09-06] 记录填充地图启用后仍灰屏

- 做了什么：对照用户截图，确认是 Bing 地图安全策略/网络问题，不是字段拖错。
- 修改文件：
  - `error.md`：记录 `FilledMapVisualNotEnabled` 与备用绑法
  - `dashboard/README.md`：补充重启、经纬度地图、州柱状图备选
  - `dev-log.md`：本步日志

## [2026-09-06] 记录 Power BI 未提升表头

- 做了什么：对照用户导入界面，确认 `brazil_states.csv` 文件本身有表头；在说明和踩坑里补上「将第一行用作标题」。
- 修改文件：
  - `dashboard/README.md`：导入步骤补充未识别列名时的处理
  - `error.md`：记录 Column1 现象与解决办法
  - `dev-log.md`：本步日志

## [2026-09-06] 写出 Power BI 搭建步骤与州名对照

- 做了什么：在 `feature/dashboard` 写好 Desktop 操作说明，并补巴西州名、RFM 排序对照表。`.pbix` 需在 Power BI Desktop 里手工保存。
- 修改文件：
  - `dashboard/README.md`：从导入到两页视觉对象的具体步骤
  - `dashboard/brazil_states.csv`：州缩写到地图全名
  - `dashboard/rfm_segment_sort.csv`：分段显示顺序
  - `README.md`：指向 Dashboard 说明
  - `dev-log.md`：本步日志

## [2026-09-06] 实现 RFM 规则分层与 KMeans 对照

- 做了什么：在 `feature/rfm-cluster` 完成 RFM 打分、五段业务标签、KMeans 对照和 EDA 笔记本；已跑通并写出汇总表。
- 修改文件：
  - `sql/04_rfm.sql`：客户 RFM、分段汇总、R×M 热力表
  - `src/rfm.py`：执行 RFM SQL、导出 CSV、画分层分布图
  - `src/cluster.py`：KMeans(k=5) 与规则分层交叉表
  - `src/run_sql.py`：把 `04_rfm.sql` 纳入统一执行
  - `notebooks/eda.ipynb`：趋势、品类/地区、RFM、聚类对照
  - `README.md`：补充 RFM 运行命令和分段人数
  - `error.md`：asof 关键字、Frequency 五分位失效、聚类与规则不对齐
  - `dev-log.md`：本步日志

## [2026-09-06] 编写 KPI / 客户 / 品类 SQL 并落库

- 做了什么：在 `feature/sql-analysis` 写完三份分析 SQL，用 `run_sql.py` 在 DuckDB 建汇总表并导出 CSV。数字与预处理核对一致。
- 修改文件：
  - `sql/01_kpi.sql`：今日/本月 KPI 快照，以及日/月销售趋势
  - `sql/02_customer.sql`：客户复购概览、州/城市销售（含坐标）
  - `sql/03_product.sql`：热销品类排名、GMV 占比
  - `src/run_sql.py`：按顺序执行上述 SQL 并导出汇总 CSV
  - `README.md`：补充运行命令、汇总表和核对值
  - `error.md`：记录城市名对不齐导致部分城市无坐标
  - `dev-log.md`：本步日志

## [2026-09-06] 实现数据预处理并写出 processed / DuckDB

- 做了什么：实现 `src/preprocess.py`，清洗 9 张 Olist 表，约定业务当日与估算毛利，写出星型表 + `fact_sales` 宽表到 CSV 和 DuckDB。已跑通：as-of 2018-08-29，当日有效 GMV 1546.04，当月 848860.10。
- 修改文件：
  - `src/preprocess.py`：读取 raw、清洗、写 `data/processed` 与 `ecommerce.duckdb`
  - `README.md`：更新口径、运行命令和 Phase 1 状态
  - `error.md`：补业务当日取 delivered、毛利率 30%、缺英译品类
  - `dev-log.md`：本步日志
  - `data/processed/*.csv`、`data/processed/ecommerce.duckdb`：本地产物，不入库

## [2026-09-06] 确认依赖未装成功

- 做了什么：核对终端安装日志和 venv 导入结果，结论是 `pip install -r requirements.txt` 失败，预处理还不能跑。
- 修改文件：
  - `error.md`：记录 pip/distlib `t64.exe` 与 `~ip` 残留导致的半残 venv

## [2026-09-06] 补充分支规则并归位 Olist 原始数据

- 做了什么：新增 Git 分支/提交规则；把 `archive/` 下 9 张 Olist CSV 挪到 `data/raw/` 后删除 `archive/`；README 补上分支规划。
- 修改文件：
  - `.cursor/rules/git-branch-commit.mdc`：完成一块功能后必须给出分支指令和 Conventional Commit
  - `data/raw/olist_customers_dataset.csv`：客户主数据（从 archive 迁入）
  - `data/raw/olist_geolocation_dataset.csv`：经纬度与邮编
  - `data/raw/olist_orders_dataset.csv`：订单头与时间状态
  - `data/raw/olist_order_items_dataset.csv`：订单行（价格、运费）
  - `data/raw/olist_order_payments_dataset.csv`：支付
  - `data/raw/olist_order_reviews_dataset.csv`：评价
  - `data/raw/olist_products_dataset.csv`：商品与品类
  - `data/raw/olist_sellers_dataset.csv`：卖家
  - `data/raw/product_category_name_translation.csv`：品类葡英对照
  - `archive/`：已删除，避免根目录多一层无关目录
  - `README.md`：补充分支规划和“数据已就位”说明
  - `dev-log.md`：本步日志

## [2026-09-06] 脚手架：明确任务并建立项目结构

- 做了什么：对齐开发任务、目标与分阶段规划；按约定搭好目录、Cursor 规则、日志模板和占位文件，未下载数据、未写业务逻辑。
- 修改文件：
  - `.cursor/rules/dev-step-log.mdc`：每完成一步必须向用户汇报并写入本日志
  - `.cursor/rules/error-log.mdc`：遇到坑必须写入 `error.md`
  - `.gitignore`：忽略原始数据、密钥、虚拟环境和 Power BI 二进制
  - `requirements.txt`：固定技术栈的 Python 依赖清单
  - `.env.example`：OpenAI / Qwen 环境变量模板
  - `data/raw/.gitkeep`、`data/processed/.gitkeep`：占住数据目录
  - `sql/01_kpi.sql`：经营核心指标查询占位
  - `sql/02_customer.sql`：客户与地区查询占位
  - `sql/03_product.sql`：商品与品类查询占位
  - `sql/04_rfm.sql`：RFM 分层查询占位
  - `src/__init__.py`：Python 包标识
  - `src/preprocess.py`：原始数据清洗入口占位
  - `src/rfm.py`：RFM 打分与分层入口占位
  - `src/cluster.py`：RFM 聚类入口占位
  - `src/report.py`：AI 经营总结入口占位
  - `notebooks/eda.ipynb`：EDA 笔记本占位
  - `dashboard/.gitkeep`：Power BI 目录占位（`.pbix` 后续在 Power BI 中创建）
  - `README.md`：项目目标、口径、阶段和结构说明
  - `error.md`：踩坑记录模板，并写入规划阶段已确认的两条数据硬约束
  - `dev-log.md`：本开发日志
