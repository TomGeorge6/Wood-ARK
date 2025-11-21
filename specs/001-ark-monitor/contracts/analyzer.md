# 模块契约：Analyzer

**模块名称**: `src/analyzer.py`  
**职责**: 单基金持仓变化分析  
**版本**: v2.0  
**最后更新**: 2025-11-14

---

## 📋 模块概述

`Analyzer` 负责对比单个 ETF 前后两日的持仓数据，识别新增、移除、增持、减持。

**核心功能**:
- 对比持仓数据（DataFrame merge）
- 计算持股数变化百分比 ⭐
- 识别显著变化（基于阈值）
- 提取 Top 10 持仓（v2.0 更新）
- 生成结构化分析结果

---

## 🔌 公共接口

### 类定义

```python
class Analyzer:
    """单基金持仓变化分析器"""
    
    def __init__(self, threshold: float = 5.0):
        """初始化分析器
        
        Args:
            threshold: 显著变化阈值（百分比，默认 5.0）
        """
```

---

### 方法：compare_holdings

**功能**: 对比两个日期的持仓数据，生成变化分析

**签名**:
```python
def compare_holdings(
    self,
    current: pd.DataFrame,
    previous: pd.DataFrame,
    etf_symbol: str,
    current_date: str,
    previous_date: str
) -> ChangeAnalysis
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `current` | `pd.DataFrame` | 当前日期持仓数据 |
| `previous` | `pd.DataFrame` | 前一日期持仓数据 |
| `etf_symbol` | `str` | ETF 代码（如 "ARKK"） |
| `current_date` | `str` | 当前日期（YYYY-MM-DD） |
| `previous_date` | `str` | 前一日期（YYYY-MM-DD） |

**返回值**:
- **类型**: `ChangeAnalysis`
- **说明**: 持仓变化分析结果对象

**实现逻辑**:
1. **合并数据**: 使用 `pd.merge()` 按 `ticker` 合并
   ```python
   merged = pd.merge(
       current, previous,
       on='ticker',
       how='outer',
       suffixes=('_current', '_previous')
   )
   ```

2. **识别新增**: `ticker` 在 `current` 中存在但在 `previous` 中不存在
   ```python
   added = merged[merged['shares_previous'].isna()]
   ```

3. **识别移除**: `ticker` 在 `previous` 中存在但在 `current` 中不存在
   ```python
   removed = merged[merged['shares_current'].isna()]
   ```

4. **计算变化**: 持股数变化百分比 ⭐
   ```python
   merged['change_pct'] = (
       (merged['shares_current'] - merged['shares_previous']) /
       merged['shares_previous'] * 100
   )
   ```

5. **过滤显著变化**: 绝对值 ≥ `threshold`
   ```python
   increased = merged[merged['change_pct'] >= threshold]
   decreased = merged[merged['change_pct'] <= -threshold]
   ```

6. **提取 Top 10**: 按权重降序排序（v2.0 更新）⭐
   ```python
   top10 = current.nlargest(10, 'weight')
   ```

7. **返回结果**: 构造 `ChangeAnalysis` 对象

---

## 📦 数据模型

### ChangeAnalysis

持仓变化分析结果对象。

```python
@dataclass
class ChangeAnalysis:
    """持仓变化分析结果"""
    
    etf_symbol: str                         # ETF 代码
    current_date: str                       # 当前日期
    previous_date: str                      # 前一日期
    
    added: List[HoldingRecord]              # 新增股票
    removed: List[HoldingRecord]            # 移除股票
    increased: List[ChangedHolding]         # 显著增持
    decreased: List[ChangedHolding]         # 显著减持
    
    top10_holdings: List[HoldingRecord]     # Top 10 持仓（v2.0）⭐
```

### HoldingRecord

单条持仓记录。

```python
@dataclass
class HoldingRecord:
    """单条持仓记录"""
    
    ticker: str              # 股票代码
    company: str             # 公司名称
    shares: float            # 持股数
    market_value: float      # 市值（美元）
    weight: float            # 权重（%）
```

### ChangedHolding

变化持仓记录。

```python
@dataclass
class ChangedHolding:
    """变化持仓记录"""
    
    ticker: str              # 股票代码
    company: str             # 公司名称
    
    previous_shares: float   # 前一日持股数
    current_shares: float    # 当前持股数
    change_pct: float        # 变化百分比（%）⭐
    
    previous_weight: float   # 前一日权重
    current_weight: float    # 当前权重
    weight_change: float     # 权重变化（百分点）
```

---

## 🔗 依赖关系

### 内部依赖
- `src.utils` - 日志记录
- 无其他内部依赖（独立模块）

### 外部依赖
- `pandas` - DataFrame 操作
- `dataclasses` - 数据类定义
- `typing` - 类型提示
- `logging` - 日志记录

### 被依赖
- `main.py` - 调用 `compare_holdings()`
- `src.summary_analyzer` - 使用 `ChangeAnalysis` 数据模型
- `src.image_generator` - 使用 `ChangeAnalysis` 数据

---

## 🚫 职责边界

### ✅ 负责
- 持仓数据对比（merge 操作）
- 变化百分比计算（持股数 ⭐）
- 新增/移除股票识别
- 显著变化过滤（基于阈值）
- Top 10 提取
- 数据结构化组织

### ❌ 不负责
- 数据下载（由 `fetcher` 负责）
- 历史数据加载（由 `fetcher` 负责）
- 报告生成（由 `reporter` 和 `notifier` 负责）
- 跨基金汇总分析（由 `summary_analyzer` 负责）
- 趋势图绘制（由 `image_generator` 负责）

---

## 📝 使用示例

```python
from src.analyzer import Analyzer
from src.fetcher import DataFetcher

# 初始化
analyzer = Analyzer(threshold=5.0)
fetcher = DataFetcher(config)

# 加载数据
current = fetcher.load_from_csv('ARKK', '2025-11-14')
previous = fetcher.load_from_csv('ARKK', '2025-11-13')

# 分析变化
analysis = analyzer.compare_holdings(
    current=current,
    previous=previous,
    etf_symbol='ARKK',
    current_date='2025-11-14',
    previous_date='2025-11-13'
)

# 输出结果
print(f"新增: {len(analysis.added)} 只")
print(f"移除: {len(analysis.removed)} 只")
print(f"显著增持: {len(analysis.increased)} 只")
print(f"显著减持: {len(analysis.decreased)} 只")
print(f"Top 10: {[h.ticker for h in analysis.top10_holdings]}")
```

---

## ⚠️ 注意事项

1. **变化百分比计算** ⭐:
   - 基于**持股数**（shares），而非权重（weight）
   - 原因：权重受基金总资产影响，持股数更准确反映买卖行为
   - 公式：`(current_shares - previous_shares) / previous_shares × 100%`

2. **阈值配置**:
   - 默认 5.0%（可通过构造函数参数调整）
   - 推荐范围：3.0% ~ 10.0%
   - 低于阈值的变化不显示在报告中

3. **Top 10 排序** ⭐:
   - v2.0 从 Top 5 改为 Top 10
   - 按**权重**降序排序（weight 字段）
   - 用于汇总报告和趋势图

4. **数据质量假设**:
   - 假设输入 DataFrame 格式正确
   - 不处理缺失值（NaN）- 由 `fetcher` 保证数据完整性

5. **性能考虑**:
   - DataFrame merge 复杂度 O(N log N)
   - 实际运行时间 <0.5 秒（单基金 ~50 只股票）

---

## 🧪 测试要点

### 单元测试
- `test_compare_holdings_added()` - 测试新增股票识别
- `test_compare_holdings_removed()` - 测试移除股票识别
- `test_compare_holdings_increased()` - 测试增持识别
- `test_compare_holdings_decreased()` - 测试减持识别
- `test_compare_holdings_threshold()` - 测试阈值过滤
- `test_compare_holdings_top10()` - 测试 Top 10 提取（v2.0）
- `test_change_pct_calculation()` - 测试变化百分比计算（基于持股数）

### 边界测试
- 空 DataFrame（无持仓）
- 完全相同的持仓（无变化）
- 所有股票都新增/移除
- 阈值为 0（所有变化都显示）

### 集成测试
- 使用真实 CSV 数据验证分析结果
- 与手工计算结果对比（准确性验证）

---

## 📊 性能指标

| 操作 | 平均耗时 | 说明 |
|------|---------|------|
| `compare_holdings()` | <0.5 秒 | 单基金 ~50 只股票 |
| DataFrame merge | ~0.1 秒 | pandas 优化算法 |
| 变化计算 | ~0.1 秒 | 向量化操作 |
| 排序过滤 | ~0.1 秒 | - |

---

## 🔄 版本变更

### v2.0 (2025-11-14)
- ✅ Top 5 改为 Top 10（支持汇总报告）
- ✅ 确认变化百分比基于持股数（shares）
- ✅ 添加详细的数据模型文档

### v1.0 (2025-11-13)
- ✅ 初始实现
- ✅ 支持新增/移除/增持/减持识别
- ✅ 支持阈值过滤

---

**契约状态**: ✅ 已实现（v2.0）  
**测试覆盖率**: 90%+  
**最后审核**: 2025-11-14
