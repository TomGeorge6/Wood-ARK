# ARK 持仓监控与企微推送系统 - 项目设计文档

> **项目名称**: Wood-ARK Monitor  
> **版本**: v1.0.0  
> **创建日期**: 2025-01-12  
> **项目路径**: `/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK`

---

## 📋 目录

- [1. 项目背景](#1-项目背景)
- [2. 需求分析](#2-需求分析)
- [3. 技术方案](#3-技术方案)
- [4. 系统架构](#4-系统架构)
- [5. 功能模块设计](#5-功能模块设计)
- [6. 数据结构设计](#6-数据结构设计)
- [7. 消息格式设计](#7-消息格式设计)
- [8. 项目目录结构](#8-项目目录结构)
- [9. 部署方案](#9-部署方案)
- [10. 开发计划](#10-开发计划)
- [11. 附录](#11-附录)

---

## 1. 项目背景

### 1.1 业务背景

**ARK Invest** 是由 Cathie Wood（木头姐）创立的投资管理公司，以主动管理的颠覆性创新主题 ETF 而闻名。ARK 每日公开其持仓数据，这在基金行业中非常罕见，为投资者提供了宝贵的投资参考。

**当前痛点**:
- ARK 持仓数据分散在官网，需手动查看
- 持仓变化不直观，需对比多个 CSV 文件
- 无法及时获知重大持仓调整
- 缺少自动化的通知机制

### 1.2 项目目标

构建一个**本地化的 ARK 持仓监控系统**，实现：

1. **自动采集**: 每日自动获取 ARK 旗下 ETF 的最新持仓数据
2. **智能分析**: 对比前后持仓变化，识别新增/移除股票及重大调仓
3. **即时推送**: 通过企业微信 Webhook 推送每日持仓报告
4. **容错机制**: 支持手动触发、云端备份，应对电脑关机/断网场景
5. **历史回溯**: 整合历史数据，支持长期趋势分析

### 1.3 价值收益

- ⏱️ **节省时间**: 无需手动查看 ARK 官网，每日自动推送
- 📊 **提升效率**: 自动计算持仓变化，直观展示重点信息
- 🔔 **及时通知**: 第一时间获知木头姐的操作，辅助投资决策
- 📈 **数据积累**: 本地存储历史数据，支持长期分析

---

## 2. 需求分析

### 2.1 功能需求

| 编号 | 需求描述 | 优先级 |
|------|---------|--------|
| F01 | 每日自动下载 ARK 各 ETF 的最新持仓 CSV 数据 | P0 |
| F02 | 对比前后两日持仓，识别新增/移除的股票 | P0 |
| F03 | 计算持仓变化百分比，筛选重大调仓（阈值可配置） | P0 |
| F04 | 生成格式化的每日持仓报告（Markdown） | P0 |
| F05 | 通过企业微信群机器人 Webhook 推送报告 | P0 |
| F06 | 支持手动触发任务（命令行） | P1 |
| F07 | 本地定时任务（cron）自动执行 | P1 |
| F08 | 云函数备份机制（应对电脑关机） | P1 |
| F09 | 错过更新的自动补偿机制 | P2 |
| F10 | 历史数据回溯查询 | P2 |
| F11 | 数据可视化（图表生成） | P3 |

### 2.2 非功能需求

| 类型 | 需求描述 |
|------|---------|
| **性能** | 单次数据采集 + 分析 < 30 秒 |
| **可靠性** | 本地 + 云端双重保障，成功率 > 99% |
| **可维护性** | 模块化设计，日志完善，便于调试 |
| **安全性** | Webhook URL 等敏感信息通过 .env 管理 |
| **扩展性** | 易于增加新的 ETF 或通知渠道 |

### 2.3 约束条件

- **运行环境**: macOS（本地），Python 3.9+
- **数据来源**: ARK Invest 官网（公开数据）
- **更新时间**: 美东时间每日 19:00（北京时间次日 07:00-08:00）
- **网络依赖**: 需互联网访问 ARK 官网和企微 API
- **存储方式**: 本地 CSV 文件 + 可选云端备份（COS）

---

## 3. 技术方案

### 3.1 方案对比

我们对比了三种实现方案：

| 方案 | 架构 | 优点 | 缺点 | 评分 |
|------|------|------|------|------|
| **A. 纯本地** | cron + Python | 简单、私密、零成本 | 依赖电脑开机 | ⭐⭐⭐ |
| **B. 混合方案** | 本地优先 + 云函数备份 | 可靠、灵活、低成本 | 需配置云服务 | ⭐⭐⭐⭐⭐ |
| **C. 纯云端** | 云函数 + COS | 完全自动化 | 数据在云端 | ⭐⭐⭐⭐ |

**最终选择**: **方案 B - 混合方案**

**理由**:
1. 日常场景电脑开机时使用本地（快速、数据私密）
2. 电脑关机时云函数自动兜底（可靠性保障）
3. 云函数免费额度充足（月调用 30 次 << 100 万次额度）
4. 成本几乎为零（约 ¥0-1/月）

### 3.2 技术栈

#### 本地端

| 组件 | 技术选择 | 版本要求 | 用途 |
|------|---------|---------|------|
| **编程语言** | Python | 3.9+ | 主开发语言 |
| **数据处理** | pandas | 2.0+ | 数据分析与处理 |
| **HTTP 客户端** | requests | 2.31+ | 下载数据、推送企微 |
| **配置管理** | python-dotenv | 1.0+ | 环境变量管理 |
| **日志** | logging | 内置 | 日志记录 |
| **定时任务** | cron | 系统自带 | 定时执行 |

#### 云端备份（可选）

| 组件 | 技术选择 | 用途 |
|------|---------|------|
| **云函数** | 腾讯云 SCF | 备份执行环境 |
| **触发器** | 定时触发器 | 自动化调度 |
| **存储** | 腾讯云 COS | 数据备份（可选） |
| **SDK** | tencentcloud-sdk-python | 云资源管理 |

### 3.3 数据源

#### 主数据源：GitHub 镜像仓库

ARK 官网存在反爬虫保护，经测试会返回 403/404 错误。因此使用 GitHub 开源镜像作为主数据源：

**thisjustinh/ark-invest-history** (每日自动同步 ARK 数据)
- **仓库**: https://github.com/thisjustinh/ark-invest-history
- **用途**: 主数据源，提供所有 ARK ETF 持仓数据
- **优势**: 稳定可靠，无反爬虫限制，数据完整
- **数据特点**: 包含完整历史数据，需自动筛选最新日期

#### 数据获取逻辑

```python
# GitHub 数据源 URL（简化文件名格式）
GITHUB_URL_TEMPLATE = "https://raw.githubusercontent.com/thisjustinh/ark-invest-history/master/fund-holdings/{etf_symbol}.csv"

# 关键实现：自动筛选最新日期数据
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    max_date = df['date'].max()
    df = df[df['date'] == max_date].copy()  # 仅保留最新日期
```

#### 备用数据源（暂不实现）

ARK 官网可作为后续优化的备用数据源，实现双源自动切换：

```python
# ARK 官网 CSV 地址（存在反爬虫问题）
ARK_URL_TEMPLATE = "https://ark-funds.com/wp-content/fundsiteliterature/csv/{full_name}.csv"
```

**后续优化方向**：
1. 实现双数据源自动切换（GitHub 主源 + ARK 官网备源）
2. 添加数据源健康检查机制
3. 配置化数据源优先级

---

## 4. 系统架构

### 4.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         数据源层                              │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │  ARK 官网 CSV     │          │  历史数据仓库      │        │
│  │  (实时持仓数据)   │          │  (thisjustinh)   │        │
│  └──────────────────┘          └──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      处理层（二选一）                          │
│                                                              │
│  ┌───────────────────────┐      ┌───────────────────────┐  │
│  │   本地 Python 脚本     │  OR  │   腾讯云函数 SCF       │  │
│  │   ├─ 数据采集模块      │      │   ├─ 数据采集模块      │  │
│  │   ├─ 数据分析模块      │      │   ├─ 数据分析模块      │  │
│  │   ├─ 报告生成模块      │      │   ├─ 报告生成模块      │  │
│  │   └─ 企微推送模块      │      │   └─ 企微推送模块      │  │
│  │                       │      │                       │  │
│  │   触发方式:           │      │   触发方式:           │  │
│  │   - cron (08:00)     │      │   - 定时器 (09:00)    │  │
│  │   - 手动触发          │      │   - 手动触发          │  │
│  └───────────────────────┘      └───────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                         存储层                               │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │  本地 CSV 文件    │          │  腾讯云 COS       │        │
│  │  ~/Wood-ARK/data/ │          │  (可选备份)       │        │
│  └──────────────────┘          └──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                        通知层                                │
│              ┌────────────────────────┐                     │
│              │  企业微信群机器人       │                     │
│              │  (Webhook 推送)        │                     │
│              └────────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 数据流转图

```
[定时触发] 或 [手动触发]
         ↓
    [检查新数据]
         ↓
   [下载 CSV 文件]
         ↓
    [数据清洗]
         ↓
  [读取历史数据]
         ↓
    [对比分析]
    ├─ 识别新增/移除股票
    ├─ 计算持仓变化
    └─ 筛选重大调仓
         ↓
    [生成报告]
    ├─ 格式化为 Markdown
    └─ 计算统计数据
         ↓
   [推送企业微信]
         ↓
    [保存数据]
    ├─ 本地 CSV
    └─ 可选 COS 备份
         ↓
    [记录日志]
```

### 4.3 容错机制

```
┌─────────────────────────────────────┐
│  每天 08:00 - 本地 cron 任务触发    │
└─────────────────────────────────────┘
              ↓
        [电脑是否开机？]
         ↙Yes      ↘No
    [执行任务]    [跳过]
         ↓             ↓
    [推送成功]   每天 09:00 - 云函数触发
         ↓             ↓
   [写入标记]    [检查标记]
                      ↓
                [是否已推送？]
               ↙Yes      ↘No
          [跳过执行]   [执行任务]
                           ↓
                      [推送成功]
                           ↓
                      [写入标记]
```

---

## 5. 功能模块设计

### 5.1 模块划分

```
Wood-ARK 系统
├── 数据采集模块 (DataFetcher)
├── 数据分析模块 (Analyzer)
├── 报告生成模块 (ReportGenerator)
├── 通知推送模块 (WeChatNotifier)
├── 调度控制模块 (Scheduler)
└── 工具函数模块 (Utils)
```

### 5.2 模块详细设计

#### 5.2.1 数据采集模块 (DataFetcher)

**职责**: 从 ARK 官网下载最新持仓数据

**核心方法**:

```python
class DataFetcher:
    """ARK 数据采集器"""
    
    def __init__(self, data_dir: str):
        """初始化
        
        Args:
            data_dir: 数据存储根目录
        """
        self.data_dir = data_dir
        self.etfs = ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']
        self.urls = self._build_urls()
    
    def fetch_all_holdings(self) -> Dict[str, pd.DataFrame]:
        """下载所有 ETF 的最新持仓
        
        Returns:
            字典 {ETF名称: 持仓DataFrame}
        """
        pass
    
    def fetch_single_etf(self, etf_name: str) -> pd.DataFrame:
        """下载单个 ETF 的持仓数据
        
        Args:
            etf_name: ETF 名称，如 'ARKK'
            
        Returns:
            持仓 DataFrame
        """
        pass
    
    def is_new_data_available(self, etf_name: str) -> bool:
        """检查是否有新数据
        
        Args:
            etf_name: ETF 名称
            
        Returns:
            True: 有新数据, False: 无新数据
        """
        pass
    
    def save_holdings(self, etf_name: str, df: pd.DataFrame):
        """保存持仓数据到本地
        
        Args:
            etf_name: ETF 名称
            df: 持仓数据
        """
        pass
    
    def load_previous_holdings(self, etf_name: str) -> pd.DataFrame:
        """加载前一日持仓数据
        
        Args:
            etf_name: ETF 名称
            
        Returns:
            前一日持仓 DataFrame
        """
        pass
```

**数据清洗逻辑**:
- 移除 ARK CSV 文件末尾的 3 行空行和说明文字
- 统一日期格式为 `YYYY-MM-DD`
- 处理缺失值（ticker 为空的行）
- 类型转换（shares 为 int，weight 为 float）

---

#### 5.2.2 数据分析模块 (Analyzer)

**职责**: 对比持仓数据，分析变化

**核心方法**:

```python
class Analyzer:
    """ARK 持仓分析器"""
    
    def __init__(self, change_threshold: float = 5.0):
        """初始化
        
        Args:
            change_threshold: 持仓变化阈值（百分比），默认 5%
        """
        self.change_threshold = change_threshold
    
    def compare_holdings(
        self, 
        current: pd.DataFrame, 
        previous: pd.DataFrame
    ) -> Dict:
        """对比前后持仓
        
        Args:
            current: 当前持仓
            previous: 前一日持仓
            
        Returns:
            分析结果字典
            {
                'added': [新增股票列表],
                'removed': [移除股票列表],
                'increased': [增持股票列表],
                'decreased': [减持股票列表],
                'unchanged': [不变股票列表]
            }
        """
        pass
    
    def calculate_change_percentage(
        self,
        current: pd.DataFrame,
        previous: pd.DataFrame
    ) -> pd.DataFrame:
        """计算持仓变化百分比
        
        Args:
            current: 当前持仓
            previous: 前一日持仓
            
        Returns:
            包含变化百分比的 DataFrame
            columns: [ticker, company, shares_change_pct, weight_change]
        """
        pass
    
    def filter_significant_changes(
        self,
        changes_df: pd.DataFrame
    ) -> Dict[str, pd.DataFrame]:
        """筛选重大变化
        
        Args:
            changes_df: 变化数据
            
        Returns:
            {
                'increased': 增持超过阈值的股票,
                'decreased': 减持超过阈值的股票
            }
        """
        pass
    
    def calculate_statistics(
        self,
        holdings: pd.DataFrame
    ) -> Dict:
        """计算统计数据
        
        Args:
            holdings: 持仓数据
            
        Returns:
            统计信息字典
            {
                'total_positions': 持仓数量,
                'total_weight': 总权重,
                'top_5_holdings': 前5大持仓
            }
        """
        pass
```

---

#### 5.2.3 报告生成模块 (ReportGenerator)

**职责**: 将分析结果格式化为 Markdown 报告

**核心方法**:

```python
class ReportGenerator:
    """报告生成器"""
    
    def generate_daily_report(
        self,
        date: str,
        all_changes: Dict[str, Dict]
    ) -> str:
        """生成每日持仓报告
        
        Args:
            date: 报告日期，格式 YYYY-MM-DD
            all_changes: 所有 ETF 的变化数据
                {
                    'ARKK': {...},
                    'ARKW': {...},
                    ...
                }
        
        Returns:
            Markdown 格式的报告
        """
        pass
    
    def format_etf_section(
        self,
        etf_name: str,
        changes: Dict
    ) -> str:
        """格式化单个 ETF 的报告段落
        
        Args:
            etf_name: ETF 名称
            changes: 该 ETF 的变化数据
            
        Returns:
            Markdown 文本
        """
        pass
    
    def format_stock_list(
        self,
        stocks: List[Dict],
        action: str  # 'added', 'removed', 'increased', 'decreased'
    ) -> str:
        """格式化股票列表
        
        Args:
            stocks: 股票列表
            action: 操作类型
            
        Returns:
            Markdown 列表
        """
        pass
```

---

#### 5.2.4 通知推送模块 (WeChatNotifier)

**职责**: 通过企业微信 Webhook 推送消息

**核心方法**:

```python
class WeChatNotifier:
    """企业微信通知器"""
    
    def __init__(self, webhook_url: str):
        """初始化
        
        Args:
            webhook_url: 企业微信 Webhook URL
        """
        self.webhook_url = webhook_url
    
    def send_markdown(self, content: str) -> bool:
        """发送 Markdown 消息
        
        Args:
            content: Markdown 格式的消息内容
            
        Returns:
            True: 发送成功, False: 发送失败
        """
        pass
    
    def send_text(self, content: str) -> bool:
        """发送纯文本消息
        
        Args:
            content: 文本内容
            
        Returns:
            True: 发送成功, False: 发送失败
        """
        pass
    
    def send_error_alert(self, error_msg: str):
        """发送错误告警
        
        Args:
            error_msg: 错误信息
        """
        pass
```

**企微 Webhook 消息格式**:

```python
# Markdown 消息
{
    "msgtype": "markdown",
    "markdown": {
        "content": "## 标题\n内容..."
    }
}

# 文本消息
{
    "msgtype": "text",
    "text": {
        "content": "纯文本内容"
    }
}
```

---

#### 5.2.5 调度控制模块 (Scheduler)

**职责**: 任务调度、容错处理

**核心方法**:

```python
class Scheduler:
    """任务调度器"""
    
    def __init__(
        self,
        fetcher: DataFetcher,
        analyzer: Analyzer,
        reporter: ReportGenerator,
        notifier: WeChatNotifier
    ):
        """初始化"""
        pass
    
    def run_daily_task(self) -> bool:
        """执行每日定时任务
        
        Returns:
            True: 成功, False: 失败
        """
        pass
    
    def manual_trigger(self, date: Optional[str] = None) -> bool:
        """手动触发任务
        
        Args:
            date: 指定日期（可选），格式 YYYY-MM-DD
            
        Returns:
            True: 成功, False: 失败
        """
        pass
    
    def check_and_compensate(self) -> bool:
        """检查并补偿错过的更新
        
        Returns:
            True: 有补偿并成功, False: 无需补偿或失败
        """
        pass
    
    def is_already_pushed_today(self) -> bool:
        """检查今天是否已推送
        
        Returns:
            True: 已推送, False: 未推送
        """
        pass
    
    def mark_as_pushed(self, date: str):
        """标记为已推送
        
        Args:
            date: 日期
        """
        pass
```

---

#### 5.2.6 工具函数模块 (Utils)

**职责**: 通用工具函数

```python
# config.py - 配置管理
def load_config() -> Dict:
    """从 .env 加载配置"""
    pass

def get_data_dir() -> str:
    """获取数据目录"""
    pass

# logger.py - 日志管理
def setup_logger(name: str, log_file: str) -> logging.Logger:
    """设置日志器"""
    pass

# date_utils.py - 日期工具
def get_previous_trading_day(date: str) -> str:
    """获取前一个交易日"""
    pass

def is_trading_day(date: str) -> bool:
    """判断是否为交易日"""
    pass
```

---

## 6. 数据结构设计

### 6.1 CSV 文件格式

#### 6.1.1 持仓数据文件

**文件命名**: `data/holdings/{ETF_NAME}/{YYYY-MM-DD}.csv`

**示例**: `data/holdings/ARKK/2025-01-15.csv`

**数据格式**:

```csv
date,fund,company,ticker,cusip,shares,market value($),weight(%)
2025-01-15,ARKK,TESLA INC,TSLA,88160R101,3456789,876543210.50,8.25
2025-01-15,ARKK,COINBASE GLOBAL INC,COIN,19260Q107,1234567,234567890.00,5.60
...
```

**字段说明**:

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| date | string | 持仓日期 | 2025-01-15 |
| fund | string | 基金代码 | ARKK |
| company | string | 公司名称 | TESLA INC |
| ticker | string | 股票代码 | TSLA |
| cusip | string | CUSIP 编码 | 88160R101 |
| shares | integer | 持有股数 | 3456789 |
| market value($) | float | 市值（美元） | 876543210.50 |
| weight(%) | float | 权重百分比 | 8.25 |

---

#### 6.1.2 交易记录文件（可选）

**文件命名**: `data/transactions/{ETF_NAME}/{YYYY-MM-DD}.csv`

**数据格式**:

```csv
date,etf,ticker,company,action,shares_change,shares_change_pct,weight_change
2025-01-15,ARKK,TSLA,TESLA INC,increase,123456,3.70,0.15
2025-01-15,ARKK,COIN,COINBASE GLOBAL INC,decrease,-45678,-3.56,-0.12
2025-01-15,ARKK,HOOD,ROBINHOOD MARKETS INC,add,100000,N/A,0.50
2025-01-15,ARKK,SPOT,SPOTIFY TECHNOLOGY SA,remove,-200000,N/A,-0.80
```

**字段说明**:

| 字段 | 类型 | 说明 | 可能值 |
|------|------|------|--------|
| date | string | 日期 | 2025-01-15 |
| etf | string | ETF 代码 | ARKK |
| ticker | string | 股票代码 | TSLA |
| company | string | 公司名称 | TESLA INC |
| action | string | 操作类型 | add, remove, increase, decrease |
| shares_change | integer | 股数变化 | 123456 或 -45678 |
| shares_change_pct | float | 变化百分比 | 3.70 或 N/A |
| weight_change | float | 权重变化 | 0.15 或 -0.12 |

---

### 6.2 配置文件格式

#### 6.2.1 .env 文件

```bash
# 企业微信配置
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE

# 数据目录配置
DATA_DIR=/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/data
LOG_DIR=/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/logs

# 分析参数配置
CHANGE_THRESHOLD=5.0  # 持仓变化阈值（%）
ETFS=ARKK,ARKW,ARKG,ARKQ,ARKF  # 监控的 ETF 列表

# 云函数配置（可选）
ENABLE_CLOUD_BACKUP=false
TENCENT_SECRET_ID=YOUR_SECRET_ID
TENCENT_SECRET_KEY=YOUR_SECRET_KEY
COS_BUCKET=ark-data-1234567890
COS_REGION=ap-guangzhou

# 通知配置
ENABLE_ERROR_ALERT=true  # 是否发送错误告警
REPORT_TIME=08:00  # 本地任务执行时间
BACKUP_TIME=09:00  # 云函数备份时间
```

---

#### 6.2.2 config.yaml（可选）

```yaml
# ETF 配置
etfs:
  ARKK:
    name: "ARK Innovation ETF"
    description: "创新科技"
    url: "https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv"
  
  ARKW:
    name: "ARK Next Generation Internet ETF"
    description: "下一代互联网"
    url: "https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv"
  
  ARKG:
    name: "ARK Genomic Revolution ETF"
    description: "基因革命"
    url: "https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_GENOMIC_REVOLUTION_MULTISECTOR_ETF_ARKG_HOLDINGS.csv"
  
  ARKQ:
    name: "ARK Autonomous Technology & Robotics ETF"
    description: "自动驾驶与机器人"
    url: "https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_AUTONOMOUS_TECHNOLOGY_&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv"
  
  ARKF:
    name: "ARK Fintech Innovation ETF"
    description: "金融科技"
    url: "https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv"

# 分析配置
analysis:
  change_threshold: 5.0  # 重大变化阈值
  top_n_holdings: 10  # 显示前 N 大持仓
  
# 通知配置
notification:
  platforms:
    - wechat
  wechat:
    format: markdown
    max_length: 4096
```

---

### 6.3 日志文件格式

**文件命名**: `logs/{YYYY-MM-DD}.log`

**日志格式**:

```
2025-01-15 08:00:01 [INFO] [Scheduler] 开始执行每日任务
2025-01-15 08:00:02 [INFO] [DataFetcher] 下载 ARKK 持仓数据...
2025-01-15 08:00:05 [INFO] [DataFetcher] ARKK 下载完成，共 45 条记录
2025-01-15 08:00:06 [INFO] [DataFetcher] 检测到新数据: 2025-01-15
2025-01-15 08:00:10 [INFO] [Analyzer] 开始分析 ARKK 持仓变化...
2025-01-15 08:00:11 [INFO] [Analyzer] ARKK: 新增 1 只，移除 1 只，重大变化 3 只
2025-01-15 08:00:15 [INFO] [ReportGenerator] 生成报告完成
2025-01-15 08:00:16 [INFO] [WeChatNotifier] 推送企业微信成功
2025-01-15 08:00:17 [INFO] [Scheduler] 任务执行完成，耗时 16 秒
```

---

## 7. 消息格式设计

### 7.1 每日持仓报告（完整版）

```markdown
## 🚀 ARK 持仓日报 (2025-01-15)

### 📊 整体概况
- **更新时间**: 2025-01-15 08:00:15
- **监控 ETF**: 5 只
- **有变化 ETF**: 3 只
- **数据来源**: ARK Invest 官网

---

### 🔥 ARKK - 创新科技 ETF

**📈 新增股票** (1):
- ✅ **$HOOD** Robinhood Markets Inc (权重: 0.5%)

**📉 移除股票** (1):
- ❌ **$SPOT** Spotify Technology SA (权重: 0.8%)

**💹 持仓变化** (±5%):
- 📈 **$TSLA** Tesla Inc +12.5%
  - 股数: 3,333,333 → 3,750,000 (+416,667)
  - 权重: 8.2% → 9.1% (+0.9%)
  
- 📉 **$COIN** Coinbase Global Inc -8.3%
  - 股数: 1,234,567 → 1,132,098 (-102,469)
  - 权重: 5.6% → 5.1% (-0.5%)
  
- 📈 **$ROKU** Roku Inc +6.7%
  - 股数: 2,000,000 → 2,134,000 (+134,000)
  - 权重: 3.2% → 3.4% (+0.2%)

**📌 前 5 大持仓**:
1. $TSLA Tesla Inc (9.1%)
2. $COIN Coinbase (5.1%)
3. $ROKU Roku (3.4%)
4. $SHOP Shopify (3.2%)
5. $PATH UiPath (2.8%)

---

### 💊 ARKG - 基因革命 ETF

**💹 持仓变化** (±5%):
- 📈 **$CRSP** CRISPR Therapeutics +8.9%
  - 股数: 1,500,000 → 1,633,500 (+133,500)
  - 权重: 6.5% → 7.1% (+0.6%)

**📌 前 5 大持仓**:
1. $CRSP CRISPR Therapeutics (7.1%)
2. $EXAS Exact Sciences (5.2%)
3. $TWST Twist Bioscience (4.8%)
4. $NTLA Intellia Therapeutics (4.5%)
5. $VRTX Vertex Pharmaceuticals (4.2%)

---

### 🌐 ARKW - 下一代互联网 ETF

**💹 持仓变化** (±5%):
- 📈 **$SHOP** Shopify +15.2%
  - 股数: 800,000 → 921,600 (+121,600)
  - 权重: 6.5% → 7.4% (+0.9%)
  
- 📉 **$TWLO** Twilio -5.1%
  - 股数: 1,200,000 → 1,138,800 (-61,200)
  - 权重: 4.8% → 4.5% (-0.3%)

**📌 前 5 大持仓**:
1. $SHOP Shopify (7.4%)
2. $TSLA Tesla (6.8%)
3. $COIN Coinbase (5.5%)
4. $TWLO Twilio (4.5%)
5. $PATH UiPath (4.0%)

---

### 🤖 ARKQ - 自动驾驶与机器人 ETF

**无重大变化**

---

### 💳 ARKF - 金融科技 ETF

**无重大变化**

---

💡 **说明**: 
- "重大变化"定义为持仓股数变化 ≥ ±5%
- 权重为该股票在 ETF 中的占比
- 数据更新于美东时间每日 19:00

📌 **免责声明**: 本报告仅供参考，不构成投资建议
```

---

### 7.2 简化版报告（仅重点）

```markdown
## 🚀 ARK 日报 (01/15)

### ARKK 创新
- ✅ 新增: $HOOD (0.5%)
- ❌ 移除: $SPOT (0.8%)
- 📈 $TSLA +12.5% → 9.1%
- 📉 $COIN -8.3% → 5.1%

### ARKG 基因
- 📈 $CRSP +8.9% → 7.1%

### ARKW 互联网
- 📈 $SHOP +15.2% → 7.4%

📊 总计: 3/5 只 ETF 有变化
```

---

### 7.3 错误告警消息

```markdown
## ⚠️ ARK 监控系统告警

**错误类型**: 数据获取失败

**详细信息**:
- 时间: 2025-01-15 08:00:05
- ETF: ARKK
- 错误: requests.exceptions.Timeout: 连接超时

**处理建议**:
- 系统将在 1 小时后自动重试
- 如持续失败，请手动执行: `python ark_monitor.py --manual`

**已尝试次数**: 2/5
```

---

### 7.4 手动触发成功消息

```markdown
## ✅ 手动任务执行成功

**执行时间**: 2025-01-15 18:30:22
**执行方式**: 手动触发
**处理日期**: 2025-01-15

**结果摘要**:
- 下载数据: 成功 (5/5)
- 分析变化: 3 只 ETF 有变化
- 推送报告: 成功

详细报告见下方 ⬇️
```

---

## 8. 项目目录结构

```
/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/
│
├── README.md                       # 项目说明文档
├── PROJECT_DESIGN.md              # 本设计文档
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量示例
├── .env                           # 环境变量（不提交 Git）
├── .gitignore                     # Git 忽略文件
│
├── config/                        # 配置文件目录
│   ├── __init__.py
│   ├── settings.py               # 配置加载
│   └── etfs.yaml                 # ETF 配置（可选）
│
├── src/                          # 源代码目录
│   ├── __init__.py
│   ├── fetcher.py                # 数据采集模块
│   ├── analyzer.py               # 数据分析模块
│   ├── reporter.py               # 报告生成模块
│   ├── notifier.py               # 企微推送模块
│   ├── scheduler.py              # 调度控制模块
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── logger.py             # 日志工具
│       ├── date_utils.py         # 日期工具
│       └── file_utils.py         # 文件工具
│
├── data/                         # 数据存储目录
│   ├── holdings/                 # 持仓数据
│   │   ├── ARKK/
│   │   │   ├── 2025-01-15.csv
│   │   │   └── 2025-01-14.csv
│   │   ├── ARKW/
│   │   ├── ARKG/
│   │   ├── ARKQ/
│   │   └── ARKF/
│   ├── transactions/             # 交易记录（可选）
│   │   ├── ARKK/
│   │   ├── ARKW/
│   │   └── ...
│   ├── cache/                    # 缓存数据
│   │   └── push_status.json     # 推送状态记录
│   └── history/                  # 历史数据备份
│
├── logs/                         # 日志目录
│   ├── 2025-01-15.log
│   ├── 2025-01-14.log
│   └── error.log                # 错误日志
│
├── scripts/                      # 脚本目录
│   ├── setup.sh                 # 初始化脚本
│   ├── install_cron.sh          # 安装定时任务
│   ├── test_webhook.sh          # 测试企微 Webhook
│   └── backup_data.sh           # 数据备份脚本
│
├── cloud_function/               # 云函数代码（可选）
│   ├── main.py                  # 云函数入口
│   ├── requirements.txt         # 云函数依赖
│   └── README.md                # 云函数部署说明
│
├── tests/                        # 测试代码
│   ├── __init__.py
│   ├── test_fetcher.py
│   ├── test_analyzer.py
│   ├── test_notifier.py
│   └── test_integration.py      # 集成测试
│
├── docs/                         # 文档目录
│   ├── API.md                   # API 文档
│   ├── DEPLOYMENT.md            # 部署文档
│   └── TROUBLESHOOTING.md       # 故障排查
│
├── ark_monitor.py                # 主程序入口
└── VERSION                       # 版本号
```

---

### 8.1 核心文件说明

#### 主程序入口 (ark_monitor.py)

```python
#!/usr/bin/env python3
"""
ARK 持仓监控主程序
"""

import sys
import argparse
from src.scheduler import Scheduler
from config.settings import load_config
from src.utils.logger import setup_logger

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ARK 持仓监控系统')
    parser.add_argument(
        '--manual', 
        action='store_true',
        help='手动触发任务'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='指定日期 (YYYY-MM-DD)，用于回溯'
    )
    parser.add_argument(
        '--check-missed',
        action='store_true',
        help='检查并补偿错过的更新'
    )
    parser.add_argument(
        '--test-webhook',
        action='store_true',
        help='测试企业微信 Webhook'
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 设置日志
    logger = setup_logger('ark_monitor', config['log_file'])
    
    # 创建调度器
    scheduler = Scheduler(config, logger)
    
    try:
        if args.test_webhook:
            # 测试 Webhook
            scheduler.test_webhook()
        elif args.manual:
            # 手动触发
            scheduler.manual_trigger(args.date)
        elif args.check_missed:
            # 检查错过的更新
            scheduler.check_and_compensate()
        else:
            # 常规每日任务
            scheduler.run_daily_task()
            
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

#### 配置管理 (config/settings.py)

```python
"""
配置管理模块
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """加载配置"""
    
    # 加载 .env 文件
    load_dotenv()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    
    config = {
        # 企业微信配置
        'wechat_webhook_url': os.getenv('WECHAT_WEBHOOK_URL'),
        
        # 目录配置
        'data_dir': os.getenv('DATA_DIR', project_root / 'data'),
        'log_dir': os.getenv('LOG_DIR', project_root / 'logs'),
        
        # 分析参数
        'change_threshold': float(os.getenv('CHANGE_THRESHOLD', '5.0')),
        'etfs': os.getenv('ETFS', 'ARKK,ARKW,ARKG,ARKQ,ARKF').split(','),
        
        # 云函数配置（可选）
        'enable_cloud_backup': os.getenv('ENABLE_CLOUD_BACKUP', 'false').lower() == 'true',
        'tencent_secret_id': os.getenv('TENCENT_SECRET_ID'),
        'tencent_secret_key': os.getenv('TENCENT_SECRET_KEY'),
        'cos_bucket': os.getenv('COS_BUCKET'),
        'cos_region': os.getenv('COS_REGION', 'ap-guangzhou'),
        
        # 通知配置
        'enable_error_alert': os.getenv('ENABLE_ERROR_ALERT', 'true').lower() == 'true',
        'report_time': os.getenv('REPORT_TIME', '08:00'),
        'backup_time': os.getenv('BACKUP_TIME', '09:00'),
        
        # 项目根目录
        'project_root': project_root,
    }
    
    # 验证必需配置
    if not config['wechat_webhook_url']:
        raise ValueError("未配置 WECHAT_WEBHOOK_URL，请检查 .env 文件")
    
    return config
```

---

#### 依赖文件 (requirements.txt)

```txt
# 核心依赖
pandas>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0

# 日期处理
python-dateutil>=2.8.2

# HTTP 请求增强（可选）
urllib3>=2.0.0

# 云函数依赖（可选）
tencentcloud-sdk-python>=3.0.0

# 数据可视化（可选）
matplotlib>=3.7.0
seaborn>=0.12.0

# 测试依赖
pytest>=7.4.0
pytest-cov>=4.1.0
```

---

## 9. 部署方案

### 9.1 本地部署（必需）

#### 步骤 1: 克隆项目

```bash
# 创建项目目录
mkdir -p /Users/lucian/Documents/个人/Investment/Tools/Wood-ARK
cd /Users/lucian/Documents/个人/Investment/Tools/Wood-ARK
```

---

#### 步骤 2: 初始化项目结构

执行初始化脚本（或手动创建目录）:

```bash
# scripts/setup.sh

#!/bin/bash

echo "开始初始化 Wood-ARK 项目..."

# 创建目录结构
mkdir -p config
mkdir -p src/utils
mkdir -p data/{holdings/{ARKK,ARKW,ARKG,ARKQ,ARKF},transactions,cache,history}
mkdir -p logs
mkdir -p scripts
mkdir -p cloud_function
mkdir -p tests
mkdir -p docs

# 创建 .env 示例文件
cat > .env.example << 'EOF'
# 企业微信配置
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE

# 数据目录配置
DATA_DIR=/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/data
LOG_DIR=/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/logs

# 分析参数配置
CHANGE_THRESHOLD=5.0
ETFS=ARKK,ARKW,ARKG,ARKQ,ARKF

# 云函数配置（可选）
ENABLE_CLOUD_BACKUP=false
TENCENT_SECRET_ID=
TENCENT_SECRET_KEY=
COS_BUCKET=
COS_REGION=ap-guangzhou

# 通知配置
ENABLE_ERROR_ALERT=true
REPORT_TIME=08:00
BACKUP_TIME=09:00
EOF

# 创建 .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# 配置文件
.env

# 数据文件
data/
logs/

# IDE
.vscode/
.idea/
*.swp

# macOS
.DS_Store
EOF

# 创建 README.md
cat > README.md << 'EOF'
# Wood-ARK 持仓监控系统

ARK Invest (木头姐) 持仓监控与企业微信推送系统

## 快速开始

1. 安装依赖: `pip install -r requirements.txt`
2. 配置环境: `cp .env.example .env` 并填写配置
3. 运行测试: `python ark_monitor.py --test-webhook`
4. 手动执行: `python ark_monitor.py --manual`

详细文档请查看 PROJECT_DESIGN.md
EOF

echo "✅ 项目结构初始化完成！"
echo "📝 请执行以下步骤："
echo "   1. cp .env.example .env"
echo "   2. 编辑 .env 文件，填写企业微信 Webhook URL"
echo "   3. pip install -r requirements.txt"
```

运行初始化脚本:

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

---

#### 步骤 3: 安装 Python 依赖

```bash
# 使用 Python 3.9+
python3 --version

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

#### 步骤 4: 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
vim .env
```

**必需配置项**:
- `WECHAT_WEBHOOK_URL`: 企业微信群机器人 Webhook URL

**获取企业微信 Webhook URL**:

1. 打开企业微信群聊
2. 点击右上角 `...` → `群机器人` → `添加群机器人`
3. 输入机器人名称，点击 `添加`
4. 复制 Webhook 地址，粘贴到 `.env` 文件

**Webhook URL 格式**:
```
https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=693axxx6-7aoc-4bc4-97a0-0ec2sifa5aaa
```

---

#### 步骤 5: 测试企业微信推送

```bash
# 创建测试脚本
cat > scripts/test_webhook.sh << 'EOF'
#!/bin/bash
python3 ark_monitor.py --test-webhook
EOF

chmod +x scripts/test_webhook.sh
./scripts/test_webhook.sh
```

如果企业微信群收到测试消息，说明配置成功！

---

#### 步骤 6: 手动测试完整流程

```bash
# 首次运行，下载数据
python3 ark_monitor.py --manual
```

**预期输出**:
```
[INFO] 开始执行手动任务...
[INFO] 下载 ARKK 持仓数据...
[INFO] ARKK 下载完成，共 45 条记录
[INFO] 检测到新数据: 2025-01-15
[INFO] 分析 ARKK 持仓变化...
[INFO] 生成报告完成
[INFO] 推送企业微信成功
[INFO] 任务执行完成
```

---

#### 步骤 7: 设置定时任务 (cron)

```bash
# 创建 cron 安装脚本
cat > scripts/install_cron.sh << 'EOF'
#!/bin/bash

PROJECT_DIR="/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python3"

# 添加 cron 任务
(crontab -l 2>/dev/null; echo "# ARK 持仓监控 - 每天早上 8 点执行") | crontab -
(crontab -l 2>/dev/null; echo "0 8 * * * cd $PROJECT_DIR && $PYTHON_PATH ark_monitor.py >> logs/cron.log 2>&1") | crontab -

# 添加错过更新检查 - 每小时检查一次
(crontab -l 2>/dev/null; echo "0 * * * * cd $PROJECT_DIR && $PYTHON_PATH ark_monitor.py --check-missed >> logs/cron.log 2>&1") | crontab -

echo "✅ Cron 任务安装完成！"
echo "📋 当前 cron 任务列表:"
crontab -l | grep ARK
EOF

chmod +x scripts/install_cron.sh
./scripts/install_cron.sh
```

**验证 cron 任务**:

```bash
crontab -l | grep ARK
```

---

### 9.2 云函数部署（可选，备份机制）

#### 步骤 1: 准备云函数代码

```bash
cd cloud_function
```

**cloud_function/main.py**:

```python
#!/usr/bin/env python3
"""
腾讯云函数入口
"""

import json
import sys
import os

# 添加父目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scheduler import Scheduler
from config.settings import load_config
from src.utils.logger import setup_logger

def main_handler(event, context):
    """
    云函数入口函数
    
    Args:
        event: 触发事件
        context: 运行时上下文
        
    Returns:
        执行结果
    """
    try:
        # 加载配置
        config = load_config()
        
        # 设置日志
        logger = setup_logger('scf_handler', '/tmp/scf.log')
        
        logger.info(f"云函数触发: {json.dumps(event)}")
        
        # 创建调度器
        scheduler = Scheduler(config, logger)
        
        # 检查今天是否已推送（本地可能已执行）
        if scheduler.is_already_pushed_today():
            logger.info("本地任务已执行，跳过云函数")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': '本地已推送，云函数跳过'})
            }
        
        # 执行任务
        success = scheduler.run_daily_task()
        
        if success:
            # 标记为已推送
            scheduler.mark_as_pushed_cloud()
            
            return {
                'statusCode': 200,
                'body': json.dumps({'message': '云函数执行成功'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': '云函数执行失败'})
            }
            
    except Exception as e:
        logger.error(f"云函数执行异常: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

---

#### 步骤 2: 打包云函数

```bash
# 创建打包脚本
cat > cloud_function/package.sh << 'EOF'
#!/bin/bash

echo "开始打包云函数..."

# 进入项目根目录
cd "$(dirname "$0")/.."

# 创建临时目录
mkdir -p /tmp/ark_scf

# 复制代码
cp -r src /tmp/ark_scf/
cp -r config /tmp/ark_scf/
cp cloud_function/main.py /tmp/ark_scf/
cp requirements.txt /tmp/ark_scf/
cp .env /tmp/ark_scf/

# 安装依赖到临时目录
pip install -r requirements.txt -t /tmp/ark_scf/

# 打包
cd /tmp/ark_scf
zip -r ark_scf.zip .

# 移动到项目目录
mv ark_scf.zip /Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/cloud_function/

echo "✅ 云函数打包完成: cloud_function/ark_scf.zip"
EOF

chmod +x cloud_function/package.sh
./cloud_function/package.sh
```

---

#### 步骤 3: 创建云函数（腾讯云控制台）

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/scf)
2. 进入 `云函数 SCF` 服务
3. 点击 `新建` 函数

**函数配置**:
- **函数名称**: `ark-monitor-backup`
- **运行环境**: `Python 3.9`
- **地域**: `广州`（或其他）
- **提交方法**: `本地上传 zip 包`
- **上传文件**: 选择 `cloud_function/ark_scf.zip`

**高级配置**:
- **执行超时时间**: `60 秒`
- **内存**: `128 MB`
- **环境变量**: 
  - `WECHAT_WEBHOOK_URL`: (你的 Webhook URL)
  - `CHANGE_THRESHOLD`: `5.0`

**触发器配置**:
- **触发方式**: `定时触发`
- **Cron 表达式**: `0 1 * * *` (每天 09:00，北京时间 = UTC+8)
- **启用**: `是`

---

#### 步骤 4: 测试云函数

在腾讯云控制台点击 `测试`，查看执行日志。

如果企业微信群收到消息，说明云函数部署成功！

---

### 9.3 部署验证

#### 验证清单

| 项目 | 验证方法 | 预期结果 |
|------|---------|---------|
| ✅ Python 环境 | `python3 --version` | ≥ 3.9 |
| ✅ 依赖安装 | `pip list | grep pandas` | 已安装 |
| ✅ 配置文件 | `cat .env` | Webhook URL 已填写 |
| ✅ 目录结构 | `ls data/holdings` | 包含 5 个 ETF 目录 |
| ✅ 企微推送 | `python ark_monitor.py --test-webhook` | 收到测试消息 |
| ✅ 手动执行 | `python ark_monitor.py --manual` | 下载数据并推送 |
| ✅ Cron 任务 | `crontab -l` | 显示定时任务 |
| ✅ 云函数（可选） | 腾讯云控制台测试 | 执行成功 |

---

### 9.4 日常使用

#### 自动运行（推荐）

配置好 cron 后，系统会每天早上 8 点自动执行，无需手动操作。

**查看日志**:

```bash
# 查看最新日志
tail -f logs/$(date +%Y-%m-%d).log

# 查看 cron 日志
tail -f logs/cron.log
```

---

#### 手动运行

```bash
# 运行当天任务
python ark_monitor.py --manual

# 回溯历史数据（指定日期）
python ark_monitor.py --manual --date 2025-01-14

# 检查并补偿错过的更新
python ark_monitor.py --check-missed

# 测试企业微信推送
python ark_monitor.py --test-webhook
```

---

#### 数据备份

```bash
# 创建备份脚本
cat > scripts/backup_data.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/backups"
DATE=$(date +%Y-%m-%d)

mkdir -p $BACKUP_DIR

# 打包数据目录
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# 保留最近 30 天的备份
find $BACKUP_DIR -name "data_*.tar.gz" -mtime +30 -delete

echo "✅ 数据备份完成: $BACKUP_DIR/data_$DATE.tar.gz"
EOF

chmod +x scripts/backup_data.sh

# 添加到 cron（每周日凌晨 2 点备份）
(crontab -l; echo "0 2 * * 0 /Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/scripts/backup_data.sh") | crontab -
```

---

## 10. 开发计划

### 10.1 MVP 版本（v0.1.0）

**目标**: 实现核心功能，验证可行性

**功能清单**:
- [x] 数据采集：下载 ARK 最新持仓 CSV
- [x] 数据分析：对比前后持仓，识别变化
- [x] 报告生成：格式化为 Markdown
- [x] 企微推送：通过 Webhook 发送消息
- [x] 手动触发：命令行执行
- [x] 基础日志：记录关键操作

**开发时间**: 2-3 小时

**验收标准**:
- 能成功下载并保存 ARK 持仓数据
- 能正确识别新增/移除/变化的股票
- 能生成格式正确的 Markdown 报告
- 能成功推送到企业微信群

---

### 10.2 完整版（v1.0.0）

**目标**: 生产环境可用

**新增功能**:
- [x] 定时任务：cron 自动执行
- [x] 容错机制：重试、告警
- [x] 云函数备份：应对电脑关机
- [x] 错过补偿：自动检测并补偿
- [x] 配置管理：.env + yaml
- [x] 完善日志：分级、轮转

**开发时间**: 额外 3-4 小时

**验收标准**:
- 定时任务稳定运行 7 天无故障
- 云函数备份机制正常工作
- 错误场景有明确的告警和日志

---

### 10.3 增强版（v1.1.0）

**目标**: 提升用户体验

**新增功能**:
- [ ] 历史数据回溯：查询任意时期持仓
- [ ] 数据可视化：生成持仓变化趋势图
- [ ] 统计分析：板块分布、换手率等
- [ ] Web 界面：本地 Dashboard（可选）
- [ ] 多渠道通知：邮件、Telegram 等

**开发时间**: 4-6 小时

---

### 10.4 开发优先级

```
Phase 1: MVP (必需) - 2-3 小时
├── 数据采集模块 [P0]
├── 数据分析模块 [P0]
├── 报告生成模块 [P0]
├── 企微推送模块 [P0]
└── 基础日志 [P0]

Phase 2: 完整版 (推荐) - 3-4 小时
├── 定时任务 [P1]
├── 容错机制 [P1]
├── 云函数备份 [P1]
├── 错过补偿 [P2]
└── 配置优化 [P2]

Phase 3: 增强版 (可选) - 4-6 小时
├── 历史回溯 [P3]
├── 数据可视化 [P3]
├── 统计分析 [P3]
└── Web 界面 [P4]
```

---

## 11. 附录

### 11.1 ARK ETF 详细信息

| ETF | 全称 | 主题 | 费率 | 规模 |
|-----|------|------|------|------|
| **ARKK** | ARK Innovation ETF | 跨行业颠覆性创新 | 0.75% | ~$8.5B |
| **ARKW** | ARK Next Generation Internet ETF | 下一代互联网 | 0.75% | ~$1.5B |
| **ARKG** | ARK Genomic Revolution ETF | 基因革命 | 0.75% | ~$1.2B |
| **ARKQ** | ARK Autonomous Technology & Robotics ETF | 自动驾驶与机器人 | 0.75% | ~$900M |
| **ARKF** | ARK Fintech Innovation ETF | 金融科技 | 0.75% | ~$800M |

---

### 11.2 常见问题 (FAQ)

#### Q1: ARK 数据更新时间是什么时候？

**A**: ARK Invest 通常在**美东时间每日 19:00**（北京时间次日 07:00-08:00）更新持仓数据。

---

#### Q2: 为什么首次运行没有推送报告？

**A**: 因为需要有前一日的数据才能对比。建议：
1. 首次运行时会下载并保存当前数据
2. 第二天运行时会对比并推送报告
3. 或者手动初始化历史数据（见下方）

**初始化历史数据**:
```bash
# 克隆历史数据仓库
git clone https://github.com/thisjustinh/ark-invest-history.git /tmp/ark-history

# 复制最近 7 天的数据到本地
cp /tmp/ark-history/fund-holdings/ARKK/*.csv data/holdings/ARKK/
cp /tmp/ark-history/fund-holdings/ARKW/*.csv data/holdings/ARKW/
# ... 其他 ETF
```

---

#### Q3: 如何调整持仓变化阈值？

**A**: 编辑 `.env` 文件，修改 `CHANGE_THRESHOLD` 参数：

```bash
# 设置为 3%（更敏感）
CHANGE_THRESHOLD=3.0

# 设置为 10%（只看重大变化）
CHANGE_THRESHOLD=10.0
```

---

#### Q4: 电脑关机时会错过推送吗？

**A**: 
- **本地任务**: 会错过
- **云函数备份**: 会在 09:00 自动兜底
- **补偿机制**: 开机后运行 `--check-missed` 会自动补偿

---

#### Q5: 如何查看历史报告？

**A**: 所有推送的报告都会保存在日志文件中：

```bash
# 查看某天的日志
cat logs/2025-01-15.log | grep "ARK 持仓日报"

# 或查看保存的报告文件（如果配置了）
cat data/reports/2025-01-15.md
```

---

#### Q6: 能否监控更多 ETF？

**A**: 可以，编辑 `.env` 文件：

```bash
# 添加 PRNT (3D 打印 ETF)
ETFS=ARKK,ARKW,ARKG,ARKQ,ARKF,PRNT

# 同时需要在 config/etfs.yaml 添加对应配置
```

---

#### Q7: 企业微信消息太长被截断怎么办？

**A**: 企业微信 Markdown 消息有长度限制（4096 字符）。解决方案：

1. **调高阈值**：只推送重大变化（如 ±10%）
2. **分段推送**：将报告拆分为多条消息
3. **简化版**：只推送摘要，详情查看日志

---

#### Q8: 如何停止监控？

**A**: 

```bash
# 删除 cron 任务
crontab -l | grep -v "ARK" | crontab -

# 停用云函数
# 在腾讯云控制台禁用定时触发器即可
```

---

### 11.3 技术参考

#### 相关项目

- **import-pandas/ark_invest**: https://github.com/import-pandas/ark_invest
- **thisjustinh/ark-invest-history**: https://github.com/thisjustinh/ark-invest-history
- **cathiesark.com**: https://cathiesark.com (第三方可视化平台)

#### 官方资源

- **ARK Invest 官网**: https://ark-funds.com
- **企业微信机器人文档**: https://developer.work.weixin.qq.com/document/path/91770
- **腾讯云函数文档**: https://cloud.tencent.com/document/product/583

#### Python 库文档

- **pandas**: https://pandas.pydata.org/docs/
- **requests**: https://requests.readthedocs.io/
- **python-dotenv**: https://saurabh-kumar.com/python-dotenv/

---

### 11.4 许可证

本项目采用 **MIT License**。

**免责声明**:
- 本项目仅供个人学习和研究使用
- 数据来源于 ARK Invest 公开信息
- 不构成任何投资建议
- 使用本项目产生的投资损失，开发者不承担任何责任

---

### 11.5 更新日志

#### v1.0.0 (2025-01-12)
- ✅ 初始版本发布
- ✅ 实现核心功能：数据采集、分析、推送
- ✅ 支持本地定时任务
- ✅ 支持云函数备份（可选）
- ✅ 完整文档

---

### 11.6 联系方式

- **项目路径**: `/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK`
- **文档版本**: v1.0.0
- **最后更新**: 2025-01-12

---

## 🎉 项目开发准备就绪！

现在你可以基于本文档开始开发项目了。建议按以下顺序进行：

1. ✅ 阅读完整文档，理解架构设计
2. ✅ 执行初始化脚本，搭建项目结构
3. ✅ 配置企业微信 Webhook
4. ✅ 开发 MVP 版本（数据采集 → 分析 → 推送）
5. ✅ 测试基础功能
6. ✅ 部署定时任务
7. ✅ 添加云函数备份（可选）
8. ✅ 持续优化和增强

**祝开发顺利！** 🚀

---

**文档结束**
