# Implementation Plan: ARK 持仓监控与企微推送系统

**Branch**: `001-ark-monitor` | **Date**: 2025-11-13 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-ark-monitor/spec.md`

---

## Summary

构建本地优先的 ARK 基金持仓监控系统，通过 Python 每日自动下载 ARK 旗下 5 只 ETF（ARKK、ARKW、ARKG、ARKQ、ARKF）的最新持仓数据，分析持仓变化（新增、移除、增减持），生成可视化长图报告和汇总分析并推送到企业微信。系统采用 **本地 Launchd + CSV 存储 + 配置文件驱动** 架构，支持趋势图生成和手动补偿机制，无需云函数或数据库依赖。

**核心技术方案**:
- **数据采集**: requests 库从 ARKFunds.io API 获取数据，pandas 解析和存储
- **持仓分析**: pandas DataFrame 对比算法（merge + 阈值过滤）+ 跨基金重叠分析
- **报告生成**: Python f-string 模板生成 Markdown（单基金 + 汇总）
- **趋势图生成**: matplotlib + Pillow 生成长图（基金趋势 + 个股趋势）
- **消息推送**: 企业微信 Webhook API（Markdown + 图片，每日 6 条消息）
- **定时调度**: macOS Launchd 任务（本地执行）+ 状态文件防重复推送
- **配置管理**: PyYAML 读取 config.yaml + python-dotenv 读取 .env

---

## Technical Context

**Language/Version**: Python 3.9+  
**Primary Dependencies**: 
- pandas 2.0+ (数据处理)
- requests 2.31+ (HTTP 请求)
- python-dotenv 1.0+ (环境变量)
- PyYAML 6.0+ (配置文件)
- matplotlib 3.7+ (趋势图绘制)
- Pillow 10.0+ (图片拼接)

**Storage**: 
- CSV 文件（持仓数据）: `data/holdings/{ETF}/{YYYY-MM-DD}.csv`
- JSON 文件（推送状态）: `data/cache/push_status.json`
- PNG 文件（长图报告）: `data/images/{ETF}/{YYYY-MM-DD}_comprehensive.png`
- PNG 文件（汇总长图）: `data/images/SUMMARY/{YYYY-MM-DD}_summary.png`
- YAML 文件（配置）: `config.yaml`

**Testing**: pytest 7.0+ (单元测试 + 集成测试)  
**Target Platform**: macOS (开发环境) + Linux（未来可选）  
**Project Type**: 单一项目（CLI 工具）  
**Performance Goals**: 
- 单次完整任务 ≤60 秒（5 只 ETF）
- 单个 ETF 下载 ≤5 秒（正常网络）
- 内存占用 <128MB

**Constraints**: 
- 轻量级：仅 6 个核心依赖，禁止引入 ORM/Web 框架/数据库
- 本地优先：所有逻辑在本地执行，无云服务依赖
- 简洁性：8 模块架构（原 5+1 + 汇总分析 + 汇总通知 + 图片生成），模块职责固定

**Scale/Scope**: 
- 监控 5 只 ETF
- 每只 ETF 平均 40 只持仓股票
- 日志保留 30 天
- 持仓数据永久保留（年增长 ~20MB）

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 通过项 ✅

1. **Article I (可靠性优先)**: 
   - ✅ 3次重试机制（网络请求 + Webhook 推送）
   - ✅ 部分成功策略（单个 ETF 失败不阻塞其他）
   - ✅ 幂等性保证（状态文件防重复推送）
   
2. **Article II (模块化)**: 
   - ✅ 5+1 架构（DataFetcher, Analyzer, ReportGenerator, WeChatNotifier, Scheduler, Utils）
   - ✅ 每个模块单一职责，独立可测试
   - ✅ 类型提示 + 文档字符串强制要求

3. **Article III (配置驱动)**: 
   - ✅ config.yaml 管理非敏感配置
   - ✅ .env 管理敏感配置（Webhook URL）
   - ✅ 启动时配置验证

4. **Article IV (数据完整性)**: 
   - ✅ 不可变历史（CSV 文件永不覆盖）
   - ✅ 严格文件命名（YYYY-MM-DD.csv）
   - ✅ 结构化日志（时间戳 + 上下文）

5. **Article V (用户中心)**: 
   - ✅ 分层信息架构（摘要 → 详情 → 完整列表）
   - ✅ 阈值过滤（可配置，默认 ±5%）
   - ✅ 字符长度控制（<4096）

6. **Article VI (性能效率)**: 
   - ✅ 执行时间预算（总计 60 秒）
   - ✅ 内存优化（<128MB）
   - ✅ I/O 优化（单次读取，批量写入）

7. **Article VII (防御式错误处理)**: 
   - ✅ 错误分类与响应策略
   - ✅ 部分成功策略
   - ✅ 日志轮转（按日分割，自动清理）

8. **技术栈约束**: 
   - ✅ Python 3.9+
   - ✅ 仅 4 个核心依赖（pandas, requests, python-dotenv, PyYAML）
   - ✅ 禁止异步框架/ORM/Web 框架/数据库

### 无违规项 🎉

本项目完全符合 Constitution 要求，无需复杂度豁免。

---

## Project Structure

### Documentation (this feature)

```text
specs/001-ark-monitor/
├── plan.md              # 本文件 (/speckit.plan 输出)
├── spec.md              # 功能规范（已完成）
├── research.md          # Phase 0 技术调研（下方生成）
├── data-model.md        # Phase 1 数据模型设计（下方生成）
├── quickstart.md        # Phase 1 快速开始指南（下方生成）
├── contracts/           # Phase 1 模块接口契约（下方生成）
│   ├── fetcher.md
│   ├── analyzer.md
│   ├── reporter.md
│   ├── notifier.md
│   ├── scheduler.md
│   └── utils.md
└── tasks.md             # Phase 2 任务列表（稍后通过 /speckit.tasks 生成）
```

### Source Code (repository root)

```text
Wood-ARK/
├── config.yaml              # 配置文件（非敏感）
├── config.yaml.example      # 配置模板
├── .env                     # 环境变量（敏感，gitignore）
├── .env.example             # 环境变量模板
├── requirements.txt         # Python 依赖
├── main.py                  # 程序入口
│
├── src/                     # 核心模块
│   ├── __init__.py
│   ├── fetcher.py           # DataFetcher 类
│   ├── analyzer.py          # Analyzer 类
│   ├── reporter.py          # ReportGenerator 类
│   ├── notifier.py          # WeChatNotifier 类
│   ├── scheduler.py         # Scheduler 类
│   └── utils.py             # 工具函数（日期处理、日志配置等）
│
├── data/                    # 数据存储（gitignore）
│   ├── holdings/            # 持仓数据
│   │   ├── ARKK/
│   │   │   ├── 2025-01-10.csv
│   │   │   └── 2025-01-11.csv
│   │   ├── ARKW/
│   │   ├── ARKG/
│   │   ├── ARKQ/
│   │   └── ARKF/
│   ├── reports/             # 本地报告备份
│   │   └── {ETF}/
│   │       └── {YYYY-MM-DD}.md
│   └── cache/               # 状态文件
│       └── push_status.json
│
├── logs/                    # 日志文件（gitignore）
│   ├── 2025-01-10.log
│   └── 2025-01-11.log
│
├── tests/                   # 测试代码
│   ├── __init__.py
│   ├── test_fetcher.py
│   ├── test_analyzer.py
│   ├── test_reporter.py
│   ├── test_notifier.py
│   ├── test_scheduler.py
│   ├── test_utils.py
│   ├── test_integration.py  # 端到端集成测试
│   └── fixtures/            # 测试数据
│       ├── sample_arkk_2025-01-10.csv
│       ├── sample_arkk_2025-01-11.csv
│       └── expected_report.md
│
├── scripts/                 # 辅助脚本
│   ├── install_cron.sh      # 安装 cron 任务
│   ├── uninstall_cron.sh    # 卸载 cron 任务
│   └── cleanup_logs.sh      # 手动清理过期日志
│
└── docs/                    # 项目文档
    ├── README.md            # 项目说明
    ├── CHANGELOG.md         # 版本变更日志
    └── TROUBLESHOOTING.md   # 常见问题排查
```

**Structure Decision**: 采用 **单一项目结构**（Option 1），因为：
1. 本项目是纯后台 CLI 工具，无前端/后端分离需求
2. 5+1 模块架构可通过单个 `src/` 目录清晰组织
3. 测试代码和源代码 1:1 对应，便于维护
4. 符合 Constitution 的简洁性原则

---

## Phase 0: Technical Research

### 研究目标

在编写任何代码前，需验证以下技术可行性：

1. **ARK CSV 数据源可用性** 
   - 验证 URL `https://ark-funds.com/wp-content/fundsiteliterature/csv/ARKK_HOLDINGS.csv` 可正常下载
   - 检查 CSV 格式是否包含必需字段：company, ticker, shares, market value, weight
   - 确认数据更新频率（预期每日更新）

2. **企业微信 Webhook API**
   - 验证 Markdown 格式消息推送能力
   - 测试 4096 字符长度限制
   - 确认重试机制是否影响推送成功率

3. **pandas 持仓对比算法**
   - 验证 DataFrame.merge() 能高效处理 200 行数据对比
   - 确认计算性能满足 <5 秒要求
   - 测试边界场景（新增 ETF、完全清仓某股票）

4. **cron 定时任务可靠性**
   - 验证 macOS cron 是否支持精确到分钟的调度
   - 测试电脑休眠唤醒后 cron 任务是否能正常触发
   - 确认 cron 环境变量是否能正确加载 Python 虚拟环境

5. **PyYAML 配置热更新**
   - 验证每次执行时重新加载 config.yaml 无性能问题
   - 测试 YAML 格式错误时的异常处理
   - 确认环境变量替换语法 `${VAR}` 是否需要额外处理

### 研究交付物

输出文件：`specs/001-ark-monitor/research.md`

**必须包含**:
- [ ] ARK CSV 数据样本（前 5 行）
- [ ] 字段映射表（CSV 列名 → Python 属性名）
- [ ] 企业微信 Webhook 测试结果（成功响应示例）
- [ ] pandas 对比算法伪代码
- [ ] cron 配置示例（带注释）
- [ ] 已知限制和风险（如 CSV 格式变更风险）

---

## Phase 1: Detailed Design

### 1.1 Data Model

输出文件：`specs/001-ark-monitor/data-model.md`

**必须定义**:

1. **HoldingRecord** - 单条持仓记录
   ```python
   @dataclass
   class HoldingRecord:
       date: str           # YYYY-MM-DD
       etf_symbol: str     # ARKK/ARKW/ARKG/ARKQ/ARKF
       company: str        # 公司名称
       ticker: str         # 股票代码
       shares: float       # 持股数量
       market_value: float # 市值（美元）
       weight: float       # 权重（百分比）
   ```

2. **ChangeAnalysis** - 持仓变化分析结果
   ```python
   @dataclass
   class ChangeAnalysis:
       etf_symbol: str
       current_date: str
       previous_date: str
       added: List[HoldingRecord]        # 新增股票
       removed: List[HoldingRecord]      # 移除股票
       increased: List[ChangedHolding]   # 增持股票
       decreased: List[ChangedHolding]   # 减持股票
       top5_holdings: List[HoldingRecord]  # 前 5 大持仓
   
   @dataclass
   class ChangedHolding:
       ticker: str
       company: str
       previous_shares: float
       current_shares: float
       change_pct: float      # 变化百分比
       previous_weight: float
       current_weight: float
   ```

3. **PushStatus** - 推送状态记录
   ```python
   @dataclass
   class PushStatus:
       date: str              # YYYY-MM-DD
       pushed_at: str         # ISO 8601 时间戳
       success: bool
       etfs_processed: List[str]
       error_message: Optional[str]
   ```

4. **Config** - 配置对象
   ```python
   @dataclass
   class Config:
       # Schedule
       schedule_enabled: bool
       cron_time: str
       timezone: str
       
       # Data
       etfs: List[str]
       data_dir: str
       log_dir: str
       
       # Analysis
       change_threshold: float
       
       # Notification
       webhook_url: str
       enable_error_alert: bool
       
       # Retry
       max_retries: int
       retry_delays: List[int]
       
       # Log
       retention_days: int
       log_level: str
   ```

### 1.2 Module Contracts

输出文件：`specs/001-ark-monitor/contracts/`

#### fetcher.md - DataFetcher 接口

```python
class DataFetcher:
    """负责从 ARK 官网下载和保存持仓数据"""
    
    def __init__(self, config: Config):
        """初始化 DataFetcher
        
        Args:
            config: 系统配置对象
        """
        pass
    
    def fetch_holdings(self, etf_symbol: str, date: str) -> pd.DataFrame:
        """下载指定 ETF 和日期的持仓数据
        
        Args:
            etf_symbol: ETF 代码（如 'ARKK'）
            date: 日期字符串 YYYY-MM-DD
            
        Returns:
            包含持仓数据的 DataFrame，列名：
            ['company', 'ticker', 'cusip', 'shares', 'market_value', 'weight']
            
        Raises:
            requests.RequestException: 网络请求失败
            ValueError: CSV 格式不正确或缺少必需列
            
        Implementation Notes:
            - URL 模板：https://ark-funds.com/wp-content/fundsiteliterature/csv/{etf_symbol}_HOLDINGS.csv
            - 超时时间：30 秒
            - 重试机制：3 次，指数退避 [1, 2, 4] 秒
        """
        pass
    
    def save_to_csv(self, df: pd.DataFrame, etf_symbol: str, date: str) -> None:
        """保存持仓数据到 CSV 文件
        
        Args:
            df: 持仓数据 DataFrame
            etf_symbol: ETF 代码
            date: 日期字符串 YYYY-MM-DD
            
        Raises:
            IOError: 文件写入失败
            
        Side Effects:
            - 创建目录 data/holdings/{etf_symbol}/（如不存在）
            - 如文件已存在，记录警告日志但不覆盖
        """
        pass
    
    def load_from_csv(self, etf_symbol: str, date: str) -> pd.DataFrame:
        """从本地 CSV 文件加载持仓数据
        
        Args:
            etf_symbol: ETF 代码
            date: 日期字符串 YYYY-MM-DD
            
        Returns:
            持仓数据 DataFrame
            
        Raises:
            FileNotFoundError: 文件不存在
            pd.errors.ParserError: CSV 解析失败
        """
        pass
```

#### analyzer.md - Analyzer 接口

```python
class Analyzer:
    """负责持仓变化分析"""
    
    def __init__(self, threshold: float = 5.0):
        """初始化 Analyzer
        
        Args:
            threshold: 显著变化阈值（百分比，默认 5.0）
        """
        pass
    
    def compare_holdings(
        self, 
        current: pd.DataFrame, 
        previous: pd.DataFrame,
        etf_symbol: str,
        current_date: str,
        previous_date: str
    ) -> ChangeAnalysis:
        """对比两个日期的持仓变化
        
        Args:
            current: 当前持仓 DataFrame
            previous: 前一日持仓 DataFrame
            etf_symbol: ETF 代码
            current_date: 当前日期
            previous_date: 前一日期
            
        Returns:
            ChangeAnalysis 对象，包含新增、移除、增持、减持、前5持仓
            
        Algorithm:
            1. 使用 DataFrame.merge() 找出新增/移除/变化股票
            2. 计算持股数变化百分比
            3. 过滤显著变化（绝对值 >= threshold）
            4. 按权重降序排序前 5 大持仓
        """
        pass
```

#### reporter.md - ReportGenerator 接口

```python
class ReportGenerator:
    """负责生成 Markdown 报告"""
    
    def generate_markdown(
        self, 
        analyses: List[ChangeAnalysis],
        execution_time: str
    ) -> str:
        """生成完整的 Markdown 报告
        
        Args:
            analyses: 所有 ETF 的分析结果列表
            execution_time: 执行时间（如 '08:00:15'）
            
        Returns:
            Markdown 格式字符串
            
        Format:
            ## 🚀 ARK 持仓日报 (YYYY-MM-DD)
            
            ### 📊 整体概况
            - 监控 ETF: 5 只
            - 有变化: 3 只
            - 执行时间: 08:00:15
            
            ### 🔥 ARKK - 创新科技 ETF
            ... (详细变化)
            
        Character Limit:
            - 如超过 4096 字符，自动截断并提示
        """
        pass
    
    def save_report(
        self, 
        content: str, 
        etf_symbol: str, 
        date: str
    ) -> None:
        """保存报告到本地文件
        
        Args:
            content: Markdown 内容
            etf_symbol: ETF 代码
            date: 日期
            
        Side Effects:
            - 创建 data/reports/{etf_symbol}/{date}.md
        """
        pass
```

#### notifier.md - WeChatNotifier 接口

```python
class WeChatNotifier:
    """负责企业微信消息推送"""
    
    def __init__(self, webhook_url: str, max_retries: int = 3):
        """初始化 WeChatNotifier
        
        Args:
            webhook_url: 企业微信 Webhook URL
            max_retries: 最大重试次数
        """
        pass
    
    def send_markdown(self, content: str) -> bool:
        """发送 Markdown 消息
        
        Args:
            content: Markdown 文本
            
        Returns:
            True 表示成功，False 表示失败
            
        Request Body:
            {
                "msgtype": "markdown",
                "markdown": {
                    "content": content
                }
            }
            
        Retry Strategy:
            - 3 次重试，每次间隔 5 秒
            - 如持续失败，记录错误日志并返回 False
        """
        pass
    
    def send_error_alert(self, error_message: str) -> bool:
        """发送错误告警（可选）
        
        Args:
            error_message: 错误描述
            
        Returns:
            True 表示成功
        """
        pass
```

#### scheduler.md - Scheduler 接口

```python
class Scheduler:
    """负责任务调度和流程编排"""
    
    def __init__(self, config: Config):
        """初始化 Scheduler
        
        Args:
            config: 系统配置对象
        """
        pass
    
    def should_run_today(self) -> bool:
        """判断今天是否应该运行（周一到周五）
        
        Returns:
            True 表示应运行，False 表示跳过
        """
        pass
    
    def get_previous_trading_day(self, current_date: str) -> str:
        """获取上一个交易日
        
        Args:
            current_date: 当前日期 YYYY-MM-DD
            
        Returns:
            上一交易日期（简化实现：前一天，不考虑节假日）
            
        Note:
            - 初版实现：简单返回前一天
            - 未来增强：调用交易日历 API
        """
        pass
    
    def check_missed_dates(self, days: int = 7) -> List[str]:
        """检测最近 N 天内缺失的持仓数据日期
        
        Args:
            days: 检测天数（默认 7）
            
        Returns:
            缺失日期列表（YYYY-MM-DD）
            
        Algorithm:
            1. 遍历最近 7 天
            2. 检查 data/holdings/ARKK/{date}.csv 是否存在
            3. 返回不存在的日期列表
        """
        pass
    
    def is_already_pushed(self, date: str) -> bool:
        """检查指定日期是否已推送
        
        Args:
            date: 日期 YYYY-MM-DD
            
        Returns:
            True 表示已推送
            
        Implementation:
            - 读取 data/cache/push_status.json
            - 检查日期是否存在且 success=True
        """
        pass
    
    def mark_pushed(self, date: str, success: bool, etfs: List[str]) -> None:
        """标记推送状态
        
        Args:
            date: 日期
            success: 是否成功
            etfs: 处理的 ETF 列表
            
        Side Effects:
            - 更新 data/cache/push_status.json
        """
        pass
```

#### utils.md - Utils 工具函数

```python
def setup_logging(log_dir: str, log_level: str = 'INFO') -> None:
    """配置日志系统
    
    Args:
        log_dir: 日志目录
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        
    Side Effects:
        - 创建日志目录（如不存在）
        - 配置日志格式：时间戳 + 级别 + 模块 + 消息
        - 日志文件命名：{YYYY-MM-DD}.log
    """
    pass

def cleanup_old_logs(log_dir: str, retention_days: int) -> None:
    """清理过期日志文件
    
    Args:
        log_dir: 日志目录
        retention_days: 保留天数
        
    Side Effects:
        - 删除 retention_days 天前的日志文件
    """
    pass

def get_current_date() -> str:
    """获取当前日期（北京时间）
    
    Returns:
        YYYY-MM-DD 格式字符串
    """
    pass

def get_previous_date(date: str) -> str:
    """获取前一天日期
    
    Args:
        date: YYYY-MM-DD 格式日期
        
    Returns:
        前一天日期（YYYY-MM-DD）
    """
    pass

def load_config(config_path: str = 'config.yaml') -> Config:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Config 对象
        
    Raises:
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: YAML 格式错误
        ValueError: 必需配置缺失或格式错误
        
    Implementation:
        1. 加载 .env 文件（python-dotenv）
        2. 读取 config.yaml（PyYAML）
        3. 替换 ${VAR} 语法为环境变量值
        4. 验证必需配置（webhook_url）
        5. 返回 Config 对象
    """
    pass

def validate_config(config: Config) -> None:
    """验证配置完整性
    
    Args:
        config: Config 对象
        
    Raises:
        ValueError: 配置不合法（含详细错误信息）
        
    Checks:
        - webhook_url 非空且格式正确
        - change_threshold 在 0.1-100 范围
        - etfs 列表非空
        - 目录路径有效
    """
    pass
```

### 1.3 Quickstart Guide

输出文件：`specs/001-ark-monitor/quickstart.md`

**必须包含**:

1. **安装步骤**
   ```bash
   # 1. 克隆项目
   git clone <repo_url>
   cd Wood-ARK
   
   # 2. 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 3. 安装依赖
   pip install -r requirements.txt
   
   # 4. 配置环境变量
   cp .env.example .env
   # 编辑 .env，填写 WECHAT_WEBHOOK_URL
   
   # 5. 配置系统参数
   cp config.yaml.example config.yaml
   # 根据需要调整配置（可选）
   ```

2. **测试 Webhook**
   ```bash
   python main.py --test-webhook
   # 预期输出：✅ Webhook 连接正常
   ```

3. **手动执行一次**
   ```bash
   python main.py --manual
   # 预期：下载数据 → 分析 → 推送到企业微信
   ```

4. **安装 cron 任务**
   ```bash
   ./scripts/install_cron.sh
   # 验证安装
   crontab -l
   ```

5. **常见问题**
   - 网络代理配置
   - cron 环境变量问题
   - 企业微信群机器人创建

---

## Phase 2: Implementation Tasks

**Note**: 任务列表通过 `/speckit.tasks` 命令生成，输出到 `specs/001-ark-monitor/tasks.md`

**预期任务分解**（示例，最终由 /speckit.tasks 生成）:

1. **Setup (1 task)**
   - [ ] 创建项目目录结构、requirements.txt、配置文件模板

2. **Core Modules (6 tasks)**
   - [ ] 实现 utils.py（配置加载、日志、日期工具）
   - [ ] 实现 fetcher.py（下载 + 保存 + 加载 CSV）
   - [ ] 实现 analyzer.py（持仓对比算法）
   - [ ] 实现 reporter.py（Markdown 生成）
   - [ ] 实现 notifier.py（企业微信推送）
   - [ ] 实现 scheduler.py（调度逻辑 + 状态管理）

3. **CLI Interface (1 task)**
   - [ ] 实现 main.py（命令行参数解析 + 流程编排）

4. **Testing (7 tasks)**
   - [ ] 准备测试 fixtures（样本 CSV、期望报告）
   - [ ] 单元测试：test_fetcher.py
   - [ ] 单元测试：test_analyzer.py
   - [ ] 单元测试：test_reporter.py
   - [ ] 单元测试：test_notifier.py
   - [ ] 单元测试：test_scheduler.py
   - [ ] 集成测试：test_integration.py

5. **Deployment (2 tasks)**
   - [ ] 编写 scripts/install_cron.sh
   - [ ] 编写 docs/README.md 和 docs/TROUBLESHOOTING.md

**总计**: ~17 个任务

---

## Complexity Tracking

> **当前状态**: ✅ 无 Constitution 违规，无需复杂度豁免

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| N/A       | N/A        | N/A                                  |

---

## Risk Mitigation

| 风险 | 应对措施 |
|------|---------|
| ARK URL 变更 | 通过配置文件支持自定义 URL 模板；增加下载失败告警 |
| CSV 格式变更 | 增加格式校验；保留旧版解析兼容；发送告警 |
| cron 任务失效 | 提供 `--check-missed` 补偿命令；文档提醒定期检查 |
| 电脑长期关机 | 文档说明手动补偿流程；可选云函数备份（未来增强） |

---

## Next Steps

1. ✅ Constitution Check 已通过
2. ⏭️ 执行 Phase 0: 创建 `research.md`（技术调研）
3. ⏭️ 执行 Phase 1: 创建 `data-model.md` + `contracts/` + `quickstart.md`
4. ⏭️ 执行 `/speckit.tasks` 生成任务列表
5. ⏭️ 执行 `/speckit.implement` 开始编码

---

**Plan Status**: ✅ Ready for Phase 0 Research

