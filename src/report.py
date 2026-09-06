"""读取 KPI / RFM 汇总，调用 OpenAI 或 Qwen 生成经营总结。"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "ecommerce.duckdb"
OUT_PATH = ROOT / "data" / "processed" / "business_summary.md"

SYSTEM_PROMPT = """你是电商经营分析师。只根据用户提供的数字写中文经营总结，禁止编造或改动任何数字。
必须写明业务当日、GMV 不含运费、利润率为估算（30%）。
结构固定为：1) 当日与当月经营 2) 品类与地区 3) RFM 分层 4) 行动建议（含 At Risk 召回）。
语气简洁，像给负责人的一页简报，不要列表堆砌原始表。"""


def load_facts(con: duckdb.DuckDBPyConnection) -> dict:
    kpi = con.execute("SELECT * FROM kpi_snapshot").fetchdf().iloc[0]
    customers = con.execute("SELECT * FROM customer_overview").fetchdf().iloc[0]
    rfm = con.execute(
        """
        SELECT segment, customers, customer_share_pct, total_gmv, gmv_share_pct,
               avg_recency_days, avg_frequency, avg_monetary
        FROM rfm_segment_summary
        """
    ).fetchdf()
    cats = con.execute(
        """
        SELECT category, gmv, gmv_share
        FROM category_sales
        ORDER BY category_rank
        LIMIT 5
        """
    ).fetchdf()
    states = con.execute(
        """
        SELECT customer_state, gmv, orders, customers
        FROM sales_by_state
        ORDER BY gmv DESC
        LIMIT 5
        """
    ).fetchdf()
    as_of = pd.Timestamp(kpi["as_of_date"]).date().isoformat()
    return {
        "as_of_date": as_of,
        "as_of_month": str(kpi["as_of_month"]),
        "today_gmv": float(kpi["today_gmv"]),
        "today_orders": int(kpi["today_orders"]),
        "today_aov": float(kpi["today_aov"]),
        "month_gmv": float(kpi["month_gmv"]),
        "month_orders": int(kpi["month_orders"]),
        "month_aov": float(kpi["month_aov"]),
        "estimated_margin": float(kpi["month_estimated_margin"]),
        "customers": int(customers["customers"]),
        "repeat_customers": int(customers["repeat_customers"]),
        "repeat_rate": float(customers["repeat_rate"]),
        "rfm": rfm.to_dict(orient="records"),
        "top_categories": cats.to_dict(orient="records"),
        "top_states": states.to_dict(orient="records"),
    }


def facts_to_prompt(facts: dict) -> str:
    rfm_lines = [
        (
            f"- {row['segment']}: 客户 {int(row['customers'])} "
            f"({row['customer_share_pct']}%), GMV {row['total_gmv']} "
            f"({row['gmv_share_pct']}%), 人均最近购买间隔 {row['avg_recency_days']} 天, "
            f"人均订单 {row['avg_frequency']}, 人均 GMV {row['avg_monetary']}"
        )
        for row in facts["rfm"]
    ]
    cat_lines = [
        f"- {row['category']}: GMV {row['gmv']} (占比 {row['gmv_share']})"
        for row in facts["top_categories"]
    ]
    state_lines = [
        f"- {row['customer_state']}: GMV {row['gmv']}, 订单 {int(row['orders'])}, "
        f"客户 {int(row['customers'])}"
        for row in facts["top_states"]
    ]
    return f"""业务当日: {facts['as_of_date']}（当月 {facts['as_of_month']}）
今日 GMV: {facts['today_gmv']}，订单 {facts['today_orders']}，客单价 {facts['today_aov']}
本月 GMV: {facts['month_gmv']}，订单 {facts['month_orders']}，客单价 {facts['month_aov']}
估算利润率: {facts['estimated_margin']}（固定 30% 估算，不是真实净利润）
客户数: {facts['customers']}，复购客户 {facts['repeat_customers']}，复购率 {facts['repeat_rate']}
GMV 口径: 有效订单的 price 之和，不含运费；有效订单排除 canceled / unavailable。

RFM 规则分层:
{chr(10).join(rfm_lines)}

热销品类 Top 5:
{chr(10).join(cat_lines)}

销售州 Top 5:
{chr(10).join(state_lines)}
"""


def offline_summary(facts: dict) -> str:
    """无 API Key 时按同一口径拼一版可核对的简报。"""
    champs = next(r for r in facts["rfm"] if r["segment"] == "Champions")
    at_risk = next(r for r in facts["rfm"] if r["segment"] == "At Risk")
    top_cat = facts["top_categories"][0]
    top_state = facts["top_states"][0]
    return f"""# Olist 经营总结（本地模板，未调用大模型）

业务当日 **{facts['as_of_date']}**。GMV 为有效订单 `price` 合计，不含运费；利润率 30% 为估算。

## 当日与当月

今日 GMV {facts['today_gmv']:.2f}，{facts['today_orders']} 单，客单价 {facts['today_aov']:.2f}。
本月 GMV {facts['month_gmv']:.2f}，{facts['month_orders']} 单，客单价 {facts['month_aov']:.2f}。
客户 {facts['customers']} 人，复购率 {facts['repeat_rate']:.2%}（复购客 {facts['repeat_customers']}）。

## 品类与地区

贡献最高的品类是 {top_cat['category']}（GMV {top_cat['gmv']:.2f}）。
销售最集中的州是 {top_state['customer_state']}（GMV {top_state['gmv']:.2f}）。

## RFM 分层

Champions {int(champs['customers'])} 人，贡献 GMV {champs['total_gmv']:.2f}，人均价值明显高于其他段。
At Risk {int(at_risk['customers'])} 人（{at_risk['customer_share_pct']}%），间隔约 {at_risk['avg_recency_days']} 天，是当前最大的流失风险池。

## 行动建议

优先对 At Risk 做召回（优惠券/复购提醒），对 Champions 做高客单品类（如 watches_gifts）的会员运营。Lost Customers 不宜平均撒预算。填写 `.env` 中的 API Key 后重新运行，可得到模型润色版。
"""


def resolve_provider() -> tuple[str, str, str] | None:
    qwen_key = os.getenv("QWEN_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if qwen_key:
        return (
            qwen_key,
            os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            os.getenv("QWEN_MODEL", "qwen-plus"),
        )
    if openai_key:
        return (
            openai_key,
            os.getenv("OPENAI_BASE_URL") or None,
            os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
    return None


def llm_summary(facts: dict, api_key: str, base_url: str | None, model: str) -> str:
    from openai import OpenAI

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": facts_to_prompt(facts)},
        ],
    )
    text = (resp.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("模型返回空内容")
    header = f"# Olist 经营总结（{model}）\n\n业务当日 **{facts['as_of_date']}**。\n\n"
    return header + text


def main() -> None:
    load_dotenv(ROOT / ".env")
    if not DB_PATH.exists():
        raise FileNotFoundError(f"未找到 {DB_PATH}，先运行 python src/preprocess.py 与 python src/run_sql.py")

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        facts = load_facts(con)
    finally:
        con.close()

    provider = resolve_provider()
    if provider is None:
        print("未检测到 QWEN_API_KEY / OPENAI_API_KEY，写入本地模板摘要。")
        report = offline_summary(facts)
    else:
        api_key, base_url, model = provider
        print(f"调用模型 {model} ...")
        report = llm_summary(facts, api_key, base_url, model)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
