# 一键生成电商经营 Dashboard 与 AI 经营日报

基于 [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 的经营分析项目。一条命令完成清洗、指标、RFM 分层和 AI 日报；用 Power BI 查看看板。

**技术栈：** DuckDB · Pandas · Power BI · OpenAI / Qwen

## 功能

- 今日 / 本月 GMV、订单量、客单价、估算利润率
- 销售趋势、热销品类、巴西州销售地图
- RFM 用户分层（Champions / Loyal / Potential Loyalists / At Risk / Lost）
- AI 自动生成经营总结

## 口径

- 业务当日 = delivered 订单的最晚下单日（本数据集为 **2018-08-29**）
- 有效订单排除 `canceled`、`unavailable`；GMV = `price` 合计，不含运费
- 利润率按 **30%** 估算（源数据无成本）
- RFM 的 F 分：1 单→1，2 单→3，3 单及以上→5（该数据集复购极低，不用五分位）

## 快速开始

1. 将 Olist 的 9 张 CSV 放到 `data/raw/`
2. 安装并运行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python main.py
```

3. 在 `.env` 中填写 `QWEN_API_KEY` 或 `OPENAI_API_KEY`（同时填写时优先 Qwen）。不填 Key 也会生成本地模板日报。
4. 用 Power BI Desktop 打开 `dashboard/Ecommerce.pbix` 并刷新；搭看板步骤见 [dashboard/README.md](dashboard/README.md)。

日报输出：`data/processed/business_summary.md`。

## 预期结果（2018-08-29）

| 指标 | 值 |
| --- | --- |
| 今日 GMV | 1546.04（11 单，客单价 140.55） |
| 本月 GMV | 848,860.10（6421 单，客单价 132.20） |
| 客户 / 复购率 | 94,983 / 3.04% |
| RFM | Champions 957 · At Risk 37,377 · Lost 18,997 |
| Top 品类 / 州 | health_beauty / SP |

原始数据、中间结果、`.env` 和 `.pbix` 仅保存在本地。

## 目录

```
main.py              # 清洗 → SQL → RFM → 日报
src/                 # 预处理、指标、分层、报告
sql/                 # DuckDB 查询
data/raw|processed/  # 输入与输出（不入库）
dashboard/           # Power BI
notebooks/eda.ipynb
```
