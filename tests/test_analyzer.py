"""
测试持仓分析模块

测试 src/analyzer.py 中的 Analyzer 类
"""

import pytest
import pandas as pd
from src.analyzer import Analyzer, ChangeAnalysis


# ==================== Fixtures ====================

@pytest.fixture
def analyzer():
    """创建 Analyzer 实例"""
    return Analyzer(threshold=5.0)


@pytest.fixture
def previous_holdings():
    """前一日持仓数据"""
    data = {
        'ticker': ['TSLA', 'COIN', 'SQ', 'SHOP', 'ROKU'],
        'company': ['Tesla Inc', 'Coinbase Global Inc', 'Block Inc', 'Shopify Inc', 'Roku Inc'],
        'shares': [1000000, 500000, 800000, 300000, 200000],
        'market_value': [250000000.00, 100000000.00, 50000000.00, 30000000.00, 15000000.00],
        'weight': [10.50, 4.20, 2.10, 1.26, 0.63]
    }
    return pd.DataFrame(data)


@pytest.fixture
def current_holdings():
    """当前持仓数据（有变化）"""
    data = {
        'ticker': ['TSLA', 'COIN', 'SQ', 'ROKU', 'PATH'],  # 移除 SHOP，新增 PATH
        'company': ['Tesla Inc', 'Coinbase Global Inc', 'Block Inc', 'Roku Inc', 'UiPath Inc'],
        'shares': [1200000, 450000, 800000, 220000, 500000],  # TSLA +20%, COIN -10%, SQ 不变, ROKU +10%
        'market_value': [300000000.00, 90000000.00, 50000000.00, 16500000.00, 25000000.00],
        'weight': [11.80, 3.50, 1.95, 0.65, 0.98]
    }
    return pd.DataFrame(data)


# ==================== 测试持仓对比 ====================

class TestCompareHoldings:
    """测试持仓对比功能"""
    
    def test_detect_added_stocks(self, analyzer, previous_holdings, current_holdings):
        """测试识别新增股票"""
        result = analyzer.compare_holdings(
            current_holdings,
            previous_holdings,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # 验证识别到新增股票
        assert isinstance(result, ChangeAnalysis)
        assert len(result.added) > 0
        
        # 验证新增股票是 PATH
        added_tickers = [stock['ticker'] for stock in result.added]
        assert 'PATH' in added_tickers
    
    def test_detect_removed_stocks(self, analyzer, previous_holdings, current_holdings):
        """测试识别移除股票"""
        result = analyzer.compare_holdings(
            current_holdings,
            previous_holdings,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # 验证识别到移除股票
        assert len(result.removed) > 0
        
        # 验证移除股票是 SHOP
        removed_tickers = [stock['ticker'] for stock in result.removed]
        assert 'SHOP' in removed_tickers
    
    def test_detect_increased_holdings(self, analyzer, previous_holdings, current_holdings):
        """测试识别增持股票"""
        result = analyzer.compare_holdings(
            current_holdings,
            previous_holdings,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # 验证识别到增持股票
        assert len(result.increased) > 0
        
        # 验证 TSLA 被识别为增持（+20%）
        increased_tickers = [stock['ticker'] for stock in result.increased]
        assert 'TSLA' in increased_tickers
        
        # 验证变化百分比正确
        tsla_change = next(s for s in result.increased if s['ticker'] == 'TSLA')
        assert tsla_change['change_percent'] == pytest.approx(20.0, rel=1e-2)
    
    def test_detect_decreased_holdings(self, analyzer, previous_holdings, current_holdings):
        """测试识别减持股票"""
        result = analyzer.compare_holdings(
            current_holdings,
            previous_holdings,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # 验证识别到减持股票
        assert len(result.decreased) > 0
        
        # 验证 COIN 被识别为减持（-10%）
        decreased_tickers = [stock['ticker'] for stock in result.decreased]
        assert 'COIN' in decreased_tickers
        
        # 验证变化百分比正确
        coin_change = next(s for s in result.decreased if s['ticker'] == 'COIN')
        assert coin_change['change_percent'] == pytest.approx(-10.0, rel=1e-2)
    
    def test_threshold_filtering(self, analyzer, previous_holdings, current_holdings):
        """测试阈值过滤"""
        # 使用 5% 阈值
        result = analyzer.compare_holdings(
            current_holdings,
            previous_holdings,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # TSLA +20% 应该在 increased
        increased_tickers = [stock['ticker'] for stock in result.increased]
        assert 'TSLA' in increased_tickers
        
        # COIN -10% 应该在 decreased
        decreased_tickers = [stock['ticker'] for stock in result.decreased]
        assert 'COIN' in decreased_tickers
        
        # ROKU +10% 应该在 increased（10% > 5%）
        assert 'ROKU' in increased_tickers
    
    def test_small_change_not_reported(self):
        """测试小幅变化不被报告（低于阈值）"""
        analyzer = Analyzer(threshold=5.0)
        
        previous = pd.DataFrame({
            'ticker': ['TSLA'],
            'company': ['Tesla Inc'],
            'shares': [1000000],
            'market_value': [250000000.00],
            'weight': [10.0]
        })
        
        current = pd.DataFrame({
            'ticker': ['TSLA'],
            'company': ['Tesla Inc'],
            'shares': [1030000],  # +3%（低于 5%）
            'market_value': [257500000.00],
            'weight': [10.3]
        })
        
        result = analyzer.compare_holdings(
            current,
            previous,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # 验证不在增持列表中（低于阈值）
        assert len(result.increased) == 0
        assert len(result.decreased) == 0
    
    def test_change_analysis_structure(self, analyzer, previous_holdings, current_holdings):
        """测试 ChangeAnalysis 数据结构"""
        result = analyzer.compare_holdings(
            current_holdings,
            previous_holdings,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # 验证必需字段
        assert result.etf_symbol == 'ARKK'
        assert result.current_date == '2025-01-15'
        assert result.previous_date == '2025-01-14'
        
        # 验证列表类型
        assert isinstance(result.added, list)
        assert isinstance(result.removed, list)
        assert isinstance(result.increased, list)
        assert isinstance(result.decreased, list)
        
        # 验证新增股票包含必要字段
        if len(result.added) > 0:
            added_stock = result.added[0]
            assert 'ticker' in added_stock
            assert 'company' in added_stock
            assert 'shares' in added_stock
            assert 'weight' in added_stock
        
        # 验证变化股票包含变化百分比
        if len(result.increased) > 0:
            increased_stock = result.increased[0]
            assert 'change_percent' in increased_stock
            assert 'previous_shares' in increased_stock
            assert 'current_shares' in increased_stock


# ==================== 测试边界情况 ====================

class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_previous_holdings(self, analyzer):
        """测试前一日持仓为空（首次运行）"""
        previous = pd.DataFrame(columns=['ticker', 'company', 'shares', 'market_value', 'weight'])
        
        current = pd.DataFrame({
            'ticker': ['TSLA', 'COIN'],
            'company': ['Tesla Inc', 'Coinbase Global Inc'],
            'shares': [1000000, 500000],
            'market_value': [250000000.00, 100000000.00],
            'weight': [10.0, 4.0]
        })
        
        result = analyzer.compare_holdings(
            current,
            previous,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # 所有股票应该被识别为新增
        assert len(result.added) == 2
        assert len(result.removed) == 0
        assert len(result.increased) == 0
        assert len(result.decreased) == 0
    
    def test_empty_current_holdings(self, analyzer, previous_holdings):
        """测试当前持仓为空（异常情况）"""
        current = pd.DataFrame(columns=['ticker', 'company', 'shares', 'market_value', 'weight'])
        
        result = analyzer.compare_holdings(
            current,
            previous_holdings,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # 所有股票应该被识别为移除
        assert len(result.added) == 0
        assert len(result.removed) == len(previous_holdings)
        assert len(result.increased) == 0
        assert len(result.decreased) == 0
    
    def test_no_changes(self, analyzer):
        """测试完全没有变化"""
        holdings = pd.DataFrame({
            'ticker': ['TSLA', 'COIN'],
            'company': ['Tesla Inc', 'Coinbase Global Inc'],
            'shares': [1000000, 500000],
            'market_value': [250000000.00, 100000000.00],
            'weight': [10.0, 4.0]
        })
        
        result = analyzer.compare_holdings(
            holdings.copy(),
            holdings.copy(),
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # 应该没有任何变化
        assert len(result.added) == 0
        assert len(result.removed) == 0
        assert len(result.increased) == 0
        assert len(result.decreased) == 0
    
    def test_custom_threshold(self):
        """测试自定义阈值"""
        # 使用 10% 阈值
        analyzer = Analyzer(threshold=10.0)
        
        previous = pd.DataFrame({
            'ticker': ['TSLA'],
            'company': ['Tesla Inc'],
            'shares': [1000000],
            'market_value': [250000000.00],
            'weight': [10.0]
        })
        
        current = pd.DataFrame({
            'ticker': ['TSLA'],
            'company': ['Tesla Inc'],
            'shares': [1070000],  # +7%（低于 10%）
            'market_value': [267500000.00],
            'weight': [10.7]
        })
        
        result = analyzer.compare_holdings(
            current,
            previous,
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14'
        )
        
        # +7% 低于 10% 阈值，不应该报告
        assert len(result.increased) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
