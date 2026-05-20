"""Correlation matrix service — Pearson correlation & diversification score."""

import json
import math
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.snapshot import Snapshot
from app.schemas.dashboard import CorrelationMatrix, CorrelationPair, DiversificationScore


def _pearson_corr(x: list[float], y: list[float]) -> float:
    """Compute Pearson correlation coefficient between two series."""
    n = len(x)
    if n < 5:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)

    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)


async def get_correlation_matrix(db: AsyncSession) -> CorrelationMatrix | None:
    """Calculate pairwise correlation matrix from snapshot holdings history.

    Uses holdings_json in snapshots to reconstruct per-symbol return series,
    then computes Pearson correlation for each pair.
    """
    # Load recent snapshots (up to 120 trading days)
    result = await db.execute(
        select(Snapshot).order_by(Snapshot.date.desc()).limit(120)
    )
    snapshots = list(reversed(result.scalars().all()))

    if len(snapshots) < 5:
        return None

    # Reconstruct per-symbol market value series from holdings_json
    symbol_series: dict[str, list[float]] = defaultdict(list)
    dates = []

    for snap in snapshots:
        dates.append(str(snap.date))
        try:
            holdings_data = json.loads(snap.holdings_json)
        except (json.JSONDecodeError, TypeError):
            holdings_data = []

        # Build a map of symbol -> market_value for this snapshot
        snap_values: dict[str, float] = {}
        for h in holdings_data:
            symbol = h.get("symbol", "")
            qty = float(h.get("quantity", 0))
            price = float(h.get("latest_price", 0)) or float(h.get("cost_price", 0))
            snap_values[symbol] = qty * price

        # Record values; missing symbols get 0 for this day
        all_symbols = set(symbol_series.keys()) | set(snap_values.keys())
        for sym in all_symbols:
            symbol_series[sym].append(snap_values.get(sym, 0.0))

    # Also load current holdings for symbol->name mapping and weights
    h_result = await db.execute(select(Holding))
    holdings = h_result.scalars().all()

    symbol_names: dict[str, str] = {}
    symbol_values: dict[str, float] = {}

    for h in holdings:
        symbol_names[h.symbol] = h.name
        val = float(h.quantity * h.latest_price) if h.latest_price else float(h.quantity * h.cost_price)
        symbol_values[h.symbol] = val

    # Only include symbols that are in current holdings AND have enough data
    active_symbols = [
        sym for sym in symbol_values
        if sym in symbol_series and len(symbol_series[sym]) >= 5
    ]

    if len(active_symbols) < 2:
        return None

    # Compute return series (daily % change) for each symbol
    return_series: dict[str, list[float]] = {}
    for sym in active_symbols:
        series = symbol_series[sym]
        # Pad shorter series with 0 if needed
        if len(series) < len(snapshots):
            series = [0.0] * (len(snapshots) - len(series)) + series

        rets = []
        for i in range(1, len(series)):
            prev = series[i - 1]
            curr = series[i]
            if prev > 0:
                rets.append((curr - prev) / prev * 100)
            else:
                rets.append(0.0)
        return_series[sym] = rets

    # Compute correlation matrix
    n = len(active_symbols)
    matrix: list[list[float]] = [[0.0] * n for _ in range(n)]
    pairs: list[CorrelationPair] = []

    for i in range(n):
        matrix[i][i] = 1.0
        for j in range(i + 1, n):
            corr = _pearson_corr(return_series[active_symbols[i]], return_series[active_symbols[j]])
            # Clamp to [-1, 1]
            corr = max(-1.0, min(1.0, corr))
            matrix[i][j] = round(corr, 4)
            matrix[j][i] = round(corr, 4)

            is_alert = abs(corr) > 0.7
            pairs.append(
                CorrelationPair(
                    symbol_a=active_symbols[i],
                    name_a=symbol_names.get(active_symbols[i], active_symbols[i]),
                    symbol_b=active_symbols[j],
                    name_b=symbol_names.get(active_symbols[j], active_symbols[j]),
                    correlation=round(corr, 4),
                    is_alert=is_alert,
                )
            )

    # Sort pairs: alert items first, then by abs(correlation) descending
    pairs.sort(key=lambda p: (not p.is_alert, -abs(p.correlation)))

    # Compute diversification score
    total_value = sum(symbol_values[sym] for sym in active_symbols)
    weights = [symbol_values[sym] / total_value for sym in active_symbols] if total_value > 0 else [1.0 / n] * n

    div_score = _compute_diversification_score(matrix, weights, n)

    # Compute risk contributions (marginal contribution to portfolio variance)
    risk_contributions = _compute_risk_contributions(
        return_series, active_symbols, weights, symbol_names
    )

    return CorrelationMatrix(
        symbols=active_symbols,
        symbol_names=[symbol_names.get(s, s) for s in active_symbols],
        matrix=matrix,
        pairs=pairs,
        diversification_score=div_score,
        risk_contributions=risk_contributions,
        period_days=len(snapshots),
    )


def _compute_diversification_score(
    matrix: list[list[float]], weights: list[float], n: int
) -> DiversificationScore:
    """Compute diversification score (0-100).

    Based on the ratio of weighted-average correlation to the
    theoretical maximum (1.0). Lower average correlation = better diversification.
    """
    if n < 2:
        return DiversificationScore(score=0, label="数据不足", avg_correlation=0.0)

    # Weighted average of absolute correlations (upper triangle only)
    total_weight = 0.0
    weighted_corr_sum = 0.0

    for i in range(n):
        for j in range(i + 1, n):
            pair_weight = weights[i] * weights[j]
            weighted_corr_sum += abs(matrix[i][j]) * pair_weight
            total_weight += pair_weight

    avg_corr = weighted_corr_sum / total_weight if total_weight > 0 else 0.0

    # Score: 100 = perfectly uncorrelated, 0 = perfectly correlated
    score = round((1.0 - avg_corr) * 100, 1)
    score = max(0.0, min(100.0, score))

    if score >= 70:
        label = "优秀"
    elif score >= 50:
        label = "良好"
    elif score >= 30:
        label = "一般"
    else:
        label = "较差"

    return DiversificationScore(
        score=score,
        label=label,
        avg_correlation=round(avg_corr, 4),
    )


def _compute_risk_contributions(
    return_series: dict[str, list[float]],
    symbols: list[str],
    weights: list[float],
    symbol_names: dict[str, str],
) -> list[dict]:
    """Compute each holding's marginal risk contribution to portfolio variance."""
    n = len(symbols)
    if n < 2:
        return []

    # Build covariance matrix
    length = min(len(return_series[s]) for s in symbols)
    if length < 5:
        return []

    # Compute mean returns
    means = {}
    for s in symbols:
        rets = return_series[s][-length:]
        means[s] = sum(rets) / length

    # Covariance matrix
    cov_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        rets_i = return_series[symbols[i]][-length:]
        for j in range(i, n):
            rets_j = return_series[symbols[j]][-length:]
            cov = sum(
                (rets_i[k] - means[symbols[i]]) * (rets_j[k] - means[symbols[j]])
                for k in range(length)
            ) / length
            cov_matrix[i][j] = cov
            cov_matrix[j][i] = cov

    # Portfolio variance = w^T * C * w
    port_var = 0.0
    for i in range(n):
        for j in range(n):
            port_var += weights[i] * weights[j] * cov_matrix[i][j]

    # Marginal risk contribution: RC_i = w_i * (C * w)_i / port_var
    contributions = []
    for i in range(n):
        marginal = sum(cov_matrix[i][j] * weights[j] for j in range(n))
        rc = weights[i] * marginal / port_var if port_var > 0 else 0.0
        contributions.append({
            "symbol": symbols[i],
            "name": symbol_names.get(symbols[i], symbols[i]),
            "weight": round(weights[i], 4),
            "risk_contribution": round(rc, 4),
        })

    # Sort by risk contribution descending
    contributions.sort(key=lambda x: x["risk_contribution"], reverse=True)
    return contributions
