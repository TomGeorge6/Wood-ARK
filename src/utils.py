"""
工具函数模块

包含配置加载、日志管理、日期处理等工具函数。
"""

import os
import re
import yaml
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv


# ==================== 数据类定义 ====================

@dataclass
class ScheduleConfig:
    """定时任务配置"""
    enabled: bool
    cron_time: str
    timezone: str


@dataclass
class DataConfig:
    """数据配置"""
    etfs: List[str]
    data_dir: str
    log_dir: str
    retention_days: int = 90          # 历史数据保留天数
    auto_download_history: bool = True  # 是否自动下载历史数据
    history_days: int = 90             # 下载历史数据的天数


@dataclass
class AnalysisConfig:
    """分析配置"""
    change_threshold: float


@dataclass
class NotificationConfig:
    """通知配置"""
    webhook_url: str
    enable_error_alert: bool


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int
    retry_delays: List[int]


@dataclass
class LogConfig:
    """日志配置"""
    retention_days: int
    level: str


@dataclass
class Config:
    """系统配置"""
    schedule: ScheduleConfig
    data: DataConfig
    analysis: AnalysisConfig
    notification: NotificationConfig
    retry: RetryConfig
    log: LogConfig


# ==================== 配置加载和验证 ====================

def load_config(config_path: str = 'config.yaml') -> Config:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径（默认 config.yaml）
        
    Returns:
        Config 对象
        
    Raises:
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: YAML 格式错误
        ValueError: 必需配置缺失或格式错误
    """
    # 1. 加载 .env 文件
    load_dotenv()
    
    # 2. 检查配置文件是否存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}\n"
            f"请复制 config.yaml.example 为 config.yaml 并修改配置"
        )
    
    # 3. 读取 YAML 配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"YAML 格式错误: {e}")
    
    # 4. 替换环境变量引用（${VAR} 语法）
    def replace_env_vars(value):
        """递归替换环境变量"""
        if isinstance(value, str):
            # 匹配 ${VAR_NAME} 格式
            pattern = r'\$\{([A-Z_]+)\}'
            matches = re.findall(pattern, value)
            for var_name in matches:
                env_value = os.getenv(var_name)
                if env_value is None:
                    raise ValueError(f"环境变量未定义: {var_name}")
                value = value.replace(f'${{{var_name}}}', env_value)
            return value
        elif isinstance(value, dict):
            return {k: replace_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [replace_env_vars(item) for item in value]
        else:
            return value
    
    raw_config = replace_env_vars(raw_config)
    
    # 5. 构造 Config 对象
    try:
        config = Config(
            schedule=ScheduleConfig(**raw_config.get('schedule', {})),
            data=DataConfig(**raw_config.get('data', {})),
            analysis=AnalysisConfig(**raw_config.get('analysis', {})),
            notification=NotificationConfig(**raw_config.get('notification', {})),
            retry=RetryConfig(**raw_config.get('retry', {})),
            log=LogConfig(**raw_config.get('log', {}))
        )
    except TypeError as e:
        raise ValueError(f"配置文件格式错误: {e}")
    
    # 6. 验证配置
    validate_config(config)
    
    return config


def validate_config(config: Config) -> None:
    """
    验证配置完整性
    
    Args:
        config: Config 对象
        
    Raises:
        ValueError: 配置不合法（含详细错误信息）
    """
    # 1. 验证 webhook_url
    if not config.notification.webhook_url:
        raise ValueError(
            "未配置 WECHAT_WEBHOOK_URL 环境变量\n"
            "请在 .env 文件中设置: WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/..."
        )
    
    if not config.notification.webhook_url.startswith('https://qyapi.weixin.qq.com'):
        raise ValueError(
            f"WECHAT_WEBHOOK_URL 格式错误: {config.notification.webhook_url}\n"
            f"必须以 https://qyapi.weixin.qq.com 开头"
        )
    
    # 2. 验证 change_threshold
    if not (0.1 <= config.analysis.change_threshold <= 100):
        raise ValueError(
            f"change_threshold 必须在 0.1-100 范围，当前值: {config.analysis.change_threshold}"
        )
    
    # 3. 验证 ETF 列表
    if not config.data.etfs:
        raise ValueError("ETF 列表不能为空")
    
    valid_etfs = {'ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF'}
    for etf in config.data.etfs:
        if etf not in valid_etfs:
            raise ValueError(
                f"无效的 ETF 代码: {etf}\n"
                f"支持的 ETF: {', '.join(sorted(valid_etfs))}"
            )
    
    # 4. 验证目录路径
    if not config.data.data_dir:
        raise ValueError("data_dir 不能为空")
    
    if not config.data.log_dir:
        raise ValueError("log_dir 不能为空")
    
    # 5. 验证重试配置
    if config.retry.max_retries < 0:
        raise ValueError(f"max_retries 不能为负数: {config.retry.max_retries}")
    
    if len(config.retry.retry_delays) != config.retry.max_retries:
        raise ValueError(
            f"retry_delays 长度 ({len(config.retry.retry_delays)}) "
            f"必须等于 max_retries ({config.retry.max_retries})"
        )
    
    # 6. 验证日志级别
    valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    if config.log.level not in valid_levels:
        raise ValueError(
            f"无效的日志级别: {config.log.level}\n"
            f"支持的级别: {', '.join(sorted(valid_levels))}"
        )


# ==================== 日志管理 ====================

def setup_logging(log_dir: str, log_level: str = 'INFO') -> None:
    """
    配置日志系统
    
    Args:
        log_dir: 日志目录
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        
    Side Effects:
        - 创建日志目录（如不存在）
        - 配置日志格式：时间戳 + 级别 + 模块 + 消息
        - 日志文件命名：{YYYY-MM-DD}.log
        - 同时输出到文件和控制台
    """
    # 1. 创建日志目录
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 2. 生成日志文件名（当天日期）
    log_file = os.path.join(log_dir, f"{get_current_date()}.log")
    
    # 3. 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 4. 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 文件处理器
            logging.FileHandler(log_file, encoding='utf-8'),
            # 控制台处理器
            logging.StreamHandler()
        ],
        force=True  # 强制重新配置（如果已配置）
    )
    
    # 5. 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("日志系统初始化成功")
    logger.info(f"日志文件: {log_file}")
    logger.info(f"日志级别: {log_level}")
    logger.info("=" * 60)


def cleanup_old_logs(log_dir: str, retention_days: int) -> None:
    """
    清理过期日志文件
    
    Args:
        log_dir: 日志目录
        retention_days: 保留天数
        
    Side Effects:
        - 删除 retention_days 天前的日志文件
    """
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(log_dir):
        logger.warning(f"日志目录不存在: {log_dir}")
        return
    
    # 计算截止日期
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d')
    
    deleted_count = 0
    for filename in os.listdir(log_dir):
        if not filename.endswith('.log'):
            continue
        
        # 提取日期（假设文件名格式为 YYYY-MM-DD.log）
        match = re.match(r'(\d{4}-\d{2}-\d{2})\.log', filename)
        if not match:
            continue
        
        file_date = match.group(1)
        if file_date < cutoff_str:
            file_path = os.path.join(log_dir, filename)
            try:
                os.remove(file_path)
                deleted_count += 1
                logger.info(f"删除过期日志: {filename}")
            except OSError as e:
                logger.error(f"删除日志失败 {filename}: {e}")
    
    if deleted_count > 0:
        logger.info(f"清理完成，删除 {deleted_count} 个过期日志文件")
    else:
        logger.debug("无过期日志需要清理")


# ==================== 日期处理 ====================

def get_current_date() -> str:
    """
    获取当前日期（美国东部时间 ET，ARK Funds 所在时区）
    
    由于 ARK 是美国基金，其数据更新按美国东部时间（ET）
    北京时间 = 美国东部时间 + 13小时（冬令时）或 + 12小时（夏令时）
    
    Returns:
        YYYY-MM-DD 格式字符串（美国东部时间）
    """
    try:
        from zoneinfo import ZoneInfo
        # 使用美国东部时区
        et_tz = ZoneInfo("America/New_York")
        et_now = datetime.now(et_tz)
        return et_now.strftime('%Y-%m-%d')
    except ImportError:
        # 备用方案：简单减去 13 小时（适用于大部分情况）
        # 这个方法不完美，但避免了引入 pytz 依赖
        utc_now = datetime.utcnow()
        et_now = utc_now - timedelta(hours=5)  # UTC-5 (东部标准时间)
        return et_now.strftime('%Y-%m-%d')


def get_previous_date(date: str) -> str:
    """
    获取前一天日期
    
    Args:
        date: YYYY-MM-DD 格式日期
        
    Returns:
        前一天日期（YYYY-MM-DD）
        
    Raises:
        ValueError: 日期格式错误
    """
    try:
        dt = datetime.strptime(date, '%Y-%m-%d')
        previous_dt = dt - timedelta(days=1)
        return previous_dt.strftime('%Y-%m-%d')
    except ValueError as e:
        raise ValueError(f"日期格式错误: {date}，应为 YYYY-MM-DD") from e


def get_recent_dates(days: int) -> List[str]:
    """
    获取最近 N 天的日期列表（倒序）
    
    Args:
        days: 天数
        
    Returns:
        日期列表（YYYY-MM-DD），从今天开始倒序
        
    Example:
        get_recent_dates(3)  # ['2025-01-15', '2025-01-14', '2025-01-13']
    """
    current = datetime.now()
    dates = []
    for i in range(days):
        date = current - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
    return dates


def is_weekday(date: Optional[str] = None) -> bool:
    """
    判断指定日期是否为工作日（周一到周五）
    
    Args:
        date: YYYY-MM-DD 格式日期（默认今天）
        
    Returns:
        True 表示工作日（周一到周五）
    """
    if date is None:
        dt = datetime.now()
    else:
        dt = datetime.strptime(date, '%Y-%m-%d')
    
    # weekday(): 0=Monday, 1=Tuesday, ..., 6=Sunday
    return dt.weekday() < 5  # 0-4 为工作日


# ==================== 文件路径工具 ====================

def ensure_dir(path: str) -> None:
    """
    确保目录存在，如不存在则创建
    
    Args:
        path: 目录路径
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def get_holding_file_path(data_dir: str, etf_symbol: str, date: str) -> str:
    """
    获取持仓数据文件路径
    
    Args:
        data_dir: 数据根目录
        etf_symbol: ETF 代码
        date: 日期（YYYY-MM-DD）
        
    Returns:
        文件路径（data/holdings/{etf_symbol}/{date}.csv）
    """
    return os.path.join(data_dir, 'holdings', etf_symbol, f"{date}.csv")


def get_report_file_path(data_dir: str, etf_symbol: str, date: str) -> str:
    """
    获取报告文件路径
    
    Args:
        data_dir: 数据根目录
        etf_symbol: ETF 代码
        date: 日期（YYYY-MM-DD）
        
    Returns:
        文件路径（data/reports/{etf_symbol}/{date}.md）
    """
    return os.path.join(data_dir, 'reports', etf_symbol, f"{date}.md")


def get_push_status_file_path(data_dir: str) -> str:
    """
    获取推送状态文件路径
    
    Args:
        data_dir: 数据根目录
        
    Returns:
        文件路径（data/cache/push_status.json）
    """
    return os.path.join(data_dir, 'cache', 'push_status.json')
