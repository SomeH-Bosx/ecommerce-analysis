"""把 sql/01–03 应用到 ecommerce.duckdb，并导出汇总 CSV。"""

from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "ecommerce.duckdb"
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "data" / "processed"
SQL_FILES = ("01_kpi.sql", "02_customer.sql", "03_product.sql")
EXPORT_TABLES = (
    "kpi_snapshot",
    "sales_trend_daily",
    "sales_trend_monthly",
    "customer_overview",
    "sales_by_state",
    "sales_by_city",
    "category_sales",
)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"未找到 {DB_PATH}，先运行 python src/preprocess.py")

    con = duckdb.connect(str(DB_PATH))
    try:
        for name in SQL_FILES:
            con.execute((SQL_DIR / name).read_text(encoding="utf-8"))
        for table in EXPORT_TABLES:
            out = OUT_DIR / f"{table}.csv"
            con.execute(f"COPY {table} TO '{out.as_posix()}' (HEADER, DELIMITER ',')")
        print(con.execute("SELECT * FROM kpi_snapshot").fetchdf().to_string(index=False))
        print(con.execute("SELECT * FROM customer_overview").fetchdf().to_string(index=False))
        print(
            con.execute("SELECT * FROM category_sales ORDER BY category_rank LIMIT 5")
            .fetchdf()
            .to_string(index=False)
        )
    finally:
        con.close()


if __name__ == "__main__":
    main()
