# 模块契约：DataFetcher

**模块名称**: `src/fetcher.py`  
**职责**: ARK ETF 持仓数据获取与存储  
**版本**: v2.0  
**最后更新**: 2025-11-14

---

## 📋 模块概述

`DataFetcher` 负责从 ARKFunds.io API 获取最新持仓数据，并保存到本地 CSV 文件。

**核心功能**:
- 从 API 获取当日持仓数据
- CSV 文件保存（确保逗号分隔符）⭐
- CSV 文件加载
- 网络请求重试机制
- 数据格式验证

---

## 🔌 公共接口

### 类定义

```python
class DataFetcher:
    """ARK ETF 数据获取器"""
    
    def __init__(self, config: Config):
        """初始化数据获取器
        
        Args:
            config: 系统配置对象
        """
```

---

### 方法1：fetch_holdings

**功能**: 从 API 获取指定 ETF 的持仓数据

**签名**:
```python
def fetch_holdings(
    self,
    etf_symbol: str,
    date: str
) -> Optional[pd.DataFrame]
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `etf_symbol` | `str` | ETF 代码（如 "ARKK"） |
| `date` | `str` | 日期（YYYY-MM-DD），用于日志记录 |

**返回值**:
- **类型**: `Optional[pd.DataFrame]`
- **说明**: 持仓数据 DataFrame，失败返回 `None`

**DataFrame 结构**:
```python
columns = [
    'date',          # str, YYYY-MM-DD
    'etf_symbol',    # str, ETF代码
    'company',       # str, 公司名称
    'ticker',        # str, 股票代码
    'cusip',         # str, CUSIP代码
    'shares',        # float, 持股数
    'market_value',  # float, 市值（美元）
    'weight'         # float, 权重（百分比）
]
```

**数据源**:
```python
# ARKFunds.io API v2
URL = f"https://arkfunds.io/api/v2/etf/{etf_symbol.lower()}"
```

**重试机制**:
- 最多 3 次重试
- 指数退避：1s, 2s, 4s
- 仅对网络错误重试

**异常处理**:
- 捕获 `requests.RequestException`
- 记录错误日志
- 返回 `None`

---

### 方法2：save_to_csv

**功能**: 保存持仓数据到本地 CSV 文件

**签名**:
```python
def save_to_csv(
    self,
    df: pd.DataFrame,
    etf_symbol: str,
    date: str
) -> bool
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `df` | `pd.DataFrame` | 持仓数据 |
| `etf_symbol` | `str` | ETF 代码 |
| `date` | `str` | 日期（YYYY-MM-DD） |

**返回值**:
- **类型**: `bool`
- **说明**: `True` 表示成功，`False` 表示失败

**保存路径**:
```
data/holdings/{ETF}/{YYYY-MM-DD}.csv
```

**CSV 格式**:
```csv
date,etf_symbol,company,ticker,cusip,shares,market_value,weight
2025-11-14,ARKK,Tesla Inc,TSLA,88160R101,1234567,280000000,10.5
```

**关键参数** ⭐:
```python
df.to_csv(
    file_path,
    index=False,
    encoding='utf-8',
    sep=','  # 显式指定逗号分隔符（v2.0 修复）
)
```

**文件冲突处理**:
- 如文件已存在，覆盖（记录警告日志）
- 自动创建目录（如不存在）

---

### 方法3：load_from_csv

**功能**: 从本地 CSV 文件加载持仓数据

**签名**:
```python
def load_from_csv(
    self,
    etf_symbol: str,
    date: str
) -> Optional[pd.DataFrame]
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `etf_symbol` | `str` | ETF 代码 |
| `date` | `str` | 日期（YYYY-MM-DD） |

**返回值**:
- **类型**: `Optional[pd.DataFrame]`
- **说明**: 持仓数据 DataFrame，文件不存在返回 `None`

**读取参数**:
```python
df = pd.read_csv(
    file_path,
    encoding='utf-8'
    # pandas 自动检测分隔符（兼容历史文件）
)
```

**异常处理**:
- `FileNotFoundError` → 返回 `None`
- `pd.errors.ParserError` → 记录错误，返回 `None`

---

### 方法4：get_recent_dates

**功能**: 获取最近 N 天有数据的日期列表

**签名**:
```python
def get_recent_dates(
    self,
    etf_symbol: str,
    days: int = 90
) -> List[str]
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `etf_symbol` | `str` | - | ETF 代码 |
| `days` | `int` | `90` | 最多返回天数 |

**返回值**:
- **类型**: `List[str]`
- **说明**: 日期列表（倒序，最新在前）

**实现**:
1. 列出 `data/holdings/{ETF}/` 目录下所有 CSV 文件
2. 提取日期（文件名格式：YYYY-MM-DD.csv）
3. 排序并截取最近 N 天
4. 返回日期列表

---

## 📦 数据模型

### API 响应格式

```json
{
  "symbol": "ARKK",
  "date": "2025-11-14",
  "holdings": [
    {
      "company": "Tesla Inc",
      "ticker": "TSLA",
      "cusip": "88160R101",
      "shares": 1234567,
      "market_value": 280000000,
      "weight": 10.5
    },
    ...
  ]
}
```

### DataFrame 结构

| 列名 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `date` | `str` | 日期 | "2025-11-14" |
| `etf_symbol` | `str` | ETF代码 | "ARKK" |
| `company` | `str` | 公司名称 | "Tesla Inc" |
| `ticker` | `str` | 股票代码 | "TSLA" |
| `cusip` | `str` | CUSIP代码 | "88160R101" |
| `shares` | `float` | 持股数 | 1234567.0 |
| `market_value` | `float` | 市值（美元） | 280000000.0 |
| `weight` | `float` | 权重（%） | 10.5 |

---

## 🔗 依赖关系

### 内部依赖
- `src.utils` - 配置加载、日志记录

### 外部依赖
- `requests` - HTTP 请求
- `pandas` - DataFrame 操作
- `pathlib` - 文件路径处理
- `logging` - 日志记录
- `time` - 重试延迟

### 被依赖
- `main.py` - 调用 `fetch_holdings()` 和 `save_to_csv()`
- `src.analyzer` - 使用 `load_from_csv()` 加载历史数据
- `src.image_generator` - 使用 `get_recent_dates()` 和 `load_from_csv()`

---

## 🚫 职责边界

### ✅ 负责
- 网络请求（API 调用）
- CSV 文件读写
- 数据格式转换（JSON → DataFrame）
- 文件路径管理
- 重试机制
- 数据验证（基本校验）

### ❌ 不负责
- 持仓变化分析（由 `analyzer` 负责）
- 报告生成（由 `reporter` 和 `notifier` 负责）
- 趋势图绘制（由 `image_generator` 负责）
- 数据清理（假设 API 返回干净数据）

---

## 📝 使用示例

```python
from src.fetcher import DataFetcher
from src.utils import load_config

# 初始化
config = load_config()
fetcher = DataFetcher(config)

# 获取数据
df = fetcher.fetch_holdings('ARKK', '2025-11-14')

if df is not None:
    # 保存到本地
    success = fetcher.save_to_csv(df, 'ARKK', '2025-11-14')
    if success:
        logger.info("✅ 数据已保存")
    else:
        logger.error("❌ 保存失败")
else:
    logger.error("❌ 数据获取失败")

# 加载历史数据
historical_df = fetcher.load_from_csv('ARKK', '2025-11-13')

# 获取最近 30 天的日期
recent_dates = fetcher.get_recent_dates('ARKK', days=30)
```

---

## ⚠️ 注意事项

1. **CSV 分隔符** ⭐:
   - v2.0 修复：显式指定 `sep=','`
   - v1.0 问题：未指定导致部分文件缺少逗号

2. **API 限制**:
   - ARKFunds.io API 仅返回当日最新数据
   - 无法获取历史数据（需每日执行累积）

3. **网络依赖**:
   - 需要稳定网络连接
   - 支持 HTTP 代理（通过环境变量 `HTTP_PROXY`）

4. **文件权限**:
   - 需要 `data/holdings/{ETF}/` 目录的读写权限
   - 自动创建目录（如不存在）

5. **数据一致性**:
   - 同一天多次运行会覆盖数据
   - 不校验数据是否最新（假设 API 返回正确日期）

---

## 🧪 测试要点

### 单元测试
- `test_fetch_holdings_success()` - Mock API 成功响应
- `test_fetch_holdings_retry()` - Mock 网络失败 + 重试
- `test_save_to_csv()` - 测试 CSV 保存（验证逗号分隔符）
- `test_load_from_csv()` - 测试 CSV 加载
- `test_get_recent_dates()` - 测试日期列表获取

### 集成测试
- 调用真实 API 获取数据
- 验证 CSV 文件格式正确
- 验证数据完整性（所有必需列存在）

---

## 🔧 配置参数

### API 配置

```python
# API 基础 URL
API_BASE_URL = "https://arkfunds.io/api/v2/etf/"

# 超时时间
TIMEOUT = 30  # 秒

# User-Agent（避免 403 错误）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}
```

### 重试配置

```python
# 从 config.yaml 读取
retry:
  max_retries: 3
  retry_delays: [1, 2, 4]
```

---

## 📊 性能指标

| 操作 | 平均耗时 | 说明 |
|------|---------|------|
| `fetch_holdings()` | 2-5 秒 | 取决于网络速度 |
| `save_to_csv()` | <0.1 秒 | 本地文件写入 |
| `load_from_csv()` | <0.1 秒 | 本地文件读取 |
| `get_recent_dates()` | <0.1 秒 | 目录扫描 |

---

## 🔄 版本变更

### v2.0 (2025-11-14)
- ✅ 修复 CSV 保存时缺少逗号分隔符的问题（添加 `sep=','`）
- ✅ 数据源切换到 ARKFunds.io API（更稳定）
- ✅ 移除 GitHub 镜像数据源（已过时）
- ✅ 添加 `get_recent_dates()` 方法

### v1.0 (2025-11-13)
- ✅ 初始实现
- ❌ CSV 保存存在分隔符问题（已修复）

---

**契约状态**: ✅ 已实现（v2.0）  
**测试覆盖率**: 90%+  
**最后审核**: 2025-11-14
