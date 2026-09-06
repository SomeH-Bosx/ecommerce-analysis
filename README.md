# 一键生成电商经营 Dashboard 与 AI 经营日报

基于 Kaggle [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)。`python main.py` 会依次清洗数据、算 SQL 指标、做 RFM 分层并生成经营总结；再刷新 Power BI 即可看看板。

## 最终用户能看到什么

| 模块 | 口径 |
| --- | --- |
| 今日 / 本月 GMV | 业务当日 = delivered 最晚下单日（**2018-08-29**）；GMV = 有效订单 `price` 之和，不含运费 |
| 订单量、客单价、利润率 | 有效订单排除 canceled / unavailable；客单价 = GMV / 订单数；利润率固定估算 **30%** |
| 销售趋势 | 有效订单按日 / 月汇总 |
| 热销品类 | 英译品类名 + 销量 / GMV |
| 地区地图 | 巴西州级 `customer_state`，地图用全名不使用 SP/RJ 缩写 |
| RFM 分层 | 规则标签：Champions / Loyal / Potential Loyalists / At Risk / Lost。F 分不用五分位（1 单→1，2 单→3，3+→5）。KMeans 只对照 |
| AI 经营总结 | 读 KPI + RFM + 品类 + 州，调用 Qwen 或 OpenAI；无 Key 写本地模板 |

## 固定技术栈

SQL（DuckDB）· Python（Pandas / Matplotlib）· Power BI · OpenAI / Qwen

## 从零运行

Olist 9 张 CSV 放在 `data/raw/`。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
# 编辑 .env，填 QWEN_API_KEY 或 OPENAI_API_KEY（同时填则优先 Qwen）
python main.py
```

`main.py` 等价于依次执行 `src/preprocess.py`、`src/run_sql.py`、`src/rfm.py`、`src/report.py`。聚类对照仍可单独跑 `python src/cluster.py`。

Power BI：按 [dashboard/README.md](dashboard/README.md) 用 `data/processed/*.csv` 打开或刷新本地 `dashboard/Ecommerce.pbix`。

## 核对数字（2018-08-29）

| 指标 | 值 |
| --- | --- |
| 今日 GMV / 订单 / 客单价 | 1546.04 / 11 / 140.55 |
| 本月 GMV / 订单 / 客单价 | 848860.10 / 6421 / 132.20 |
| 估算利润率 | 30% |
| 客户 / 复购客 / 复购率 | 94983 / 2887 / 3.04% |
| RFM 人数 | Champions 957 · Loyal 898 · Potential 36754 · At Risk 37377 · Lost 18997 |
| Top 品类 / Top 州 | health_beauty · SP |

报告输出：`data/processed/business_summary.md`。

## 不入库（本地才有）

`data/raw/*.csv`、`data/processed/*`（含 DuckDB、汇总 CSV、经营总结）、`.env`、`.venv/`、`dashboard/Ecommerce.pbix`

## 项目结构

```
ecommerce-analysis/
├── data/raw/                 # Olist 原始 CSV
├── data/processed/           # 清洗表、汇总、DuckDB、经营总结
├── sql/01–04_*.sql           # KPI / 客户 / 品类 / RFM
├── main.py                   # 一键：清洗 → SQL → RFM → 经营日报
├── src/preprocess.py         # 清洗
├── src/run_sql.py            # 执行 SQL 并导出汇总
├── src/rfm.py / cluster.py   # 规则分层与 KMeans 对照
├── src/report.py             # AI / 本地经营总结
├── notebooks/eda.ipynb
├── dashboard/                # Power BI 步骤与对照表；pbix 仅本地
├── .env.example
├── dev-log.md
└── error.md
```

## Git 分支

功能已全部合入 `main`。历史分支：`feature/data-pipeline` → `sql-analysis` → `rfm-cluster` → `dashboard` → `ai-report`。跨功能文档改在 `main`。

## 开发阶段

0–5 已完成。6. **收口**（本步）：口径、复现步骤、核对表写进 README。
