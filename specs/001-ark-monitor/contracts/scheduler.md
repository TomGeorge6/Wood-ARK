# Module Contract: Scheduler

**Module**: `src/scheduler.py`  
**Purpose**: 负责任务调度、流程编排和状态管理

---

## Class Definition

```python
class Scheduler:
    """任务调度器"""
    
    def __init__(self, config: Config):
        """初始化 Scheduler
        
        Args:
            config: 系统配置对象
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
```

---

## Public Methods

### 1. should_run_today()

**签名**:

```python
def should_run_today(self) -> bool:
    """判断今天是否应该运行（周一到周五）
    
    Returns:
        True: 应运行（工作日且配置启用）
        False: 跳过（周末或配置禁用）
        
    Implementation Details:
        1. 检查 config.schedule.enabled
        2. 检查当前是否为工作日（周一=0 到 周五=4）
        3. 返回结果
        
    Note:
        - 本方法仅检查星期几，不考虑节假日
        - 未来可增强：调用交易日历 API 判断美股交易日
    """
    pass
```

**Example Usage**:

```python
scheduler = Scheduler(config)

if scheduler.should_run_today():
    print("今天是工作日，执行任务")
else:
    print("今天是周末，跳过任务")
```

---

### 2. get_previous_trading_day()

**签名**:

```python
def get_previous_trading_day(self, current_date: str) -> str:
    """获取上一个交易日
    
    Args:
        current_date: 当前日期 YYYY-MM-DD
        
    Returns:
        上一交易日期 YYYY-MM-DD
        
    Implementation Details:
        - 简化实现：直接返回前一天
        - 未来增强：考虑周末和节假日
        
    Examples:
        - 2025-01-15（周三） → 2025-01-14（周二）
        - 2025-01-13（周一） → 2025-01-10（周五）[未来增强]
        - 当前版本：2025-01-13 → 2025-01-12（简化）
    """
    pass
```

**Example Usage**:

```python
scheduler = Scheduler(config)

previous_date = scheduler.get_previous_trading_day('2025-01-15')
print(previous_date)  # 2025-01-14
```

---

### 3. check_missed_dates()

**签名**:

```python
def check_missed_dates(self, days: int = 7) -> List[str]:
    """检测最近 N 天内缺失的持仓数据日期
    
    Args:
        days: 检测天数（默认 7 天）
        
    Returns:
        缺失日期列表 YYYY-MM-DD（按时间升序）
        
    Algorithm:
        1. 获取最近 7 天的日期列表
        2. 过滤掉周末（周六、周日）
        3. 遍历每个工作日
        4. 检查 data/holdings/ARKK/{date}.csv 是否存在
        5. 如不存在，添加到缺失列表
        6. 返回缺失列表
        
    Implementation Details:
        - 仅检查 ARKK（代表性 ETF）
        - 如 ARKK 数据存在，假设其他 ETF 也存在
        - 简化实现：仅过滤周末，不考虑节假日
    """
    pass
```

**Example Usage**:

```python
scheduler = Scheduler(config)

missed = scheduler.check_missed_dates(days=7)
if missed:
    print(f"检测到 {len(missed)} 个缺失日期: {', '.join(missed)}")
    for date in missed:
        # 补偿下载和推送
        process_date(date)
else:
    print("无缺失数据")
```

---

### 4. is_already_pushed()

**签名**:

```python
def is_already_pushed(self, date: str) -> bool:
    """检查指定日期是否已推送报告
    
    Args:
        date: 日期 YYYY-MM-DD
        
    Returns:
        True: 已推送
        False: 未推送或推送失败
        
    Implementation Details:
        1. 读取 data/cache/push_status.json
        2. 查找日期对应的记录
        3. 检查 success 字段
        4. 返回结果
        
    File Format:
        {
            "2025-01-15": {
                "pushed_at": "2025-01-15T11:05:23+08:00",
                "success": true,
                "etfs_processed": ["ARKK", "ARKW", ...],
                "error_message": null
            }
        }
    """
    pass
```

**Example Usage**:

```python
scheduler = Scheduler(config)

if scheduler.is_already_pushed('2025-01-15'):
    print("今天已推送，跳过")
else:
    print("今天未推送，执行任务")
```

---

### 5. mark_pushed()

**签名**:

```python
def mark_pushed(
    self,
    date: str,
    success: bool,
    etfs: List[str],
    error_message: str = None
) -> None:
    """标记推送状态
    
    Args:
        date: 日期 YYYY-MM-DD
        success: 是否成功
        etfs: 已处理的 ETF 列表
        error_message: 错误信息（失败时）
        
    Side Effects:
        - 更新 data/cache/push_status.json
        - 保留最近 30 天记录
        - 自动创建文件（如不存在）
        
    Implementation Details:
        1. 读取现有状态文件（如不存在则初始化为 {}）
        2. 添加/更新日期记录
        3. 清理 30 天前的记录
        4. 写入文件
    """
    pass
```

**Example Usage**:

```python
scheduler = Scheduler(config)

# 成功推送
scheduler.mark_pushed(
    date='2025-01-15',
    success=True,
    etfs=['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']
)

# 失败推送
scheduler.mark_pushed(
    date='2025-01-15',
    success=False,
    etfs=['ARKK'],  # 仅 ARKK 成功
    error_message='ARKW 下载超时'
)
```

---

### 6. run_daily_task()

**签名**:

```python
def run_daily_task(
    self,
    fetcher: DataFetcher,
    analyzer: Analyzer,
    reporter: ReportGenerator,
    notifier: WeChatNotifier,
    force: bool = False,
    target_date: str = None
) -> bool:
    """执行每日任务（完整流程编排）
    
    Args:
        fetcher: 数据获取器
        analyzer: 分析器
        reporter: 报告生成器
        notifier: 推送器
        force: 是否强制执行（忽略工作日检查和已推送检查）
        target_date: 目标日期（默认今天）
        
    Returns:
        True: 任务成功
        False: 任务失败
        
    Workflow:
        1. 确定目标日期（默认今天）
        2. 检查是否应运行（工作日 + 未推送，除非 force=True）
        3. 遍历配置中的 ETF 列表
        4. 对每个 ETF：
           a. 下载当前持仓数据
           b. 加载前一日数据
           c. 分析持仓变化
           d. 累积分析结果
        5. 生成综合报告
        6. 推送到企业微信
        7. 标记推送状态
        8. 返回结果
        
    Error Handling:
        - 单个 ETF 失败不阻塞其他 ETF（部分成功策略）
        - 推送失败时保存报告到本地
        - 所有错误记录到日志
    """
    pass
```

**Example Usage**:

```python
scheduler = Scheduler(config)
fetcher = DataFetcher(config)
analyzer = Analyzer(config.analysis.change_threshold)
reporter = ReportGenerator()
notifier = WeChatNotifier(config.notification.webhook_url)

# 自动模式（遵循工作日检查）
success = scheduler.run_daily_task(fetcher, analyzer, reporter, notifier)

# 手动模式（强制执行）
success = scheduler.run_daily_task(
    fetcher, analyzer, reporter, notifier,
    force=True
)

# 指定日期模式
success = scheduler.run_daily_task(
    fetcher, analyzer, reporter, notifier,
    force=True,
    target_date='2025-01-10'
)
```

---

## Private Methods

### _load_push_status()

```python
def _load_push_status(self) -> dict:
    """加载推送状态文件
    
    Returns:
        状态字典（如文件不存在返回空字典）
    """
    status_file = os.path.join(
        self.config.data.data_dir,
        'cache',
        'push_status.json'
    )
    
    if not os.path.exists(status_file):
        return {}
    
    with open(status_file, 'r', encoding='utf-8') as f:
        return json.load(f)
```

### _save_push_status()

```python
def _save_push_status(self, status: dict) -> None:
    """保存推送状态到文件
    
    Side Effects:
        - 创建 cache 目录（如不存在）
        - 写入 push_status.json
    """
    cache_dir = os.path.join(self.config.data.data_dir, 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    status_file = os.path.join(cache_dir, 'push_status.json')
    
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
```

### _cleanup_old_status()

```python
def _cleanup_old_status(self, status: dict, retention_days: int = 30) -> dict:
    """清理过期的推送状态记录
    
    Args:
        status: 状态字典
        retention_days: 保留天数
        
    Returns:
        清理后的状态字典
    """
    from datetime import datetime, timedelta
    
    cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime('%Y-%m-%d')
    
    return {
        date: record
        for date, record in status.items()
        if date >= cutoff_date
    }
```

---

## Testing

```python
# tests/test_scheduler.py

def test_should_run_today_weekday():
    """测试工作日判断"""
    config = Config(schedule=ScheduleConfig(enabled=True))
    scheduler = Scheduler(config)
    
    # Mock 当前日期为周三
    with freeze_time("2025-01-15"):  # 周三
        assert scheduler.should_run_today() is True

def test_should_run_today_weekend():
    """测试周末判断"""
    config = Config(schedule=ScheduleConfig(enabled=True))
    scheduler = Scheduler(config)
    
    # Mock 当前日期为周六
    with freeze_time("2025-01-18"):  # 周六
        assert scheduler.should_run_today() is False

def test_check_missed_dates(tmp_path):
    """测试缺失日期检测"""
    config = Config(data=DataConfig(data_dir=str(tmp_path)))
    scheduler = Scheduler(config)
    
    # 创建部分日期的数据
    arkk_dir = tmp_path / 'holdings' / 'ARKK'
    arkk_dir.mkdir(parents=True)
    (arkk_dir / '2025-01-10.csv').touch()
    (arkk_dir / '2025-01-14.csv').touch()
    # 2025-01-13 缺失
    
    with freeze_time("2025-01-15"):
        missed = scheduler.check_missed_dates(days=7)
        assert '2025-01-13' in missed

def test_mark_pushed_creates_file(tmp_path):
    """测试标记推送创建文件"""
    config = Config(data=DataConfig(data_dir=str(tmp_path)))
    scheduler = Scheduler(config)
    
    scheduler.mark_pushed('2025-01-15', True, ['ARKK', 'ARKW'])
    
    status_file = tmp_path / 'cache' / 'push_status.json'
    assert status_file.exists()
    
    with open(status_file, 'r') as f:
        status = json.load(f)
        assert '2025-01-15' in status
        assert status['2025-01-15']['success'] is True

def test_run_daily_task_integration(mocker):
    """测试完整任务流程（集成测试）"""
    # Mock 所有依赖
    mock_fetcher = mocker.Mock()
    mock_analyzer = mocker.Mock()
    mock_reporter = mocker.Mock()
    mock_notifier = mocker.Mock()
    
    # 配置 Mock 返回值
    mock_fetcher.fetch_holdings.return_value = pd.DataFrame(...)
    mock_analyzer.compare_holdings.return_value = ChangeAnalysis(...)
    mock_reporter.generate_markdown.return_value = "# Test"
    mock_notifier.send_markdown.return_value = True
    
    scheduler = Scheduler(config)
    success = scheduler.run_daily_task(
        mock_fetcher, mock_analyzer, mock_reporter, mock_notifier,
        force=True
    )
    
    assert success is True
    assert mock_fetcher.fetch_holdings.call_count == 5  # 5 个 ETF
    assert mock_notifier.send_markdown.called
```

---

## State Management

### 推送状态文件结构

```json
{
  "2025-01-15": {
    "pushed_at": "2025-01-15T11:05:23+08:00",
    "success": true,
    "etfs_processed": ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"],
    "error_message": null
  },
  "2025-01-14": {
    "pushed_at": "2025-01-14T11:05:18+08:00",
    "success": true,
    "etfs_processed": ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"],
    "error_message": null
  },
  "2025-01-13": {
    "pushed_at": "2025-01-13T11:05:30+08:00",
    "success": false,
    "etfs_processed": ["ARKK", "ARKW"],
    "error_message": "ARKG 下载超时"
  }
}
```

### 状态清理策略

- **保留期**: 30 天
- **清理时机**: 每次 `mark_pushed()` 时自动清理
- **清理规则**: 删除 30 天前的记录

---

## Dependencies

- **os**: 文件路径操作
- **json**: 状态文件读写
- **datetime**: 日期计算
- **logging**: 日志记录

---

## Performance Considerations

- **状态文件大小**: ~1KB（30 天记录）
- **状态文件读写**: <0.01 秒
- **缺失日期检测**: <0.1 秒（检查 7 天）

---

**Contract Status**: ✅ Defined | **Last Updated**: 2025-11-13
