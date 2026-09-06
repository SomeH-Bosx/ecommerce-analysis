"""读取 data/raw 的 Olist CSV，清洗后写入 data/processed 与 DuckDB。"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DB_PATH = PROCESSED_DIR / "ecommerce.duckdb"

INVALID_STATUSES = frozenset({"canceled", "unavailable"})
ESTIMATED_GROSS_MARGIN = 0.30
CATEGORY_EN_FALLBACK = {
    "portateis_cozinha_e_preparadores_de_alimentos": "kitchen_portable_and_food_preparers",
    "pc_gamer": "pc_gamer",
}
RAW_FILES = (
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
)


def _require_raw_files() -> None:
    missing = [name for name in RAW_FILES if not (RAW_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(f"缺少原始文件，请放到 {RAW_DIR}: {missing}")


def _read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / name)


def _pad_zip(series: pd.Series) -> pd.Series:
    return series.astype("int64").astype(str).str.zfill(5)


def _to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def load_raw() -> dict[str, pd.DataFrame]:
    _require_raw_files()
    return {
        "customers": _read_csv("olist_customers_dataset.csv"),
        "geolocation": _read_csv("olist_geolocation_dataset.csv"),
        "orders": _read_csv("olist_orders_dataset.csv"),
        "order_items": _read_csv("olist_order_items_dataset.csv"),
        "payments": _read_csv("olist_order_payments_dataset.csv"),
        "reviews": _read_csv("olist_order_reviews_dataset.csv"),
        "products": _read_csv("olist_products_dataset.csv"),
        "sellers": _read_csv("olist_sellers_dataset.csv"),
        "category_translation": _read_csv("product_category_name_translation.csv"),
    }


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["customer_zip_code_prefix"] = _pad_zip(out["customer_zip_code_prefix"])
    out["customer_city"] = out["customer_city"].str.strip().str.lower()
    out["customer_state"] = out["customer_state"].str.strip().str.upper()
    return out


def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["seller_zip_code_prefix"] = _pad_zip(out["seller_zip_code_prefix"])
    out["seller_city"] = out["seller_city"].str.strip().str.lower()
    out["seller_state"] = out["seller_state"].str.strip().str.upper()
    return out


def clean_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    """同一邮编前缀有多条坐标，取均值供地图使用。"""
    out = df.copy()
    out["geolocation_zip_code_prefix"] = _pad_zip(out["geolocation_zip_code_prefix"])
    out["geolocation_city"] = out["geolocation_city"].str.strip().str.lower()
    out["geolocation_state"] = out["geolocation_state"].str.strip().str.upper()
    return (
        out.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(
            geolocation_lat=("geolocation_lat", "mean"),
            geolocation_lng=("geolocation_lng", "mean"),
            geolocation_city=("geolocation_city", "first"),
            geolocation_state=("geolocation_state", "first"),
        )
    )


def clean_products(products: pd.DataFrame, translation: pd.DataFrame) -> pd.DataFrame:
    out = products.rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    )
    trans = translation.copy()
    extra = pd.DataFrame(
        list(CATEGORY_EN_FALLBACK.items()),
        columns=["product_category_name", "product_category_name_english"],
    )
    trans = pd.concat([trans, extra], ignore_index=True).drop_duplicates(
        subset=["product_category_name"], keep="first"
    )
    out = out.merge(trans, on="product_category_name", how="left")
    out["product_category_name"] = out["product_category_name"].fillna("unknown")
    out["product_category_name_english"] = out["product_category_name_english"].fillna(
        "unknown"
    )
    return out


def clean_orders(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp]:
    out = df.copy()
    time_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in time_cols:
        out[col] = _to_datetime(out[col])

    out["is_valid_order"] = ~out["order_status"].isin(INVALID_STATUSES)
    delivered = out.loc[out["order_status"] == "delivered", "order_purchase_timestamp"]
    if delivered.empty:
        raise ValueError("没有 delivered 订单，无法确定业务当日")
    as_of_ts = delivered.max()

    out["order_purchase_date"] = out["order_purchase_timestamp"].dt.normalize()
    out["order_purchase_month"] = out["order_purchase_timestamp"].dt.to_period("M").astype(str)
    as_of_date = as_of_ts.normalize()
    as_of_month = as_of_ts.to_period("M").strftime("%Y-%m")
    out["is_as_of_day"] = out["order_purchase_date"] == as_of_date
    out["is_as_of_month"] = out["order_purchase_month"] == as_of_month
    out["delivery_days"] = (
        out["order_delivered_customer_date"] - out["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    return out, as_of_ts


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["shipping_limit_date"] = _to_datetime(out["shipping_limit_date"])
    out["gmv"] = out["price"]
    out["estimated_profit"] = (out["price"] * ESTIMATED_GROSS_MARGIN).round(2)
    out["estimated_cost"] = (out["price"] * (1 - ESTIMATED_GROSS_MARGIN)).round(2)
    return out


def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["review_creation_date"] = _to_datetime(out["review_creation_date"])
    out["review_answer_timestamp"] = _to_datetime(out["review_answer_timestamp"])
    return out


def build_fact_sales(
    orders: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    sales = items.merge(orders, on="order_id", how="inner")
    sales = sales.merge(
        products[
            [
                "product_id",
                "product_category_name",
                "product_category_name_english",
            ]
        ],
        on="product_id",
        how="left",
    )
    sales = sales.merge(
        customers[
            [
                "customer_id",
                "customer_unique_id",
                "customer_city",
                "customer_state",
                "customer_zip_code_prefix",
            ]
        ],
        on="customer_id",
        how="left",
    )
    sales = sales.merge(
        sellers[["seller_id", "seller_city", "seller_state"]],
        on="seller_id",
        how="left",
    )
    sales["product_category_name_english"] = sales[
        "product_category_name_english"
    ].fillna("unknown")
    return sales


def build_meta(as_of_ts: pd.Timestamp, tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of_ts": as_of_ts,
                "as_of_date": as_of_ts.normalize(),
                "as_of_month": as_of_ts.to_period("M").strftime("%Y-%m"),
                "as_of_rule": "max(order_purchase_timestamp) among delivered orders",
                "gmv_rule": "sum(price) on items of orders not canceled/unavailable",
                "estimated_gross_margin": ESTIMATED_GROSS_MARGIN,
                "fact_sales_rows": len(tables["fact_sales"]),
                "fact_orders_rows": len(tables["fact_orders"]),
                "valid_orders": int(tables["fact_orders"]["is_valid_order"].sum()),
            }
        ]
    )


def write_outputs(tables: dict[str, pd.DataFrame]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = duckdb.connect(str(DB_PATH))
    try:
        for name, frame in tables.items():
            frame.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
            con.register("_tmp", frame)
            con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM _tmp')
            con.unregister("_tmp")
    finally:
        con.close()


def main() -> None:
    raw = load_raw()
    customers = clean_customers(raw["customers"])
    sellers = clean_sellers(raw["sellers"])
    geolocation = clean_geolocation(raw["geolocation"])
    products = clean_products(raw["products"], raw["category_translation"])
    orders, as_of_ts = clean_orders(raw["orders"])
    items = clean_order_items(raw["order_items"])
    payments = clean_payments(raw["payments"])
    reviews = clean_reviews(raw["reviews"])
    fact_sales = build_fact_sales(orders, items, products, customers, sellers)

    tables = {
        "dim_customers": customers,
        "dim_sellers": sellers,
        "dim_geolocation": geolocation,
        "dim_products": products,
        "fact_orders": orders,
        "fact_order_items": items,
        "fact_payments": payments,
        "fact_reviews": reviews,
        "fact_sales": fact_sales,
    }
    tables["meta_asof"] = build_meta(as_of_ts, tables)
    write_outputs(tables)

    meta = tables["meta_asof"].iloc[0]
    print(f"as_of_date={meta['as_of_date'].date()}  as_of_month={meta['as_of_month']}")
    print(
        f"orders={meta['fact_orders_rows']}  valid={meta['valid_orders']}  "
        f"fact_sales={meta['fact_sales_rows']}"
    )
    print(f"wrote CSV + DuckDB -> {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
