"""执行 04_rfm.sql，导出 RFM 表并画出规则分层分布。"""

from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "ecommerce.duckdb"
SQL_PATH = ROOT / "sql" / "04_rfm.sql"
OUT_DIR = ROOT / "data" / "processed"
EXPORT_TABLES = ("rfm_customers", "rfm_segment_summary", "rfm_score_heatmap")
SEGMENT_ORDER = [
    "Champions",
    "Loyal Customers",
    "Potential Loyalists",
    "At Risk",
    "Lost Customers",
]
SEGMENT_COLORS = {
    "Champions": "#1e3a5f",
    "Loyal Customers": "#4a90c8",
    "Potential Loyalists": "#3d8b5a",
    "At Risk": "#e07a2f",
    "Lost Customers": "#c0392b",
}


def apply_rfm_sql(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(SQL_PATH.read_text(encoding="utf-8"))
    for table in EXPORT_TABLES:
        out = OUT_DIR / f"{table}.csv"
        con.execute(f"COPY {table} TO '{out.as_posix()}' (HEADER, DELIMITER ',')")


def plot_segments(summary: pd.DataFrame, path: Path) -> None:
    frame = summary.set_index("segment").reindex(SEGMENT_ORDER).dropna(how="all")
    colors = [SEGMENT_COLORS[name] for name in frame.index]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].bar(frame.index, frame["customers"], color=colors)
    axes[0].set_title("RFM customers by segment")
    axes[0].set_ylabel("Customers")
    axes[0].tick_params(axis="x", rotation=25)
    axes[1].bar(frame.index, frame["total_gmv"], color=colors)
    axes[1].set_title("RFM GMV by segment")
    axes[1].set_ylabel("GMV")
    axes[1].tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"未找到 {DB_PATH}，先运行 python src/preprocess.py")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    try:
        apply_rfm_sql(con)
        summary = con.execute("SELECT * FROM rfm_segment_summary").fetchdf()
        print(summary.to_string(index=False))
    finally:
        con.close()

    plot_segments(summary, OUT_DIR / "rfm_segment_counts.png")
    print(f"wrote RFM tables + {OUT_DIR / 'rfm_segment_counts.png'}")


if __name__ == "__main__":
    main()
