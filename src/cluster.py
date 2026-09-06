"""对 RFM 原值做 KMeans(k=5)，并与规则分层交叉对照。"""

from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "ecommerce.duckdb"
OUT_DIR = ROOT / "data" / "processed"
CLUSTER_NAMES = [
    "Champions-like",
    "Loyal-like",
    "Potential-like",
    "AtRisk-like",
    "Lost-like",
]
SEGMENT_ORDER = [
    "Champions",
    "Loyal Customers",
    "Potential Loyalists",
    "At Risk",
    "Lost Customers",
]


def _label_clusters(centers: np.ndarray) -> dict[int, str]:
    """按 -Recency + Frequency + Monetary 的中心得分从高到低命名。"""
    value_score = -centers[:, 0] + centers[:, 1] + centers[:, 2]
    order = np.argsort(-value_score)
    return {int(cluster_id): CLUSTER_NAMES[rank] for rank, cluster_id in enumerate(order)}


def fit_clusters(rfm: pd.DataFrame) -> pd.DataFrame:
    features = np.column_stack(
        [
            rfm["recency_days"].to_numpy(dtype=float),
            np.log1p(rfm["frequency"].to_numpy(dtype=float)),
            np.log1p(rfm["monetary"].to_numpy(dtype=float)),
        ]
    )
    scaled = StandardScaler().fit_transform(features)
    model = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_id = model.fit_predict(scaled)
    names = _label_clusters(model.cluster_centers_)
    out = rfm[["customer_unique_id", "segment", "recency_days", "frequency", "monetary"]].copy()
    out["cluster_id"] = cluster_id
    out["cluster_label"] = out["cluster_id"].map(names)
    return out


def plot_compare(compare: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    compare.plot(kind="bar", stacked=True, ax=ax)
    ax.set_title("Rule segment vs KMeans label")
    ax.set_xlabel("RFM rule segment")
    ax.set_ylabel("Customers")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(title="cluster", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"未找到 {DB_PATH}，先运行 python src/preprocess.py")

    con = duckdb.connect(str(DB_PATH))
    try:
        rfm = con.execute("SELECT * FROM rfm_customers").fetchdf()
        if rfm.empty:
            raise RuntimeError("rfm_customers 为空，先运行 python src/rfm.py")

        labeled = fit_clusters(rfm)
        con.register("_clusters", labeled)
        con.execute("CREATE OR REPLACE TABLE rfm_clusters AS SELECT * FROM _clusters")
        con.unregister("_clusters")
        con.execute(
            f"COPY rfm_clusters TO '{(OUT_DIR / 'rfm_clusters.csv').as_posix()}' "
            "(HEADER, DELIMITER ',')"
        )

        compare = pd.crosstab(labeled["segment"], labeled["cluster_label"])
        compare = compare.reindex(index=SEGMENT_ORDER, columns=CLUSTER_NAMES).fillna(0)
        compare.to_csv(OUT_DIR / "rfm_cluster_compare.csv")
        plot_compare(compare, OUT_DIR / "rfm_cluster_compare.png")
        print(compare.to_string())
    finally:
        con.close()

    print(f"wrote {OUT_DIR / 'rfm_clusters.csv'} + compare table/png")


if __name__ == "__main__":
    main()
