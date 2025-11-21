# 模块契约：SummaryAnalyzer

**模块名称**: `src/summary_analyzer.py`  
**职责**: ARK 全系列基金汇总分析  
**版本**: v2.0  
**最后更新**: 2025-11-14

---

## 📋 模块概述

`SummaryAnalyzer` 负责分析所有 ARK 基金的持仓数据，生成跨基金汇总分析结果。

**核心功能**:
- 分析跨基金重叠股票
- 识别各基金独家持仓
- 检测多基金同时增持/减持
- 生成基金对比统计

---

## 🔌 公共接口

### 类定义

```python
class SummaryAnalyzer:
    """ARK 全系列基金汇总分析器"""
    
    def __init__(self, config: Config):
        """初始化汇总分析器
        
        Args:
            config: 系统配置对象
        """
```

---

### 方法1：analyze_all_funds

**功能**: 分析所有基金数据，生成汇总结果

**签名**:
```python
def analyze_all_funds(
    self,
    all_holdings: Dict[str, pd.DataFrame],
    all_analyses: Dict[str, ChangeAnalysis],
    current_date: str
) -> Optional[SummaryAnalysis]
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `all_holdings` | `Dict[str, pd.DataFrame]` | 所有基金的当日持仓数据（key=ETF代码） |
| `all_analyses` | `Dict[str, ChangeAnalysis]` | 所有基金的持仓变化分析（key=ETF代码） |
| `current_date` | `str` | 当前日期（YYYY-MM-DD） |

**返回值**:
- **类型**: `Optional[SummaryAnalysis]`
- **说明**: 汇总分析结果对象，如果成功基金 <2 个则返回 `None`

**异常**:
- 无（内部处理所有异常并记录日志）

**实现逻辑**:
1. 验证数据完整性（至少2个基金成功）
2. 计算跨基金重叠股票
3. 识别各基金独家持仓（权重 ≥ `exclusive_threshold`）
4. 检测重点变化（多基金同时增持/减持）
5. 生成基金对比统计
6. 返回 `SummaryAnalysis` 对象

---

### 方法2：_calculate_overlaps

**功能**: 计算跨基金重叠股票

**签名**:
```python
def _calculate_overlaps(
    self,
    all_holdings: Dict[str, pd.DataFrame]
) -> List[OverlapHolding]
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `all_holdings` | `Dict[str, pd.DataFrame]` | 所有基金的持仓数据 |

**返回值**:
- **类型**: `List[OverlapHolding]`
- **说明**: 重叠股票列表，按出现基金数降序排序

**实现逻辑**:
1. 遍历所有股票代码（ticker）
2. 统计每只股票出现在哪些基金中
3. 计算跨基金总权重（各基金权重之和）
4. 过滤出现在 2+ 基金中的股票
5. 按出现基金数降序、总权重降序排序
6. 返回前 10 名

---

### 方法3：_identify_exclusives

**功能**: 识别各基金的独家持仓

**签名**:
```python
def _identify_exclusives(
    self,
    all_holdings: Dict[str, pd.DataFrame],
    threshold: float = 3.0
) -> Dict[str, List[HoldingRecord]]
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `all_holdings` | `Dict[str, pd.DataFrame]` | - | 所有基金的持仓数据 |
| `threshold` | `float` | `3.0` | 独家持仓权重阈值（百分比） |

**返回值**:
- **类型**: `Dict[str, List[HoldingRecord]]`
- **说明**: 各基金的独家持仓列表（key=ETF代码）

**实现逻辑**:
1. 遍历所有股票
2. 识别仅在单一基金中持有的股票
3. 过滤权重 ≥ `threshold` 的股票
4. 按基金分组
5. 每个基金最多返回 3 只

---

### 方法4：_detect_highlights

**功能**: 检测重点变化（多基金同时增持/减持）

**签名**:
```python
def _detect_highlights(
    self,
    all_analyses: Dict[str, ChangeAnalysis]
) -> List[Highlight]
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `all_analyses` | `Dict[str, ChangeAnalysis]` | 所有基金的变化分析 |

**返回值**:
- **类型**: `List[Highlight]`
- **说明**: 重点变化列表（最多5条）

**检测规则**:
1. **多基金同时增持**: 同一股票在 2+ 基金中都是"显著增持"
2. **多基金同时减持**: 同一股票在 2+ 基金中都是"显著减持"
3. **新增跨基金持仓**: 之前在单一基金，现在出现在 2+ 基金
4. **从独家变跨基金**: 某股票从独家持仓变为跨基金持仓

**优先级排序**:
- 涉及基金数越多，优先级越高
- 同等基金数，权重变化越大，优先级越高

---

## 📦 数据模型

### SummaryAnalysis

汇总分析结果对象。

```python
@dataclass
class SummaryAnalysis:
    """汇总分析结果"""
    
    date: str                                    # 日期
    total_holdings: int                          # 总持仓数
    overlap_count: int                           # 跨基金重叠数
    exclusive_count: int                         # 单基金独有数
    
    overlaps: List[OverlapHolding]               # 跨基金重叠 Top 10
    fund_stats: Dict[str, FundStats]             # 各基金统计（key=ETF代码）
    exclusives: Dict[str, List[HoldingRecord]]   # 各基金独家持仓
    highlights: List[Highlight]                  # 重点变化（最多5条）
```

### OverlapHolding

跨基金重叠股票。

```python
@dataclass
class OverlapHolding:
    """跨基金重叠股票"""
    
    ticker: str                      # 股票代码
    company: str                     # 公司名称
    fund_count: int                  # 出现基金数
    total_weight: float              # 跨基金总权重
    fund_weights: Dict[str, float]   # 各基金权重（key=ETF代码）
```

### FundStats

单个基金统计信息。

```python
@dataclass
class FundStats:
    """单个基金统计"""
    
    etf_symbol: str          # 基金代码
    name_cn: str             # 中文名称
    theme: str               # 投资主题
    holding_count: int       # 持仓数量
    top1_ticker: str         # 第1大持仓代码
    top1_weight: float       # 第1大持仓权重
```

### Highlight

重点变化项。

```python
@dataclass
class Highlight:
    """重点变化"""
    
    type: str                # 类型: "multi_increase" | "multi_decrease" | "new_overlap" | "exclusive_to_overlap"
    ticker: str              # 股票代码
    company: str             # 公司名称
    fund_count: int          # 涉及基金数
    funds: List[str]         # 涉及基金列表
    description: str         # 描述文本
```

---

## 🔗 依赖关系

### 内部依赖
- `src.utils` - 配置加载、日志记录
- `src.analyzer` - 使用 `ChangeAnalysis` 数据模型

### 外部依赖
- `pandas` - DataFrame 数据处理
- `dataclasses` - 数据类定义
- `typing` - 类型提示
- `logging` - 日志记录

### 被依赖
- `main.py` - 调用 `analyze_all_funds()`
- `src.summary_notifier` - 使用 `SummaryAnalysis` 对象

---

## 🚫 职责边界

### ✅ 负责
- 跨基金重叠股票计算
- 独家持仓识别
- 重点变化检测
- 基金统计信息生成
- 数据结构化组织

### ❌ 不负责
- 数据下载（由 `fetcher` 负责）
- 单基金持仓分析（由 `analyzer` 负责）
- 报告生成（由 `summary_notifier` 负责）
- 图片生成（由 `image_generator` 负责）
- 推送消息（由 `summary_notifier` 负责）

---

## 📝 使用示例

```python
from src.summary_analyzer import SummaryAnalyzer
from src.utils import load_config

# 初始化
config = load_config()
analyzer = SummaryAnalyzer(config)

# 准备数据
all_holdings = {
    'ARKK': arkk_df,
    'ARKW': arkw_df,
    'ARKG': arkg_df,
    'ARKQ': arkq_df,
    'ARKF': arkf_df
}

all_analyses = {
    'ARKK': arkk_analysis,
    'ARKW': arkw_analysis,
    # ...
}

# 执行分析
summary = analyzer.analyze_all_funds(
    all_holdings,
    all_analyses,
    '2025-11-14'
)

if summary:
    print(f"总持仓: {summary.total_holdings}")
    print(f"跨基金重叠: {summary.overlap_count}")
    print(f"重点变化: {len(summary.highlights)} 条")
else:
    print("数据不足，跳过汇总分析")
```

---

## ⚠️ 注意事项

1. **最低要求**: 至少2个成功基金才生成汇总，否则返回 `None`
2. **阈值配置**: 独家持仓权重阈值可通过 `config.yaml` 配置
3. **数据一致性**: 所有基金数据必须是同一日期
4. **性能考虑**: 遍历算法复杂度 O(N×M)，N=股票数，M=基金数，实际运行 <1秒
5. **错误处理**: 内部捕获所有异常，记录日志后返回 `None`

---

## 🧪 测试要点

### 单元测试
- `test_calculate_overlaps()` - 测试重叠股票计算
- `test_identify_exclusives()` - 测试独家持仓识别
- `test_detect_highlights()` - 测试重点变化检测
- `test_analyze_all_funds_success()` - 测试完整流程
- `test_analyze_all_funds_insufficient_data()` - 测试数据不足场景

### 集成测试
- 使用真实 CSV 数据验证汇总结果准确性
- 测试与 `summary_notifier` 的协同工作

---

**契约状态**: ✅ 已实现  
**测试覆盖率**: 85%+  
**最后审核**: 2025-11-14
