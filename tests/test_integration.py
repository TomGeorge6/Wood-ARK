"""
集成测试

测试完整工作流：数据获取 → 分析 → 报告 → 推送
"""

import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.fetcher import DataFetcher
from src.analyzer import Analyzer, ChangeAnalysis
from src.reporter import ReportGenerator
from src.notifier import WeChatNotifier
from src.scheduler import Scheduler
from src.utils import Config, ScheduleConfig, DataConfig, AnalysisConfig, NotificationConfig, RetryConfig, LogConfig


# ==================== Fixtures ====================

@pytest.fixture
def mock_config(tmp_path):
    """创建完整的模拟配置"""
    config = MagicMock(spec=Config)
    config.schedule = MagicMock(spec=ScheduleConfig)
    config.schedule.enabled = True
    config.schedule.cron_time = "11:00"
    config.schedule.timezone = "Asia/Shanghai"
    
    config.data = MagicMock(spec=DataConfig)
    config.data.etfs = ["ARKK"]  # 只测试一个 ETF
    config.data.data_dir = str(tmp_path)
    config.data.log_dir = str(tmp_path / "logs")
    
    config.analysis = MagicMock(spec=AnalysisConfig)
    config.analysis.change_threshold = 5.0
    
    config.notification = MagicMock(spec=NotificationConfig)
    config.notification.webhook_url = "https://test.webhook.com"
    config.notification.enable_error_alert = True
    
    config.retry = MagicMock(spec=RetryConfig)
    config.retry.max_retries = 3
    config.retry.retry_delays = [1, 2, 4]
    
    config.log = MagicMock(spec=LogConfig)
    config.log.retention_days = 30
    config.log.level = "INFO"
    
    return config


@pytest.fixture
def sample_csv_previous():
    """前一日 CSV 数据"""
    return """date,fund,company,ticker,cusip,shares,market value($),weight(%)
2025-01-14,ARKK,Tesla Inc,TSLA,88160R101,1000000,250000000.00,10.50
2025-01-14,ARKK,Coinbase Global Inc,COIN,19260Q107,500000,100000000.00,4.20
2025-01-14,ARKK,Shopify Inc,SHOP,82509L107,300000,30000000.00,1.26
"""


@pytest.fixture
def sample_csv_current():
    """当前 CSV 数据"""
    return """date,fund,company,ticker,cusip,shares,market value($),weight(%)
2025-01-15,ARKK,Tesla Inc,TSLA,88160R101,1200000,300000000.00,11.80
2025-01-15,ARKK,Coinbase Global Inc,COIN,19260Q107,450000,90000000.00,3.50
2025-01-15,ARKK,UiPath Inc,PATH,90364P105,500000,25000000.00,0.98
"""


# ==================== 完整流程集成测试 ====================

class TestFullWorkflow:
    """测试完整工作流"""
    
    @patch('src.fetcher.requests.get')
    @patch('src.notifier.requests.post')
    def test_manual_mode_full_workflow(
        self,
        mock_post,
        mock_get,
        mock_config,
        sample_csv_previous,
        sample_csv_current
    ):
        """测试手动模式完整流程"""
        # ========== 1. Mock HTTP 请求 ==========
        
        # Mock 数据下载（两次请求：前一日 + 当前）
        def mock_get_response(url, *args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            
            # 根据 URL 返回不同数据（简化处理）
            # 实际中会根据日期区分，这里假设第一次是前一日，第二次是当前
            if mock_get.call_count == 1:
                mock_response.text = sample_csv_previous
            else:
                mock_response.text = sample_csv_current
            
            return mock_response
        
        mock_get.side_effect = mock_get_response
        
        # Mock 企业微信推送
        mock_push_response = Mock()
        mock_push_response.status_code = 200
        mock_push_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_post.return_value = mock_push_response
        
        # ========== 2. 创建测试实例 ==========
        
        fetcher = DataFetcher(mock_config)
        analyzer = Analyzer(threshold=mock_config.analysis.change_threshold)
        reporter = ReportGenerator()
        reporter.data_dir = mock_config.data.data_dir
        notifier = WeChatNotifier(
            webhook_url=mock_config.notification.webhook_url,
            max_retries=mock_config.retry.max_retries
        )
        scheduler = Scheduler(mock_config)
        
        # ========== 3. 执行完整流程 ==========
        
        current_date = '2025-01-15'
        previous_date = '2025-01-14'
        etf_symbol = 'ARKK'
        
        # 3.1 获取当前数据
        current_df = fetcher.fetch_holdings(etf_symbol, current_date)
        fetcher.save_to_csv(current_df, etf_symbol, current_date)
        
        # 3.2 获取前一日数据
        previous_df = fetcher.fetch_holdings(etf_symbol, previous_date)
        fetcher.save_to_csv(previous_df, etf_symbol, previous_date)
        
        # 3.3 分析持仓变化
        analysis = analyzer.compare_holdings(
            current_df,
            previous_df,
            etf_symbol,
            current_date,
            previous_date
        )
        
        # 3.4 生成报告
        markdown = reporter.generate_markdown([analysis], execution_time='11:05:23')
        reporter.save_report(markdown, etf_symbol, current_date)
        
        # 3.5 推送到企业微信
        push_success = notifier.send_markdown(markdown)
        
        # 3.6 更新状态
        scheduler.mark_pushed(current_date, success=push_success, etfs=[etf_symbol])
        
        # ========== 4. 验证结果 ==========
        
        # 验证数据文件保存
        assert (Path(mock_config.data.data_dir) / "holdings" / etf_symbol / f"{current_date}.csv").exists()
        assert (Path(mock_config.data.data_dir) / "holdings" / etf_symbol / f"{previous_date}.csv").exists()
        
        # 验证报告文件保存
        assert (Path(mock_config.data.data_dir) / "reports" / etf_symbol / f"{current_date}.md").exists()
        
        # 验证持仓变化分析正确
        assert isinstance(analysis, ChangeAnalysis)
        assert len(analysis.added) > 0  # 新增 PATH
        assert len(analysis.removed) > 0  # 移除 SHOP
        assert len(analysis.increased) > 0  # TSLA 增持 20%
        assert len(analysis.decreased) > 0  # COIN 减持 10%
        
        # 验证推送成功
        assert push_success is True
        assert mock_post.called
        
        # 验证推送状态记录
        status_file = Path(mock_config.data.data_dir) / "cache" / "push_status.json"
        assert status_file.exists()
        status_data = json.loads(status_file.read_text())
        assert current_date in status_data
        assert status_data[current_date]['success'] is True
    
    @patch('src.fetcher.requests.get')
    def test_check_missed_mode_workflow(
        self,
        mock_get,
        mock_config,
        sample_csv_current
    ):
        """测试补偿模式工作流"""
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_csv_current
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 创建 scheduler
        scheduler = Scheduler(mock_config)
        
        # 检测缺失日期
        missed_dates = scheduler.check_missed_dates(days=3)
        
        # 验证返回缺失日期列表
        assert isinstance(missed_dates, list)
        assert len(missed_dates) > 0
    
    @patch('src.fetcher.requests.get')
    @patch('src.notifier.requests.post')
    def test_network_failure_retry(
        self,
        mock_post,
        mock_get,
        mock_config,
        sample_csv_current
    ):
        """测试网络故障重试机制"""
        # Mock: 数据下载第 2 次成功
        mock_get_fail = Mock()
        mock_get_fail.raise_for_status.side_effect = Exception("Network error")
        
        mock_get_success = Mock()
        mock_get_success.status_code = 200
        mock_get_success.text = sample_csv_current
        mock_get_success.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_get_fail, mock_get_success]
        
        # Mock: 推送第 2 次成功
        mock_post_fail = Mock()
        mock_post_fail.status_code = 500
        mock_post_fail.json.return_value = {'errcode': 500, 'errmsg': 'error'}
        
        mock_post_success = Mock()
        mock_post_success.status_code = 200
        mock_post_success.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        
        mock_post.side_effect = [mock_post_fail, mock_post_success]
        
        # 执行流程
        fetcher = DataFetcher(mock_config)
        notifier = WeChatNotifier(
            webhook_url=mock_config.notification.webhook_url,
            max_retries=3
        )
        
        # 数据下载（会重试）
        df = fetcher.fetch_holdings('ARKK', '2025-01-15')
        assert df is not None
        assert mock_get.call_count == 2  # 重试 1 次后成功
        
        # 推送（会重试）
        success = notifier.send_markdown("# Test")
        assert success is True
        assert mock_post.call_count == 2  # 重试 1 次后成功


# ==================== 数据一致性测试 ====================

class TestDataConsistency:
    """测试数据一致性"""
    
    @patch('src.fetcher.requests.get')
    def test_save_and_load_consistency(
        self,
        mock_get,
        mock_config,
        sample_csv_current
    ):
        """测试数据保存和加载的一致性"""
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_csv_current
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        fetcher = DataFetcher(mock_config)
        
        # 下载并保存
        df_fetched = fetcher.fetch_holdings('ARKK', '2025-01-15')
        fetcher.save_to_csv(df_fetched, 'ARKK', '2025-01-15')
        
        # 重新加载
        df_loaded = fetcher.load_from_csv('ARKK', '2025-01-15')
        
        # 验证数据一致
        assert len(df_loaded) == len(df_fetched)
        assert set(df_loaded['ticker'].tolist()) == set(df_fetched['ticker'].tolist())
        
        # 验证数值精度
        for ticker in df_loaded['ticker']:
            fetched_row = df_fetched[df_fetched['ticker'] == ticker].iloc[0]
            loaded_row = df_loaded[df_loaded['ticker'] == ticker].iloc[0]
            
            assert fetched_row['shares'] == loaded_row['shares']
            assert abs(fetched_row['weight'] - loaded_row['weight']) < 0.01  # 允许精度误差
    
    def test_analysis_to_report_consistency(self, mock_config):
        """测试分析结果到报告的一致性"""
        # 创建分析结果
        analysis = ChangeAnalysis(
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14',
            added=[{
                'ticker': 'PATH',
                'company': 'UiPath Inc',
                'shares': 500000,
                'market_value': 25000000.00,
                'weight': 0.98
            }],
            removed=[],
            increased=[],
            decreased=[]
        )
        
        # 生成报告
        reporter = ReportGenerator()
        markdown = reporter.generate_markdown([analysis], execution_time='11:05:23')
        
        # 验证报告包含分析结果的关键信息
        assert 'ARKK' in markdown
        assert 'PATH' in markdown
        assert 'UiPath Inc' in markdown
        assert '2025-01-15' in markdown


# ==================== 错误处理测试 ====================

class TestErrorHandling:
    """测试错误处理"""
    
    @patch('src.fetcher.requests.get')
    def test_single_etf_failure_does_not_block_others(
        self,
        mock_get,
        mock_config
    ):
        """测试单个 ETF 失败不影响其他 ETF"""
        # 修改配置，监控 2 个 ETF
        mock_config.data.etfs = ['ARKK', 'ARKW']
        
        # Mock: ARKK 失败，ARKW 成功
        def mock_get_response(url, *args, **kwargs):
            if 'ARKK' in url:
                raise Exception("Network error")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = """date,fund,company,ticker,shares,market value($),weight(%)
2025-01-15,ARKW,Tesla Inc,TSLA,1000000,250000000.00,10.0
"""
                mock_response.raise_for_status = Mock()
                return mock_response
        
        mock_get.side_effect = mock_get_response
        
        # 尝试获取两个 ETF（ARKK 会失败）
        fetcher = DataFetcher(mock_config)
        
        # ARKK 失败
        with pytest.raises(Exception):
            fetcher.fetch_holdings('ARKK', '2025-01-15')
        
        # ARKW 成功
        df = fetcher.fetch_holdings('ARKW', '2025-01-15')
        assert df is not None
        assert len(df) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
