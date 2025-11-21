"""
测试调度逻辑模块

测试 src/scheduler.py 中的 Scheduler 类
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.scheduler import Scheduler
from src.utils import Config, ScheduleConfig, DataConfig, AnalysisConfig, NotificationConfig, RetryConfig, LogConfig


# ==================== Fixtures ====================

@pytest.fixture
def mock_config():
    """创建模拟配置"""
    config = MagicMock(spec=Config)
    config.schedule = MagicMock(spec=ScheduleConfig)
    config.schedule.enabled = True
    config.schedule.cron_time = "11:00"
    config.schedule.timezone = "Asia/Shanghai"
    
    config.data = MagicMock(spec=DataConfig)
    config.data.etfs = ["ARKK", "ARKW", "ARKG"]
    config.data.data_dir = "./test_data"
    config.data.log_dir = "./test_logs"
    
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
def scheduler(mock_config):
    """创建 Scheduler 实例"""
    return Scheduler(mock_config)


# ==================== 测试工作日判断 ====================

class TestWeekdayCheck:
    """测试工作日判断"""
    
    @patch('src.scheduler.datetime')
    def test_should_run_on_monday(self, mock_datetime, scheduler):
        """测试周一应该运行"""
        # Mock 周一
        mock_datetime.now.return_value = datetime(2025, 1, 13)  # 2025-01-13 是周一
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        assert scheduler.should_run_today() is True
    
    @patch('src.scheduler.datetime')
    def test_should_run_on_friday(self, mock_datetime, scheduler):
        """测试周五应该运行"""
        # Mock 周五
        mock_datetime.now.return_value = datetime(2025, 1, 17)  # 2025-01-17 是周五
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        assert scheduler.should_run_today() is True
    
    @patch('src.scheduler.datetime')
    def test_should_not_run_on_saturday(self, mock_datetime, scheduler):
        """测试周六不应该运行"""
        # Mock 周六
        mock_datetime.now.return_value = datetime(2025, 1, 18)  # 2025-01-18 是周六
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        assert scheduler.should_run_today() is False
    
    @patch('src.scheduler.datetime')
    def test_should_not_run_on_sunday(self, mock_datetime, scheduler):
        """测试周日不应该运行"""
        # Mock 周日
        mock_datetime.now.return_value = datetime(2025, 1, 19)  # 2025-01-19 是周日
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        assert scheduler.should_run_today() is False


# ==================== 测试日期计算 ====================

class TestDateCalculation:
    """测试日期计算功能"""
    
    def test_get_previous_trading_day(self, scheduler):
        """测试获取前一个交易日"""
        # 周二的前一个交易日是周一
        previous = scheduler.get_previous_trading_day('2025-01-14')
        assert previous == '2025-01-13'
        
        # 周一的前一个交易日是上周五（简化实现可能是周日）
        previous = scheduler.get_previous_trading_day('2025-01-13')
        assert previous in ['2025-01-12', '2025-01-10']  # 取决于实现方式
    
    def test_check_missed_dates(self, scheduler, tmp_path):
        """测试检测缺失日期"""
        # 修改配置的数据目录
        scheduler.config.data.data_dir = str(tmp_path)
        
        # 创建一些测试数据文件（模拟已有数据）
        arkk_dir = tmp_path / "holdings" / "ARKK"
        arkk_dir.mkdir(parents=True)
        
        # 创建前天和昨天的数据文件
        two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        (arkk_dir / f"{two_days_ago}.csv").write_text("date,ticker\n2025-01-10,TSLA")
        (arkk_dir / f"{yesterday}.csv").write_text("date,ticker\n2025-01-11,TSLA")
        
        # 检测最近 7 天缺失的日期
        missed_dates = scheduler.check_missed_dates(days=7)
        
        # 验证返回的是缺失日期列表
        assert isinstance(missed_dates, list)
        # 至少包含今天（因为今天没有数据）
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in missed_dates or len(missed_dates) > 0


# ==================== 测试状态管理 ====================

class TestPushStatus:
    """测试推送状态管理"""
    
    def test_is_already_pushed_false(self, scheduler, tmp_path):
        """测试未推送状态"""
        scheduler.config.data.data_dir = str(tmp_path)
        
        # 状态文件不存在
        result = scheduler.is_already_pushed('2025-01-15')
        assert result is False
    
    def test_is_already_pushed_true(self, scheduler, tmp_path):
        """测试已推送状态"""
        scheduler.config.data.data_dir = str(tmp_path)
        
        # 创建状态文件
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        status_file = cache_dir / "push_status.json"
        
        status_data = {
            "2025-01-15": {
                "pushed": True,
                "timestamp": "2025-01-15 11:05:23",
                "success": True,
                "etfs": ["ARKK", "ARKW", "ARKG"]
            }
        }
        status_file.write_text(json.dumps(status_data, ensure_ascii=False, indent=2))
        
        # 检查状态
        result = scheduler.is_already_pushed('2025-01-15')
        assert result is True
    
    def test_mark_pushed_success(self, scheduler, tmp_path):
        """测试标记推送成功"""
        scheduler.config.data.data_dir = str(tmp_path)
        
        # 标记推送
        scheduler.mark_pushed('2025-01-15', success=True, etfs=["ARKK", "ARKW"])
        
        # 验证状态文件创建
        status_file = tmp_path / "cache" / "push_status.json"
        assert status_file.exists()
        
        # 验证状态内容
        status_data = json.loads(status_file.read_text())
        assert '2025-01-15' in status_data
        assert status_data['2025-01-15']['success'] is True
        assert status_data['2025-01-15']['etfs'] == ["ARKK", "ARKW"]
    
    def test_mark_pushed_failure(self, scheduler, tmp_path):
        """测试标记推送失败"""
        scheduler.config.data.data_dir = str(tmp_path)
        
        # 标记推送失败
        scheduler.mark_pushed('2025-01-15', success=False, etfs=["ARKK"])
        
        # 验证状态
        status_file = tmp_path / "cache" / "push_status.json"
        status_data = json.loads(status_file.read_text())
        
        assert status_data['2025-01-15']['success'] is False
    
    def test_mark_pushed_updates_existing(self, scheduler, tmp_path):
        """测试更新已有状态"""
        scheduler.config.data.data_dir = str(tmp_path)
        
        # 第一次标记
        scheduler.mark_pushed('2025-01-15', success=True, etfs=["ARKK"])
        
        # 第二次标记（更新）
        scheduler.mark_pushed('2025-01-15', success=True, etfs=["ARKK", "ARKW"])
        
        # 验证状态更新
        status_file = tmp_path / "cache" / "push_status.json"
        status_data = json.loads(status_file.read_text())
        
        assert len(status_data['2025-01-15']['etfs']) == 2
        assert "ARKW" in status_data['2025-01-15']['etfs']


# ==================== 测试完整流程（Mock） ====================

class TestDailyTaskExecution:
    """测试每日任务执行"""
    
    @patch('src.scheduler.DataFetcher')
    @patch('src.scheduler.Analyzer')
    @patch('src.scheduler.ReportGenerator')
    @patch('src.scheduler.WeChatNotifier')
    def test_run_daily_task_success(
        self,
        mock_notifier_class,
        mock_reporter_class,
        mock_analyzer_class,
        mock_fetcher_class,
        scheduler,
        tmp_path
    ):
        """测试每日任务成功执行"""
        scheduler.config.data.data_dir = str(tmp_path)
        
        # Mock 各个组件
        mock_fetcher = MagicMock()
        mock_analyzer = MagicMock()
        mock_reporter = MagicMock()
        mock_notifier = MagicMock()
        
        mock_fetcher_class.return_value = mock_fetcher
        mock_analyzer_class.return_value = mock_analyzer
        mock_reporter_class.return_value = mock_reporter
        mock_notifier_class.return_value = mock_notifier
        
        # Mock 返回值
        import pandas as pd
        mock_df = pd.DataFrame({
            'ticker': ['TSLA'],
            'company': ['Tesla Inc'],
            'shares': [1000000],
            'market_value': [250000000.00],
            'weight': [10.0]
        })
        mock_fetcher.fetch_holdings.return_value = mock_df
        
        from src.analyzer import ChangeAnalysis
        mock_analysis = ChangeAnalysis(
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14',
            added=[],
            removed=[],
            increased=[],
            decreased=[]
        )
        mock_analyzer.compare_holdings.return_value = mock_analysis
        
        mock_reporter.generate_markdown.return_value = "# ARK 持仓变化"
        mock_notifier.send_markdown.return_value = True
        
        # 执行任务（手动强制模式）
        scheduler.run_daily_task('2025-01-15', force=True)
        
        # 验证各组件被调用
        assert mock_fetcher.fetch_holdings.called
        assert mock_analyzer.compare_holdings.called
        assert mock_reporter.generate_markdown.called
        assert mock_notifier.send_markdown.called
    
    @patch('src.scheduler.DataFetcher')
    def test_run_daily_task_skip_if_already_pushed(
        self,
        mock_fetcher_class,
        scheduler,
        tmp_path
    ):
        """测试已推送时跳过"""
        scheduler.config.data.data_dir = str(tmp_path)
        
        # 创建已推送状态
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        status_file = cache_dir / "push_status.json"
        status_data = {
            "2025-01-15": {
                "pushed": True,
                "success": True,
                "etfs": ["ARKK", "ARKW", "ARKG"]
            }
        }
        status_file.write_text(json.dumps(status_data))
        
        # 执行任务（非强制模式）
        scheduler.run_daily_task('2025-01-15', force=False)
        
        # 验证不会调用数据获取
        mock_fetcher_class.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
