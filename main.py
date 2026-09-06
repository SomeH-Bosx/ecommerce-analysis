"""一键跑完清洗、SQL 汇总、RFM 分层和经营日报。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = (
    ROOT / "src" / "preprocess.py",
    ROOT / "src" / "run_sql.py",
    ROOT / "src" / "rfm.py",
    ROOT / "src" / "report.py",
)


def main() -> None:
    for script in STEPS:
        print(f"\n=== {script.relative_to(ROOT)} ===")
        result = subprocess.run([sys.executable, str(script)], cwd=ROOT)
        if result.returncode != 0:
            raise SystemExit(f"失败：{script.name}（退出码 {result.returncode}）")
    print("\n完成。请刷新 dashboard/Ecommerce.pbix")


if __name__ == "__main__":
    main()
