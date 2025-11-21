"""
测试工具函数模块

测试 src/utils.py 中的所有工具函数
"""

import os
import pytest
import yaml
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from src.utils import (
    load_config,
    validate_config,
    setup_logging,
    cleanup_old_logs,
    get_current_date,
    get_previous_date,
    get_recent_dates,
    Config
)


# ==================== 测试配置加载和验证 ====================

class TestConfigLoading:
    """测试配置加载相关功能"""
    
    def test_load_config_success(self, tmp_path):
        """测试正常加载配置"""
        # 准备测试配置文件
        config_content = """
schedule:
  enabled: true
  cron_time: "11:00"
  timezone: "Asia/Shanghai"

data:
  etfs: ["ARKK", "ARKW", "ARKG"]
  data_dir: "./data"
  log_dir: "./logs"

analysis:
  change_threshold: 5.0

notification:
  webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
  enable_error_alert: true

retry:
  max_retries: 3
  retry_delays: [1, 2, 4]

log:
  retention_days: 30
  level: "INFO"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        # 加载配置
        config = load_config(str(config_file))
        
        # 验证配置正确加载
        assert config.schedule.enabled is True
        assert config.schedule.cron_time == "11:00"
        assert config.data.etfs == ["ARKK", "ARKW", "ARKG"]
        assert config.analysis.change_threshold == 5.0
        assert config.notification.webhook_url == "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
        assert config.retry.max_retries == 3
        assert config.log.retention_days == 30
    
    def test_load_config_with_env_var(self, tmp_path, monkeypatch):
        """测试环境变量替换"""
        # 设置环境变量
        monkeypatch.setenv("WECHAT_WEBHOOK_URL", "https://webhook.test.com")
        
        # 准备测试配置文件
        config_content = """
schedule:
  enabled: true
  cron_time: "11:00"
  timezone: "Asia/Shanghai"

data:
  etfs: ["ARKK"]
  data_dir: "./data"
  log_dir: "./logs"

analysis:
  change_threshold: 5.0

notification:
  webhook_url: "${WECHAT_WEBHOOK_URL}"
  enable_error_alert: true

retry:
  max_retries: 3
  retry_delays: [1, 2, 4]

log:
  retention_days: 30
  level: "INFO"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        # 加载配置
        config = load_config(str(config_file))
        
        # 验证环境变量被正确替换
        assert config.notification.webhook_url == "https://webhook.test.com"
    
    def test_load_config_missing_env_var(self, tmp_path, monkeypatch):
        """测试缺失环境变量"""
        # 确保环境变量不存在
        monkeypatch.delenv("WECHAT_WEBHOOK_URL", raising=False)
        
        # 准备测试配置文件（使用未定义的环境变量）
        config_content = """
schedule:
  enabled: true
  cron_time: "11:00"
  timezone: "Asia/Shanghai"

data:
  etfs: ["ARKK"]
  data_dir: "./data"
  log_dir: "./logs"

analysis:
  change_threshold: 5.0

notification:
  webhook_url: "${WECHAT_WEBHOOK_URL}"
  enable_error_alert: true

retry:
  max_retries: 3
  retry_delays: [1, 2, 4]

log:
  retention_days: 30
  level: "INFO"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        # 加载配置不应抛出异常（只是保留原始字符串）
        config = load_config(str(config_file))
        
        # 验证会保留原始格式或为空
        assert "${WECHAT_WEBHOOK_URL}" in config.notification.webhook_url or config.notification.webhook_url == ""
    
    def test_validate_config_success(self, tmp_path):
        """测试配置验证成功"""
        config_content = """
schedule:
  enabled: true
  cron_time: "11:00"
  timezone: "Asia/Shanghai"

data:
  etfs: ["ARKK", "ARKW"]
  data_dir: "./data"
  log_dir: "./logs"

analysis:
  change_threshold: 5.0

notification:
  webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
  enable_error_alert: true

retry:
  max_retries: 3
  retry_delays: [1, 2, 4]

log:
  retention_days: 30
  level: "INFO"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        config = load_config(str(config_file))
        
        # 验证应该成功（不抛出异常）
        validate_config(config)
    
    def test_validate_config_invalid_webhook(self, tmp_path):
        """测试 webhook_url 缺失或无效"""
        config_content = """
schedule:
  enabled: true
  cron_time: "11:00"
  timezone: "Asia/Shanghai"

data:
  etfs: ["ARKK"]
  data_dir: "./data"
  log_dir: "./logs"

analysis:
  change_threshold: 5.0

notification:
  webhook_url: ""
  enable_error_alert: true

retry:
  max_retries: 3
  retry_delays: [1, 2, 4]

log:
  retention_days: 30
  level: "INFO"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        config = load_config(str(config_file))
        
        # 验证应该抛出 ValueError
        with pytest.raises(ValueError, match="webhook_url"):
            validate_config(config)
    
    def test_validate_config_invalid_threshold(self, tmp_path):
        """测试阈值超出范围"""
        config_content = """
schedule:
  enabled: true
  cron_time: "11:00"
  timezone: "Asia/Shanghai"

data:
  etfs: ["ARKK"]
  data_dir: "./data"
  log_dir: "./logs"

analysis:
  change_threshold: 150.0

notification:
  webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
  enable_error_alert: true

retry:
  max_retries: 3
  retry_delays: [1, 2, 4]

log:
  retention_days: 30
  level: "INFO"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        config = load_config(str(config_file))
        
        # 验证应该抛出 ValueError
        with pytest.raises(ValueError, match="change_threshold"):
            validate_config(config)
    
    def test_validate_config_empty_etfs(self, tmp_path):
        """测试 ETF 列表为空"""
        config_content = """
schedule:
  enabled: true
  cron_time: "11:00"
  timezone: "Asia/Shanghai"

data:
  etfs: []
  data_dir: "./data"
  log_dir: "./logs"

analysis:
  change_threshold: 5.0

notification:
  webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
  enable_error_alert: true

retry:
  max_retries: 3
  retry_delays: [1, 2, 4]

log:
  retention_days: 30
  level: "INFO"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        config = load_config(str(config_file))
        
        # 验证应该抛出 ValueError
        with pytest.raises(ValueError, match="etfs"):
            validate_config(config)


# ==================== 测试日志管理 ====================

class TestLogging:
    """测试日志相关功能"""
    
    def test_setup_logging(self, tmp_path):
        """测试日志系统配置"""
        log_dir = str(tmp_path / "logs")
        
        # 配置日志
        setup_logging(log_dir, "INFO")
        
        # 验证日志目录创建成功
        assert os.path.exists(log_dir)
        
        # 验证日志文件创建
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = Path(log_dir) / f"{today}.log"
        assert log_file.exists()
    
    def test_cleanup_old_logs(self, tmp_path):
        """测试过期日志清理"""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        
        # 创建测试日志文件
        today = datetime.now()
        
        # 创建 35 天前的日志（应被删除）
        old_date = today - timedelta(days=35)
        old_log = log_dir / f"{old_date.strftime('%Y-%m-%d')}.log"
        old_log.write_text("old log")
        
        # 创建 10 天前的日志（应保留）
        recent_date = today - timedelta(days=10)
        recent_log = log_dir / f"{recent_date.strftime('%Y-%m-%d')}.log"
        recent_log.write_text("recent log")
        
        # 创建今天的日志（应保留）
        today_log = log_dir / f"{today.strftime('%Y-%m-%d')}.log"
        today_log.write_text("today log")
        
        # 执行清理（保留 30 天）
        cleanup_old_logs(str(log_dir), retention_days=30)
        
        # 验证结果
        assert not old_log.exists(), "35天前的日志应被删除"
        assert recent_log.exists(), "10天前的日志应保留"
        assert today_log.exists(), "今天的日志应保留"


# ==================== 测试日期工具 ====================

class TestDateUtils:
    """测试日期工具函数"""
    
    def test_get_current_date(self):
        """测试获取当前日期"""
        current_date = get_current_date()
        
        # 验证格式为 YYYY-MM-DD
        assert len(current_date) == 10
        assert current_date[4] == '-'
        assert current_date[7] == '-'
        
        # 验证是今天的日期
        today = datetime.now().strftime("%Y-%m-%d")
        assert current_date == today
    
    def test_get_previous_date(self):
        """测试获取前一天日期"""
        # 测试正常情况
        current_date = "2025-01-15"
        previous_date = get_previous_date(current_date)
        assert previous_date == "2025-01-14"
        
        # 测试跨月情况
        current_date = "2025-02-01"
        previous_date = get_previous_date(current_date)
        assert previous_date == "2025-01-31"
        
        # 测试跨年情况
        current_date = "2025-01-01"
        previous_date = get_previous_date(current_date)
        assert previous_date == "2024-12-31"
    
    def test_get_recent_dates(self):
        """测试获取最近 N 天的日期"""
        # 测试获取最近 5 天
        recent_dates = get_recent_dates(5)
        
        # 验证返回 5 个日期
        assert len(recent_dates) == 5
        
        # 验证第一个是今天
        today = datetime.now().strftime("%Y-%m-%d")
        assert recent_dates[0] == today
        
        # 验证日期连续递减
        for i in range(len(recent_dates) - 1):
            current = datetime.strptime(recent_dates[i], "%Y-%m-%d")
            next_day = datetime.strptime(recent_dates[i + 1], "%Y-%m-%d")
            delta = (current - next_day).days
            assert delta == 1, "日期应连续递减"
    
    def test_get_recent_dates_single_day(self):
        """测试获取最近 1 天（边界情况）"""
        recent_dates = get_recent_dates(1)
        
        assert len(recent_dates) == 1
        today = datetime.now().strftime("%Y-%m-%d")
        assert recent_dates[0] == today


# ==================== Pytest Fixtures ====================

@pytest.fixture(autouse=True)
def cleanup_logging():
    """每个测试后清理日志配置"""
    yield
    # 清理日志处理器，避免测试间干扰
    import logging
    logger = logging.getLogger()
    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
