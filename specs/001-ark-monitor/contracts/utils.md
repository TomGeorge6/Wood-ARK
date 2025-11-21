# Module Contract: Utils

**Module**: `src/utils.py`  
**Purpose**: 提供共享的工具函数（配置加载、日志设置、日期处理等）

---

## Public Functions

### 1. load_config()

**签名**:

```python
def load_config(config_path: str = 'config.yaml') -> Config:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径（默认 'config.yaml'）
        
    Returns:
        Config 对象
        
    Raises:
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: YAML 格式错误
        ValueError: 必需配置缺失或格式错误
        
    Implementation Details:
        1. 加载 .env 文件（python-dotenv）
        2. 读取 config.yaml（PyYAML）
        3. 递归替换 ${VAR} 语法为环境变量值
        4. 验证必需配置（webhook_url）
        5. 构造并返回 Config 对象
        
    Environment Variable Substitution:
        配置文件中的 ${VAR} 会被替换为环境变量值
        示例: webhook_url: "${WECHAT_WEBHOOK_URL}"
    """
    pass
```

**Example Usage**:

```python
from src.utils import load_config

config = load_config('config.yaml')

print(config.schedule.cron_time)  # "11:00"
print(config.data.etfs)  # ["ARKK", "ARKW", ...]
print(config.notification.webhook_url)  # 从 .env 读取的实际 URL
```

---

### 2. validate_config()

**签名**:

```python
def validate_config(config: Config) -> None:
    """验证配置完整性
    
    Args:
        config: Config 对象
        
    Raises:
        ValueError: 配置不合法（含详细错误信息）
        
    Validation Checks:
        - webhook_url 非空
        - webhook_url 以 'https://qyapi.weixin.qq.com' 开头
        - change_threshold 在 0.1-100 范围
        - etfs 列表非空且所有 ETF 代码有效
        - data_dir 和 log_dir 路径有效
        - log_level 为有效值（DEBUG/INFO/WARNING/ERROR）
    """
    pass
```

**Example Usage**:

```python
from src.utils import load_config, validate_config

config = load_config()

try:
    validate_config(config)
    print("✅ 配置验证通过")
except ValueError as e:
    print(f"❌ 配置错误: {e}")
    sys.exit(1)
```

---

### 3. setup_logging()

**签名**:

```python
def setup_logging(
    log_dir: str,
    log_level: str = 'INFO',
    date: str = None
) -> None:
    """配置日志系统
    
    Args:
        log_dir: 日志目录
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        date: 日期（用于日志文件命名，默认今天）
        
    Side Effects:
        - 创建日志目录（如不存在）
        - 配置日志格式
        - 配置文件处理器（写入文件）
        - 配置控制台处理器（输出到终端）
        
    Log Format:
        2025-01-15 11:05:23 [INFO] [src.fetcher] ARKK 数据下载成功
        
        包含:
        - 时间戳（YYYY-MM-DD HH:MM:SS）
        - 日志级别
        - 模块名称
        - 日志消息
        
    Log File Naming:
        {log_dir}/{YYYY-MM-DD}.log
    """
    pass
```

**Example Usage**:

```python
from src.utils import setup_logging

setup_logging(
    log_dir='./logs',
    log_level='INFO'
)

import logging
logger = logging.getLogger(__name__)

logger.info("系统启动")
logger.error("发生错误")
```

---

### 4. cleanup_old_logs()

**签名**:

```python
def cleanup_old_logs(log_dir: str, retention_days: int) -> int:
    """清理过期日志文件
    
    Args:
        log_dir: 日志目录
        retention_days: 保留天数
        
    Returns:
        删除的文件数量
        
    Implementation Details:
        1. 遍历日志目录下的 .log 文件
        2. 解析文件名中的日期（YYYY-MM-DD.log）
        3. 计算文件年龄
        4. 删除超过 retention_days 的文件
        5. 记录删除操作到日志
    """
    pass
```

**Example Usage**:

```python
from src.utils import cleanup_old_logs

deleted_count = cleanup_old_logs('./logs', retention_days=30)
print(f"清理了 {deleted_count} 个过期日志文件")
```

---

### 5. get_current_date()

**签名**:

```python
def get_current_date(timezone: str = 'Asia/Shanghai') -> str:
    """获取当前日期（指定时区）
    
    Args:
        timezone: 时区（默认北京时间）
        
    Returns:
        日期字符串 YYYY-MM-DD
        
    Implementation Details:
        1. 获取当前 UTC 时间
        2. 转换到指定时区
        3. 格式化为 YYYY-MM-DD
        
    Note:
        - 使用 datetime 库，无需外部时区库（pytz）
        - 简化实现：假设运行环境时区为北京时间
    """
    pass
```

**Example Usage**:

```python
from src.utils import get_current_date

today = get_current_date()
print(today)  # "2025-01-15"
```

---

### 6. get_previous_date()

**签名**:

```python
def get_previous_date(date: str, days: int = 1) -> str:
    """获取前 N 天的日期
    
    Args:
        date: 日期字符串 YYYY-MM-DD
        days: 向前推移天数（默认 1）
        
    Returns:
        前 N 天日期 YYYY-MM-DD
        
    Examples:
        get_previous_date('2025-01-15', 1)  # '2025-01-14'
        get_previous_date('2025-01-15', 7)  # '2025-01-08'
    """
    pass
```

**Example Usage**:

```python
from src.utils import get_previous_date

yesterday = get_previous_date('2025-01-15')
print(yesterday)  # "2025-01-14"

last_week = get_previous_date('2025-01-15', days=7)
print(last_week)  # "2025-01-08"
```

---

### 7. is_weekday()

**签名**:

```python
def is_weekday(date: str) -> bool:
    """判断是否为工作日（周一到周五）
    
    Args:
        date: 日期字符串 YYYY-MM-DD
        
    Returns:
        True: 工作日
        False: 周末
        
    Implementation Details:
        1. 解析日期字符串
        2. 获取星期几（0=周一，6=周日）
        3. 判断是否在 0-4 范围
    """
    pass
```

**Example Usage**:

```python
from src.utils import is_weekday

print(is_weekday('2025-01-15'))  # True (周三)
print(is_weekday('2025-01-18'))  # False (周六)
```

---

### 8. get_recent_dates()

**签名**:

```python
def get_recent_dates(
    days: int = 7,
    end_date: str = None,
    weekdays_only: bool = True
) -> List[str]:
    """获取最近 N 天的日期列表
    
    Args:
        days: 天数（默认 7）
        end_date: 结束日期（默认今天）
        weekdays_only: 是否仅返回工作日（默认 True）
        
    Returns:
        日期列表 YYYY-MM-DD（按时间升序）
        
    Example:
        get_recent_dates(7)  
        # ['2025-01-08', '2025-01-09', '2025-01-10', 
        #  '2025-01-13', '2025-01-14', '2025-01-15']
        # (排除了 2025-01-11 和 2025-01-12 周末)
    """
    pass
```

**Example Usage**:

```python
from src.utils import get_recent_dates

# 最近 7 个工作日
dates = get_recent_dates(days=7, weekdays_only=True)
print(dates)  # ['2025-01-08', '2025-01-09', ...]

# 最近 7 天（包括周末）
all_dates = get_recent_dates(days=7, weekdays_only=False)
print(all_dates)  # ['2025-01-08', '2025-01-09', ..., '2025-01-15']
```

---

### 9. format_number()

**签名**:

```python
def format_number(value: float, precision: int = 2, use_abbreviation: bool = False) -> str:
    """格式化数字（保留小数位、添加千位分隔符、缩写）
    
    Args:
        value: 数值
        precision: 小数位数（默认 2）
        use_abbreviation: 是否使用 M/K 缩写（默认 False）
        
    Returns:
        格式化后的字符串
        
    Examples:
        format_number(3245678.0, precision=2)  
        # "3,245,678.00"
        
        format_number(3245678.0, use_abbreviation=True)  
        # "3.25M"
        
        format_number(850123456.78, use_abbreviation=True)  
        # "850.12M"
    """
    pass
```

**Example Usage**:

```python
from src.utils import format_number

# 千位分隔符
print(format_number(3245678.0))  # "3,245,678.00"

# M/K 缩写
print(format_number(3245678.0, use_abbreviation=True))  # "3.25M"
print(format_number(50000.0, use_abbreviation=True))  # "50.00K"
```

---

### 10. ensure_dir_exists()

**签名**:

```python
def ensure_dir_exists(path: str) -> None:
    """确保目录存在（不存在则创建）
    
    Args:
        path: 目录路径
        
    Side Effects:
        - 创建目录及父目录（递归创建）
        - 如目录已存在，不做任何操作
        
    Implementation:
        使用 os.makedirs(path, exist_ok=True)
    """
    pass
```

**Example Usage**:

```python
from src.utils import ensure_dir_exists

ensure_dir_exists('./data/holdings/ARKK')
# 结果：创建 data/ → holdings/ → ARKK/ 三级目录
```

---

## Private Helper Functions

### _replace_env_vars()

```python
def _replace_env_vars(obj: Any) -> Any:
    """递归替换配置中的环境变量引用
    
    Args:
        obj: 配置对象（dict/list/str）
        
    Returns:
        替换后的对象
        
    Implementation:
        1. 如果是 dict，递归处理每个值
        2. 如果是 list，递归处理每个元素
        3. 如果是 str，查找 ${VAR} 模式并替换
        4. 其他类型直接返回
        
    Pattern:
        ${VAR_NAME} → os.getenv('VAR_NAME', '')
    """
    import re
    import os
    
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, obj)
        for var_name in matches:
            env_value = os.getenv(var_name, '')
            obj = obj.replace(f'${{{var_name}}}', env_value)
        return obj
    else:
        return obj
```

---

## Testing

```python
# tests/test_utils.py

def test_load_config():
    """测试配置加载"""
    config = load_config('config.yaml')
    
    assert isinstance(config, Config)
    assert config.schedule.cron_time == "11:00"
    assert len(config.data.etfs) == 5

def test_validate_config_missing_webhook():
    """测试 Webhook URL 缺失验证"""
    config = Config(notification=NotificationConfig(webhook_url=''))
    
    with pytest.raises(ValueError, match="未配置 WECHAT_WEBHOOK_URL"):
        validate_config(config)

def test_get_previous_date():
    """测试日期计算"""
    assert get_previous_date('2025-01-15', 1) == '2025-01-14'
    assert get_previous_date('2025-01-15', 7) == '2025-01-08'

def test_is_weekday():
    """测试工作日判断"""
    assert is_weekday('2025-01-15') is True  # 周三
    assert is_weekday('2025-01-18') is False  # 周六

def test_get_recent_dates():
    """测试最近日期列表"""
    with freeze_time("2025-01-15"):
        dates = get_recent_dates(days=7, weekdays_only=True)
        assert len(dates) == 5  # 排除 2 个周末
        assert '2025-01-11' not in dates  # 周六
        assert '2025-01-12' not in dates  # 周日

def test_cleanup_old_logs(tmp_path):
    """测试日志清理"""
    # 创建测试日志文件
    (tmp_path / '2024-12-01.log').touch()  # 过期
    (tmp_path / '2025-01-10.log').touch()  # 未过期
    
    with freeze_time("2025-01-15"):
        deleted = cleanup_old_logs(str(tmp_path), retention_days=7)
        assert deleted == 1
        assert (tmp_path / '2025-01-10.log').exists()
        assert not (tmp_path / '2024-12-01.log').exists()

def test_format_number():
    """测试数字格式化"""
    assert format_number(3245678.0, precision=2) == "3,245,678.00"
    assert format_number(3245678.0, use_abbreviation=True) == "3.25M"
    assert format_number(50000.0, use_abbreviation=True) == "50.00K"
```

---

## Dependencies

- **os**: 文件系统操作
- **json**: 配置文件解析（push_status.json）
- **yaml**: YAML 配置文件解析
- **logging**: 日志系统
- **datetime**: 日期时间处理
- **re**: 正则表达式（环境变量替换）
- **dotenv**: 环境变量加载

---

## Performance Considerations

- **配置加载**: <0.01 秒（包含环境变量替换）
- **日期计算**: <0.001 秒
- **日志清理**: <0.1 秒（扫描 100 个文件）

---

**Contract Status**: ✅ Defined | **Last Updated**: 2025-11-13
