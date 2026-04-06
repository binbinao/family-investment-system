"""Phase 2: A 股行情定时与调度注册约定。"""

from app.core.scheduler import _CN_EQUITY_REFRESH_TRIGGER_KW


def test_cn_equity_refresh_has_six_triggers():
    """与设计 §2.1 一致：上午三段 + 下午两段 + 15:00 收盘。"""
    assert len(_CN_EQUITY_REFRESH_TRIGGER_KW) == 6
    last = _CN_EQUITY_REFRESH_TRIGGER_KW[-1]
    assert last["hour"] == 15 and last["minute"] == 0
