"""Tests for correlation matrix and rebalance services."""

import math
from decimal import Decimal

from app.services.correlation import _pearson_corr
from app.services.rebalance import _compute_trade_costs, _get_redemption_fee, _get_dividend_tax


class TestPearsonCorrelation:
    """Test the Pearson correlation helper."""

    def test_perfect_positive_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        assert abs(_pearson_corr(x, y) - 1.0) < 0.001

    def test_perfect_negative_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]
        assert abs(_pearson_corr(x, y) - (-1.0)) < 0.001

    def test_no_correlation(self):
        # Zero variance -> returns 0
        x = [5.0, 5.0, 5.0, 5.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert _pearson_corr(x, y) == 0.0

    def test_insufficient_data(self):
        x = [1.0, 2.0]
        y = [3.0, 4.0]
        assert _pearson_corr(x, y) == 0.0


class TestTradeCosts:
    """Test trade cost calculation for rebalance."""

    def test_stock_buy_commission_only(self):
        cost = _compute_trade_costs("买入", Decimal("100000"), "股票")
        assert cost.stamp_tax == Decimal("0")
        assert cost.commission > 0
        assert cost.redemption_fee == Decimal("0")
        assert cost.dividend_tax == Decimal("0")
        assert cost.total_cost == cost.commission

    def test_stock_sell_stamp_tax(self):
        cost = _compute_trade_costs("卖出", Decimal("100000"), "股票", holding_days=400)
        assert cost.stamp_tax == Decimal("50.00")  # 100000 * 0.0005
        assert cost.commission > 0
        assert cost.dividend_tax == Decimal("0")  # >1年免红利税

    def test_stock_sell_short_holding_dividend_tax(self):
        cost = _compute_trade_costs("卖出", Decimal("100000"), "股票", holding_days=15)
        assert cost.stamp_tax > 0
        assert cost.dividend_tax > 0  # <1个月，红利税20%

    def test_fund_redemption_fee_short(self):
        cost = _compute_trade_costs("卖出", Decimal("100000"), "基金", holding_days=5)
        assert cost.redemption_fee > 0  # <7天: 1.5%
        assert cost.stamp_tax == Decimal("0")

    def test_fund_redemption_fee_long(self):
        cost = _compute_trade_costs("卖出", Decimal("100000"), "基金", holding_days=800)
        assert cost.redemption_fee == Decimal("0.00")  # >2年: 0%

    def test_bond_low_commission(self):
        cost = _compute_trade_costs("买入", Decimal("100000"), "债券")
        assert cost.commission > 0
        assert cost.stamp_tax == Decimal("0")

    def test_cash_no_cost(self):
        cost = _compute_trade_costs("买入", Decimal("100000"), "现金")
        assert cost.total_cost == Decimal("0.00")

    def test_min_commission(self):
        cost = _compute_trade_costs("买入", Decimal("100"), "股票")
        assert cost.commission == Decimal("5.00")  # minimum commission


class TestFeeSchedules:
    """Test fee schedule lookups."""

    def test_redemption_fee_schedule(self):
        assert _get_redemption_fee(3) == Decimal("0.015")   # <7天
        assert _get_redemption_fee(15) == Decimal("0.0075")  # 7-30天
        assert _get_redemption_fee(100) == Decimal("0.005")  # 30-365天
        assert _get_redemption_fee(400) == Decimal("0.0025")  # 1-2年
        assert _get_redemption_fee(800) == Decimal("0")       # >2年

    def test_dividend_tax_schedule(self):
        assert _get_dividend_tax(15) == Decimal("0.20")   # <1月
        assert _get_dividend_tax(100) == Decimal("0.10")   # 1月-1年
        assert _get_dividend_tax(400) == Decimal("0")      # >1年
