# 电商经营数据分析 Dashboard

基于 Kaggle [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 的经营分析项目。最终交付是 Power BI Dashboard，辅以 SQL 指标层、Python 分层/聚类，以及 OpenAI / Qwen 自动经营总结。

## 最终用户能看到什么

| 模块 | 含义 | 数据口径 |
| --- | --- | --- |
| 今日 / 本月 GMV | 成交总额 | 业务当日 = delivered 最晚下单日（2018-08-29）；GMV = 有效订单的 `price` 之和 |
| 订单量、客单价、利润率 | 规模、客单、盈利能力 | 有效订单不含 canceled / unavailable；估算毛利率 30% |
| 销售趋势 | 时间序列 | 按日 / 月订单与 GMV |
| 热销品类 | 品类贡献 | 英译品类名 + 销量 / GMV |
| 地区销售地图 | 地理分布 | 巴西州级（`customer_state`） |
| RFM 用户分层 | 价值分层 | Champions / Loyal / Potential Loyalists / At Risk / Lost |
| AI 经营总结 | 自动解读 | 由 KPI + RFM 汇总生成短文 |

## 固定技术栈

- SQL：DuckDB（分析查询）/ SQLite（可选落盘）
- Python：Pandas + Matplotlib（清洗、RFM、聚类、出图）
- Power BI：`dashboard/Ecommerce.pbix`（交互看板）
- OpenAI / Qwen：`src/report.py` 生成经营报告

## 项目结构

```
ecommerce-analysis/
├── data/raw/              # Olist 原始 CSV（不入库）
├── data/processed/        # 清洗后的表与汇总
├── sql/                   # KPI / 客户 / 商品 / RFM 查询
├── notebooks/eda.ipynb    # 探索性分析
├── src/                   # 预处理、RFM、聚类、AI 报告
├── dashboard/             # Power BI 文件（后续手工创建）
├── .cursor/rules/         # 开发日志与踩坑记录规则
├── dev-log.md             # 开发日志
├── error.md               # 踩坑记录
└── README.md
```

## Git 分支

```
main
├── feature/data-pipeline    # 数据接入与清洗
├── feature/sql-analysis     # SQL 指标
├── feature/rfm-cluster      # RFM 与聚类
├── feature/dashboard        # Power BI
└── feature/ai-report        # AI 经营报告
```

跨功能的规则和脚手架改动提交在 `main`。

## 开发阶段

0. **脚手架**（已完成）：目录、规则、日志、占位脚本
1. **数据接入**（已完成）：`src/preprocess.py` 写出 `data/processed/*.csv` 与 `ecommerce.duckdb`
2. **SQL 指标**（已完成）：`01_kpi.sql` / `02_customer.sql` / `03_product.sql`，用 `python src/run_sql.py` 写入 DuckDB 并导出汇总 CSV
3. **用户分层**（已完成）：`04_rfm.sql` + `rfm.py` + `cluster.py` + `notebooks/eda.ipynb`
4. **Power BI**（进行中）：按 `dashboard/README.md` 用汇总 CSV 搭 `Ecommerce.pbix`
5. **AI 报告**：`report.py` 读取汇总，调用 OpenAI 或 Qwen
6. **收口**：口径说明、README 运行步骤、回归核对数字

## 已知数据约束（规划阶段已确认）

1. Olist 是 2016–2018 历史单。业务当日 = delivered 订单的 `max(order_purchase_timestamp)`，当前为 **2018-08-29**。
2. 没有商品成本。估算毛利率固定 **30%**：`estimated_profit = price * 0.30`。GMV 只用 `price`，不含运费。
3. 有效订单：`order_status` 不是 `canceled` / `unavailable`。

## 本地准备

Olist 9 张原始 CSV 已在 `data/raw/`（不入库）。

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src/preprocess.py
python src/run_sql.py
python src/rfm.py
python src/cluster.py
```

清洗结果在 `data/processed/`（CSV + `ecommerce.duckdb`，不入库）。明细表：`fact_sales`、`fact_orders`、`dim_*`、`meta_asof`。汇总表：`kpi_snapshot`、`sales_trend_daily` / `monthly`、`customer_overview`、`sales_by_state` / `city`、`category_sales`、`rfm_customers`、`rfm_segment_summary`、`rfm_clusters`。

RFM 看板用规则标签：Champions 957 人 / Loyal 898 / Potential Loyalists 36754 / At Risk 37377 / Lost 18997。KMeans 五簇只作对照。

业务当日 2018-08-29 的核对值：当日 GMV 1546.04（11 单，客单价 140.55）；当月 GMV 848860.10（6421 单，客单价 132.20）。估算利润率恒为 30%。

API Key 复制 `.env.example` 为 `.env`。
