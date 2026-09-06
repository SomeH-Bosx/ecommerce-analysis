# 开发日志

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
