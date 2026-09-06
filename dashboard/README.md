# Power BI 搭建步骤

在 Windows 上用 **Power BI Desktop** 操作。不要直连 `ecommerce.duckdb`（Desktop 没有稳定官方连接器），用已经导出的 CSV。

保存位置：`dashboard/Ecommerce.pbix`（该文件被 git 忽略，只留在本地）。

## 0. 打开前确认

汇总 CSV 已在 `data/processed/`。若缺失，先在仓库根目录运行：

```powershell
.\.venv\Scripts\Activate.ps1
python src/preprocess.py
python src/run_sql.py
python src/rfm.py
```

本步对照值（卡片必须对上）：

- 业务当日 **2018-08-29**
- 今日 GMV **1546.04**，订单 **11**，客单价 **140.55**
- 本月 GMV **848860.10**，订单 **6421**，客单价 **132.20**
- 估算利润率 **30%**

## 1. 新建文件并导入表

1. 打开 Power BI Desktop → 空报告。
2. **获取数据 → 文本/CSV**，逐个导入下面这些文件（不要导入 `fact_sales.csv`，明细太大，看板用汇总即可）。

从 `data/processed/`：

| 文件 | 用途 |
| --- | --- |
| `kpi_snapshot.csv` | 今日/本月 KPI |
| `meta_asof.csv` | 业务当日说明 |
| `sales_trend_monthly.csv` | 月销售趋势 |
| `sales_trend_daily.csv` | 日趋势（可选） |
| `category_sales.csv` | 热销品类 |
| `sales_by_state.csv` | 州销售 |
| `customer_overview.csv` | 客户数/复购 |
| `rfm_segment_summary.csv` | RFM 分段人数与 GMV |
| `rfm_score_heatmap.csv` | R×M 热力 |

从 `dashboard/`：

| 文件 | 用途 |
| --- | --- |
| `brazil_states.csv` | 州缩写 → 地图用全名 |
| `rfm_segment_sort.csv` | 分段显示顺序 |

3. 每个文件点 **转换数据**，确认第一行是标题，再 **关闭并应用**。若列名是 `Column1`、`Column2`，在 Power Query 点 **将第一行用作标题**（`brazil_states`、`rfm_segment_sort` 容易出现）。

## 2. Power Query 里改类型

打开 **转换数据**，按表改：

- `kpi_snapshot`：`as_of_date` → 日期；GMV/订单/客单价 → 小数或整数。
- `sales_trend_monthly`：新增列 `month_date`，公式  
  `Date.FromText([order_month] & "-01")`，类型设为日期。
- `sales_by_state`：`customer_state` 文本；`gmv` 小数。
- `brazil_states`：全部文本。
- `rfm_score_heatmap`：`r_score`、`m_score` 整数。

**关闭并应用**。

## 3. 建关系

**模型** 视图里只建这两条：

1. `sales_by_state[customer_state]` → `brazil_states[state_code]`（多对一）
2. `rfm_segment_summary[segment]` → `rfm_segment_sort[segment]`（多对一）

其余表各自独立，卡片直接用字段，不必硬连。

选中 `rfm_segment_summary[segment]`，功能区 **列工具 → 排序依据** 选 `rfm_segment_sort[sort_order]`。若跨表排序不好用：把 `sort_order` 合并进 `rfm_segment_summary` 后再按该列排序。

## 4. 字段格式

在 **数据** 或 **报表** 视图点字段：

- `today_gmv` / `month_gmv` / `total_gmv` / `gmv`：货币，小数 2 位，符号用 `$` 或 `R$`
- `today_aov` / `month_aov`：货币
- `today_estimated_margin` / `month_estimated_margin`：百分比（源值是 `0.3`）
- `customer_share_pct` / `gmv_share_pct`：这些已经是 38.70 这种百分数，不要再 ×100，自定义格式 `0.00"%"`

## 5. 第 1 页：经营概览

页面名：`Overview`。

顶部放文本框标题：`Olist Ecommerce Dashboard`，副标题用 `meta_asof[as_of_date]` 做成卡片，显示 **As of 2018-08-29**。

**卡片**（字段都来自 `kpi_snapshot`，聚合用“第一个”或求和，该表只有 1 行）：

| 卡片 | 字段 |
| --- | --- |
| 今日 GMV | `today_gmv` |
| 本月 GMV | `month_gmv` |
| 本月订单量 | `month_orders` |
| 本月客单价 | `month_aov` |
| 估算利润率 | `month_estimated_margin` |
| 客户数 | `customer_overview[customers]` |
| 复购率 | `customer_overview[repeat_rate]`（百分比） |

**折线图**：轴 = `sales_trend_monthly[month_date]`，值 = `gmv`。标题：`Monthly GMV`。

**簇状柱形图**：轴 = `category_sales[category]`，值 = `gmv`。筛选器：`category_rank` 小于等于 10。标题：`Top categories`。

**填充地图**：

1. 视觉对象选 **填充地图**
2. 位置 = `brazil_states[map_location]`
3. 色饱和度 = `sales_by_state[gmv]`
4. 若州不上色：位置改用 `state_name_en`，并在筛选器加 `country = Brazil`

不要用地图气泡去绑 `SP`/`RJ`，Bing 认不全缩写。

填充地图依赖 Bing。若灰框提示已禁用，或只亮几秒：先 **文件 → 选项和设置 → 选项 → 全局/当前文件 → 安全性**，勾选使用地图，确定后**完全退出再打开 pbix**，删掉坏掉的图再新建。仍不行就改用普通 **地图**：纬度 `sales_by_state[state_lat]`，经度 `state_lng`，气泡大小 `gmv`。再不行用州柱状图代替，先把 KPI 和趋势做完。

## 6. 第 2 页：RFM 分层

页面名：`RFM`。

**卡片**：从 `rfm_segment_summary` 做三个度量值（或三个筛选后的卡片）：

```dax
Champions Customers = CALCULATE(SUM(rfm_segment_summary[customers]), rfm_segment_summary[segment] = "Champions")
Champions GMV = CALCULATE(SUM(rfm_segment_summary[total_gmv]), rfm_segment_summary[segment] = "Champions")
At Risk Customers = CALCULATE(SUM(rfm_segment_summary[customers]), rfm_segment_summary[segment] = "At Risk")
```

**簇状柱形图**：轴 = `segment`，值 = `customers`。颜色按段区分（Champions 深蓝，Loyal 浅蓝，Potential 绿，At Risk 橙，Lost 红）。

**饼图**：图例 = `segment`，值 = `customers`。

**矩阵（热力）**：行 = `rfm_score_heatmap[m_score]`，列 = `r_score`，值 = `customers`。条件格式 → 背景色，用黄到红。行按 `m_score` 降序，使右上角是高 R 高 M（Champions 区）。

页脚文本框写清口径：规则分层；F 分不是五分位；利润率是估算 30%。

## 7. 保存

另存为：

`D:\Carrer\Project\ecommerce-analysis\dashboard\Ecommerce.pbix`

以后数据重跑，在 Power BI 里点 **刷新**。若提示找不到文件，用 **转换数据 → 数据源设置** 把路径指回 `data/processed/`。
