# Data Model: ARK 持仓监控系统

**Feature**: 001-ark-monitor  
**Date**: 2025-11-13  
**Status**: Phase 1 Complete

---

## Overview

本文档定义系统中所有数据结构、存储格式和转换规则。所有模块必须遵循此数据模型进行交互。

---

## Core Data Structures

### 1. HoldingRecord - 单条持仓记录

**用途**: 代表某只 ETF 在特定日期对单只股票的持仓信息

**Python 定义**:

```python
from dataclasses import dataclass

@dataclass
class HoldingRecord:
    """单条持仓记录"""
    date: str           # 日期，格式 YYYY-MM-DD
    etf_symbol: str     # ETF 代码（ARKK/ARKW/ARKG/ARKQ/ARKF）
    company: str        # 公司全称
    ticker: str         # 股票代码
    cusip: str          # CUSIP 编码（可选）
    shares: float       # 持股数量
    market_value: float # 市值（美元）
    weight: float       # 权重（百分比，如 9.15 表示 9.15%）
```

**DataFrame 表示** (pandas):

| 列名 | 数据类型 | 示例值 | 说明 |
|------|---------|--------|------|
| `date` | str | `2025-01-15` | 日期 |
| `etf_symbol` | str | `ARKK` | ETF 代码 |
| `company` | str | `TESLA INC` | 公司全称（大写） |
| `ticker` | str | `TSLA` | 股票代码 |
| `cusip` | str | `88160R101` | CUSIP 编码 |
| `shares` | float | `3245678.0` | 持股数量 |
| `market_value` | float | `850123456.78` | 市值 |
| `weight` | float | `9.15` | 权重百分比 |

**验证规则**:
- `date` 必须匹配正则 `^\d{4}-\d{2}-\d{2}$`
- `etf_symbol` 必须在 `['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']` 中
- `ticker` 非空且长度 1-5 字符
- `shares` > 0
- `market_value` > 0
- `weight` 在 0-100 范围

---

### 2. ChangedHolding - 变化持仓记录

**用途**: 代表单只股票的持仓变化详情（增持或减持）

**Python 定义**:

```python
@dataclass
class ChangedHolding:
    """变化持仓记录"""
    ticker: str              # 股票代码
    company: str             # 公司名称
    previous_shares: float   # 前一日持股数
    current_shares: float    # 当前持股数
    change_pct: float        # 变化百分比（如 +15.2 表示增持 15.2%）
    previous_weight: float   # 前一日权重
    current_weight: float    # 当前权重
    weight_change: float     # 权重变化（百分点，如 +1.5 表示权重从 8% 增加到 9.5%）
```

**计算公式**:

```python
change_pct = ((current_shares - previous_shares) / previous_shares) * 100
weight_change = current_weight - previous_weight
```

**示例**:

```python
ChangedHolding(
    ticker='TSLA',
    company='TESLA INC',
    previous_shares=2800000.0,
    current_shares=3245678.0,
    change_pct=15.92,        # (3245678 - 2800000) / 2800000 * 100
    previous_weight=8.20,
    current_weight=9.15,
    weight_change=0.95       # 9.15 - 8.20
)
```

---

### 3. ChangeAnalysis - 持仓变化分析结果

**用途**: 代表单个 ETF 在两个日期之间的完整持仓变化分析

**Python 定义**:

```python
@dataclass
class ChangeAnalysis:
    """持仓变化分析结果"""
    etf_symbol: str                    # ETF 代码
    current_date: str                  # 当前日期 YYYY-MM-DD
    previous_date: str                 # 前一日期 YYYY-MM-DD
    added: List[HoldingRecord]         # 新增股票列表
    removed: List[HoldingRecord]       # 移除股票列表
    increased: List[ChangedHolding]    # 增持股票列表（变化 >= threshold）
    decreased: List[ChangedHolding]    # 减持股票列表（变化 <= -threshold）
    top5_holdings: List[HoldingRecord] # 当前前 5 大持仓
    total_holdings_count: int          # 当前总持仓数量
```

**示例**:

```python
ChangeAnalysis(
    etf_symbol='ARKK',
    current_date='2025-01-15',
    previous_date='2025-01-14',
    added=[
        HoldingRecord(ticker='HOOD', company='ROBINHOOD MARKETS INC', ...)
    ],
    removed=[
        HoldingRecord(ticker='SPOT', company='SPOTIFY TECHNOLOGY SA', ...)
    ],
    increased=[
        ChangedHolding(ticker='TSLA', change_pct=15.92, ...)
    ],
    decreased=[
        ChangedHolding(ticker='COIN', change_pct=-8.35, ...)
    ],
    top5_holdings=[...],
    total_holdings_count=42
)
```

---

### 4. PushStatus - 推送状态记录

**用途**: 记录某日是否已成功推送报告，用于防止重复推送

**Python 定义**:

```python
@dataclass
class PushStatus:
    """推送状态记录"""
    date: str                  # 日期 YYYY-MM-DD
    pushed_at: str             # 推送时间（ISO 8601 格式）
    success: bool              # 是否成功
    etfs_processed: List[str]  # 已处理的 ETF 列表
    error_message: Optional[str] = None  # 错误信息（失败时）
```

**JSON 存储格式** (`data/cache/push_status.json`):

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
  }
}
```

**操作**:
- **写入**: 每次推送成功/失败后更新
- **读取**: 检查某日是否已推送（`--check-missed` 使用）
- **清理**: 保留最近 30 天记录，自动删除过期

---

### 5. Config - 配置对象

**用途**: 封装所有系统配置参数

**Python 定义**:

```python
@dataclass
class ScheduleConfig:
    """定时任务配置"""
    enabled: bool       # 是否启用
    cron_time: str      # 执行时间（如 "11:00"）
    timezone: str       # 时区（如 "Asia/Shanghai"）

@dataclass
class DataConfig:
    """数据配置"""
    etfs: List[str]     # 监控的 ETF 列表
    data_dir: str       # 数据存储目录
    log_dir: str        # 日志存储目录

@dataclass
class AnalysisConfig:
    """分析配置"""
    change_threshold: float  # 显著变化阈值（%）

@dataclass
class NotificationConfig:
    """通知配置"""
    webhook_url: str           # 企业微信 Webhook URL
    enable_error_alert: bool   # 是否发送错误告警

@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int           # 最大重试次数
    retry_delays: List[int]    # 重试延迟列表（秒）

@dataclass
class LogConfig:
    """日志配置"""
    retention_days: int  # 保留天数
    level: str          # 日志级别（DEBUG/INFO/WARNING/ERROR）

@dataclass
class Config:
    """系统配置"""
    schedule: ScheduleConfig
    data: DataConfig
    analysis: AnalysisConfig
    notification: NotificationConfig
    retry: RetryConfig
    log: LogConfig
```

**YAML 配置文件示例** (`config.yaml`):

```yaml
schedule:
  enabled: true
  cron_time: "11:00"
  timezone: "Asia/Shanghai"

data:
  etfs: ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"]
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
```

---

## File Storage Formats

### CSV 文件（持仓数据）

**路径**: `data/holdings/{ETF_SYMBOL}/{YYYY-MM-DD}.csv`

**格式**:

```csv
date,etf_symbol,company,ticker,cusip,shares,market_value,weight
2025-01-15,ARKK,TESLA INC,TSLA,88160R101,3245678.0,850123456.78,9.15
2025-01-15,ARKK,COINBASE GLOBAL INC,COIN,19260Q107,2145789.0,412567890.12,4.44
```

**编码**: UTF-8  
**分隔符**: 逗号 `,`  
**引号**: 可选（仅在字段包含逗号时使用）

**存储策略**:
- ✅ 历史数据**永不覆盖**
- ✅ 文件命名严格遵循 `YYYY-MM-DD.csv`
- ✅ 每日一个文件，按 ETF 分目录

---

### Markdown 文件（报告）

**路径**: `data/reports/{ETF_SYMBOL}/{YYYY-MM-DD}.md`

**格式**: 标准 Markdown

**示例**:

```markdown
# ARKK 持仓变化 (2025-01-15)

## 📊 概览
- 对比日期: 2025-01-14 → 2025-01-15
- 新增持仓: 1 只
- 移除持仓: 1 只
- 增持: 3 只
- 减持: 2 只

## ✅ 新增持仓
- **HOOD** Robinhood Markets Inc (0.5%)

## ❌ 移除持仓
- **SPOT** Spotify Technology SA (之前 1.2%)

## 📈 显著增持 (>5%)
- **TSLA** Tesla Inc: +15.9% (8.2% → 9.15%)

## 📉 显著减持 (>5%)
- **COIN** Coinbase Global Inc: -8.4% (4.84% → 4.44%)

## 📋 前 5 大持仓
1. TSLA Tesla Inc (9.15%)
2. COIN Coinbase Global Inc (4.44%)
3. ROKU Roku Inc (4.18%)
4. ZM Zoom Video Communications Inc (3.24%)
5. SQ Block Inc (3.21%)
```

**存储策略**:
- ✅ 本地备份每日报告
- ✅ 推送失败时保存到 `data/reports/failed/{YYYY-MM-DD}.md`

---

### JSON 文件（推送状态）

**路径**: `data/cache/push_status.json`

**格式**:

```json
{
  "2025-01-15": {
    "pushed_at": "2025-01-15T11:05:23+08:00",
    "success": true,
    "etfs_processed": ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"],
    "error_message": null
  }
}
```

**编码**: UTF-8  
**缩进**: 2 空格

**存储策略**:
- ✅ 仅保留最近 30 天记录
- ✅ 每次推送后立即更新
- ✅ 文件不存在时自动创建空对象 `{}`

---

## Data Transformations

### 1. ARK CSV → HoldingRecord DataFrame

**输入**: ARK 官方 CSV

```csv
date,fund,company,ticker,cusip,shares,market value($),weight(%)
01/15/2025,ARKK,TESLA INC,TSLA,88160R101,3245678,850123456.78,9.15
```

**输出**: pandas DataFrame

| date | etf_symbol | company | ticker | cusip | shares | market_value | weight |
|------|------------|---------|--------|-------|--------|-------------|--------|
| 2025-01-15 | ARKK | TESLA INC | TSLA | 88160R101 | 3245678.0 | 850123456.78 | 9.15 |

**转换规则**:
1. 列名清理：去除空格和特殊字符，转小写
2. 日期格式转换：`MM/DD/YYYY` → `YYYY-MM-DD`
3. 数值类型转换：`shares`, `market_value`, `weight` 转 float
4. 删除无效行：`ticker` 或 `shares` 为空的行

**代码示例**:

```python
import pandas as pd
from datetime import datetime

def transform_ark_csv(df: pd.DataFrame) -> pd.DataFrame:
    # 1. 清理列名
    df.columns = df.columns.str.strip().str.lower().str.replace('[^a-z0-9]', '_', regex=True)
    
    # 2. 重命名列
    df = df.rename(columns={
        'fund': 'etf_symbol',
        'market_value': 'market_value',
        'weight': 'weight'
    })
    
    # 3. 日期转换
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y').dt.strftime('%Y-%m-%d')
    
    # 4. 数值转换
    df['shares'] = pd.to_numeric(df['shares'], errors='coerce')
    df['market_value'] = pd.to_numeric(df['market_value'], errors='coerce')
    df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
    
    # 5. 删除无效行
    df = df.dropna(subset=['ticker', 'shares'])
    
    return df
```

---

### 2. DataFrame 对比 → ChangeAnalysis

**输入**: 
- `current_df`: 当前持仓 DataFrame
- `previous_df`: 前一日持仓 DataFrame

**输出**: `ChangeAnalysis` 对象

**算法**:

```python
def create_change_analysis(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    etf_symbol: str,
    current_date: str,
    previous_date: str,
    threshold: float = 5.0
) -> ChangeAnalysis:
    # 1. Merge 两个 DataFrame
    merged = pd.merge(
        current_df[['ticker', 'company', 'shares', 'weight']],
        previous_df[['ticker', 'shares', 'weight']],
        on='ticker',
        how='outer',
        suffixes=('_current', '_previous'),
        indicator=True
    )
    
    # 2. 识别新增
    added = merged[merged['_merge'] == 'left_only']
    
    # 3. 识别移除
    removed = merged[merged['_merge'] == 'right_only']
    
    # 4. 识别共同持有
    common = merged[merged['_merge'] == 'both'].copy()
    
    # 5. 计算变化百分比
    common['shares_change_pct'] = (
        (common['shares_current'] - common['shares_previous']) / 
        common['shares_previous'] * 100
    )
    common['weight_change'] = common['weight_current'] - common['weight_previous']
    
    # 6. 过滤显著变化
    increased = common[common['shares_change_pct'] >= threshold]
    decreased = common[common['shares_change_pct'] <= -threshold]
    
    # 7. 前 5 大持仓
    top5 = current_df.nlargest(5, 'weight')
    
    # 8. 构造返回对象
    return ChangeAnalysis(
        etf_symbol=etf_symbol,
        current_date=current_date,
        previous_date=previous_date,
        added=added.to_dict('records'),
        removed=removed.to_dict('records'),
        increased=increased.to_dict('records'),
        decreased=decreased.to_dict('records'),
        top5_holdings=top5.to_dict('records'),
        total_holdings_count=len(current_df)
    )
```

---

### 3. ChangeAnalysis → Markdown Report

**输入**: `List[ChangeAnalysis]`（多个 ETF 的分析结果）

**输出**: Markdown 字符串

**模板**:

```python
def generate_markdown(analyses: List[ChangeAnalysis]) -> str:
    lines = []
    
    # 1. 标题
    lines.append(f"## 🚀 ARK 持仓日报 ({analyses[0].current_date})")
    lines.append("")
    
    # 2. 整体概况
    lines.append("### 📊 整体概况")
    lines.append(f"- 监控 ETF: {len(analyses)} 只")
    changed_count = sum(1 for a in analyses if a.added or a.removed or a.increased or a.decreased)
    lines.append(f"- 有变化: {changed_count} 只")
    lines.append("")
    
    # 3. 分 ETF 详情
    for analysis in analyses:
        lines.append(f"### 🔥 {analysis.etf_symbol}")
        
        # 新增
        if analysis.added:
            lines.append("**✅ 新增持仓**:")
            for record in analysis.added:
                lines.append(f"- **{record['ticker']}** {record['company']} ({record['weight']:.2f}%)")
        
        # 移除
        if analysis.removed:
            lines.append("**❌ 移除持仓**:")
            for record in analysis.removed:
                lines.append(f"- **{record['ticker']}** {record['company']}")
        
        # 增持
        if analysis.increased:
            lines.append("**📈 显著增持**:")
            for change in analysis.increased:
                lines.append(f"- **{change['ticker']}** {change['company']}: +{change['change_pct']:.1f}%")
        
        # 减持
        if analysis.decreased:
            lines.append("**📉 显著减持**:")
            for change in analysis.decreased:
                lines.append(f"- **{change['ticker']}** {change['company']}: {change['change_pct']:.1f}%")
        
        lines.append("")
    
    return "\n".join(lines)
```

---

## Validation Rules

### HoldingRecord 验证

```python
def validate_holding_record(record: dict) -> None:
    """验证单条持仓记录"""
    # 日期格式
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', record['date']):
        raise ValueError(f"日期格式错误: {record['date']}")
    
    # ETF 代码
    if record['etf_symbol'] not in ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']:
        raise ValueError(f"无效的 ETF 代码: {record['etf_symbol']}")
    
    # 股票代码
    if not record['ticker'] or len(record['ticker']) > 5:
        raise ValueError(f"无效的股票代码: {record['ticker']}")
    
    # 数值范围
    if record['shares'] <= 0:
        raise ValueError(f"持股数量必须 >0: {record['shares']}")
    
    if record['market_value'] <= 0:
        raise ValueError(f"市值必须 >0: {record['market_value']}")
    
    if not (0 <= record['weight'] <= 100):
        raise ValueError(f"权重必须在 0-100 范围: {record['weight']}")
```

### Config 验证

```python
def validate_config(config: Config) -> None:
    """验证配置完整性"""
    # Webhook URL
    if not config.notification.webhook_url:
        raise ValueError("未配置 WECHAT_WEBHOOK_URL")
    
    if not config.notification.webhook_url.startswith('https://qyapi.weixin.qq.com'):
        raise ValueError("WECHAT_WEBHOOK_URL 格式错误")
    
    # 阈值范围
    if not (0.1 <= config.analysis.change_threshold <= 100):
        raise ValueError(f"change_threshold 必须在 0.1-100 范围: {config.analysis.change_threshold}")
    
    # ETF 列表
    if not config.data.etfs:
        raise ValueError("ETF 列表不能为空")
    
    valid_etfs = {'ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF'}
    for etf in config.data.etfs:
        if etf not in valid_etfs:
            raise ValueError(f"无效的 ETF 代码: {etf}")
```

---

## Data Flow Diagram

```
                    ┌──────────────────┐
                    │  ARK Official    │
                    │  CSV (ARKK.csv)  │
                    └────────┬─────────┘
                             │ HTTP GET
                             ▼
                    ┌──────────────────┐
                    │   DataFetcher    │
                    │  (fetch_holdings)│
                    └────────┬─────────┘
                             │ Transform
                             ▼
                    ┌──────────────────┐
                    │ HoldingRecord DF │
                    │  (current.csv)   │
                    └────────┬─────────┘
                             │
                             ├────────────────────┐
                             │                    │
                             ▼                    ▼
                    ┌──────────────────┐  ┌──────────────────┐
                    │   Analyzer       │  │ previous.csv     │
                    │ (compare_holdings│  │ (从本地加载)      │
                    └────────┬─────────┘  └────────┬─────────┘
                             │                    │
                             └─────────┬──────────┘
                                       │ Merge & Calculate
                                       ▼
                              ┌──────────────────┐
                              │ ChangeAnalysis   │
                              │  (对象)           │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ ReportGenerator  │
                              │ (generate_md)    │
                              └────────┬─────────┘
                                       │ Format
                                       ▼
                              ┌──────────────────┐
                              │ Markdown String  │
                              └────────┬─────────┘
                                       │
                                       ├────────────────────┐
                                       │                    │
                                       ▼                    ▼
                              ┌──────────────────┐  ┌──────────────────┐
                              │ WeChatNotifier   │  │ Save to          │
                              │ (send_markdown)  │  │ reports/*.md     │
                              └──────────────────┘  └──────────────────┘
```

---

**Data Model Status**: ✅ Complete | **Date**: 2025-11-13

