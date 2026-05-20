"""Tests for dashboard risk metrics and sector allocation services."""

from decimal import Decimal

import pytest

from app.models.holding import Holding
from app.models.snapshot import Snapshot
from app.services.dashboard import (
    get_risk_metrics,
    get_sector_allocation,
)


# ---------------------------------------------------------------------------
# Risk Metrics Tests
# ---------------------------------------------------------------------------


class TestGetRiskMetrics:
    """Test get_risk_metrics() calculation correctness."""

    @pytest.mark.asyncio
    async def test_returns_none_when_insufficient_data(self, db_session):
        """Less than 5 snapshots with daily_return → None."""
        # No snapshots → None
        result = await get_risk_metrics(db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_calculates_max_drawdown(self, db_session):
        """Max drawdown should reflect the largest peak-to-trough decline."""
        # Create snapshots: values go up then crash
        values = [100000, 105000, 110000, 95000, 90000, 92000, 98000]
        for i, val in enumerate(values):
            daily_ret = None
            if i > 0:
                daily_ret = float((val - values[i - 1]) / values[i - 1] * 100)
            snap = Snapshot(
                date=f"2025-01-{10 + i:02d}",
                total_market_value=Decimal(str(val)),
                total_cost=Decimal("80000"),
                total_profit_loss=Decimal(str(val - 80000)),
                daily_return=daily_ret,
                holdings_json="[]",
            )
            db_session.add(snap)
        await db_session.commit()

        result = await get_risk_metrics(db_session)
        assert result is not None
        # Peak at 110000, trough at 90000 → drawdown = (110000-90000)/110000 = 18.18%
        assert result.max_drawdown > 15  # should be ~18.18
        assert result.max_drawdown < 20

    @pytest.mark.asyncio
    async def test_calculates_sharpe_ratio(self, db_session):
        """Sharpe ratio should be (annualized_return - risk_free) / annual_vol."""
        # Simulate 10 trading days with known returns
        returns = [0.5, -0.3, 0.8, 0.1, -0.2, 0.4, 0.3, -0.1, 0.6, 0.2]
        base_value = 100000
        values = [base_value]
        for r in returns:
            values.append(base_value * (1 + r / 100))

        for i in range(len(values)):
            daily_ret = returns[i - 1] if i > 0 else 0.0
            snap = Snapshot(
                date=f"2025-02-{10 + i:02d}",
                total_market_value=Decimal(str(int(values[i]))),
                total_cost=Decimal("80000"),
                total_profit_loss=Decimal(str(int(values[i] - 80000))),
                daily_return=daily_ret,
                holdings_json="[]",
            )
            db_session.add(snap)
        await db_session.commit()

        result = await get_risk_metrics(db_session)
        assert result is not None
        assert isinstance(result.sharpe_ratio, float)
        assert result.period_days == 10

    @pytest.mark.asyncio
    async def test_var_95_is_positive(self, db_session):
        """VaR 95% should always be a positive number (potential loss)."""
        # Create 20 days of mostly negative returns
        returns = [-1.0, -0.5, 0.3, -2.0, -1.5, 0.1, -0.8, -0.3, 0.5, -1.2,
                   -0.7, 0.2, -0.9, -1.1, 0.4, -0.6, -1.3, 0.1, -0.4, -0.8]
        base_value = 100000
        values = [base_value]
        for r in returns:
            values.append(base_value * (1 + r / 100))

        for i in range(len(values)):
            daily_ret = returns[i - 1] if i > 0 else 0.0
            snap = Snapshot(
                date=f"2025-03-{1 + i:02d}",
                total_market_value=Decimal(str(int(values[i]))),
                total_cost=Decimal("80000"),
                total_profit_loss=Decimal(str(int(values[i] - 80000))),
                daily_return=daily_ret,
                holdings_json="[]",
            )
            db_session.add(snap)
        await db_session.commit()

        result = await get_risk_metrics(db_session)
        assert result is not None
        assert result.var_95 > 0  # positive number = potential loss


# ---------------------------------------------------------------------------
# Sector Allocation Tests
# ---------------------------------------------------------------------------


class TestGetSectorAllocation:
    """Test get_sector_allocation() calculation correctness."""

    @pytest.mark.asyncio
    async def test_empty_holdings(self, db_session):
        """No holdings → empty list."""
        result = await get_sector_allocation(db_session)
        assert result == []

    @pytest.mark.asyncio
    async def test_groups_by_sector(self, db_session):
        """Holdings should be grouped by their sector field."""
        h1 = Holding(
            symbol="sh600519", name="贵州茅台", asset_type="股票",
            sector="食品饮料", quantity=Decimal("10"), cost_price=Decimal("1800"),
            account="主账户",
        )
        h2 = Holding(
            symbol="sh601318", name="中国平安", asset_type="股票",
            sector="非银金融", quantity=Decimal("100"), cost_price=Decimal("50"),
            account="主账户",
        )
        h3 = Holding(
            symbol="sz000858", name="五粮液", asset_type="股票",
            sector="食品饮料", quantity=Decimal("20"), cost_price=Decimal("150"),
            account="主账户",
        )
        db_session.add_all([h1, h2, h3])
        await db_session.commit()

        result = await get_sector_allocation(db_session)
        assert len(result) == 2  # two sectors

        food = next(r for r in result if r.sector == "食品饮料")
        assert food.holdings_count == 2
        assert food.percentage > 0

        finance = next(r for r in result if r.sector == "非银金融")
        assert finance.holdings_count == 1

    @pytest.mark.asyncio
    async def test_uncategorized_when_no_sector(self, db_session):
        """Holdings without sector go to '未分类'."""
        h = Holding(
            symbol="sz159919", name="300ETF", asset_type="基金",
            sector=None, quantity=Decimal("1000"), cost_price=Decimal("4"),
            account="主账户",
        )
        db_session.add(h)
        await db_session.commit()

        result = await get_sector_allocation(db_session)
        assert len(result) == 1
        assert result[0].sector == "未分类"
        assert result[0].holdings_count == 1

    @pytest.mark.asyncio
    async def test_percentages_sum_to_100(self, db_session):
        """All sector percentages should sum to ~100%."""
        holdings = [
            Holding(symbol="sh600519", name="茅台", asset_type="股票",
                    sector="食品饮料", quantity=Decimal("10"), cost_price=Decimal("1800")),
            Holding(symbol="sh601318", name="平安", asset_type="股票",
                    sector="非银金融", quantity=Decimal("100"), cost_price=Decimal("50")),
            Holding(symbol="sz000858", name="五粮液", asset_type="股票",
                    sector="食品饮料", quantity=Decimal("20"), cost_price=Decimal("150")),
        ]
        db_session.add_all(holdings)
        await db_session.commit()

        result = await get_sector_allocation(db_session)
        total_pct = sum(r.percentage for r in result)
        assert abs(total_pct - 100.0) < 0.1
