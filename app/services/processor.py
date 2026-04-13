import numpy as np
from typing import List, Dict, Any


def compute_metrics(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute metrics without pandas - pure Python/numpy"""
    if not data:
        return data

    data = [d.copy() for d in data]

    closes = np.array([d.get("close", d.get("Close", 0)) for d in data])
    opens = np.array([d.get("open", d.get("Open", 0)) for d in data])

    daily_returns = (closes - opens) / np.where(opens > 0, opens, 1)

    for i, d in enumerate(data):
        d["daily_return"] = float(daily_returns[i])

        window_7 = max(0, i - 6)
        d["moving_avg_7d"] = float(np.mean(closes[window_7 : i + 1])) if i >= 0 else 0

        d["week52_high"] = float(np.max(closes[: i + 1])) if i > 0 else float(closes[i])
        d["week52_low"] = float(np.min(closes[: i + 1])) if i > 0 else float(closes[i])

        if i >= 29:
            window_30 = daily_returns[i - 29 : i + 1]
            d["volatility_score"] = float(np.std(window_30) * np.sqrt(30))
        else:
            window_30 = daily_returns[: i + 1]
            d["volatility_score"] = (
                float(np.std(window_30) * np.sqrt(30)) if len(window_30) > 1 else 0.0
            )

    return data
