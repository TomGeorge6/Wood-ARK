# 模块契约：ImageGenerator

**模块名称**: `src/image_generator.py`  
**职责**: 生成趋势图和长图报告  
**版本**: v2.0  
**最后更新**: 2025-11-14

---

## 📋 模块概述

`ImageGenerator` 负责绘制所有趋势图表并拼接成长图。

**核心功能**:
- 绘制基金市值趋势图（1个月 + 3个月）
- 绘制 Top 10 个股持股数趋势图
- 绘制持仓变化柱状图
- 生成单基金综合长图
- 生成汇总报告长图
- 图片拼接与保存

---

## 🔌 公共接口

### 类定义

```python
class ImageGenerator:
    """趋势图和长图生成器"""
    
    def __init__(self, config: Config):
        """初始化图片生成器
        
        Args:
            config: 系统配置对象
        """
```

---

### 方法1：generate_comprehensive_image

**功能**: 生成单基金综合长图

**签名**:
```python
def generate_comprehensive_image(
    self,
    etf_symbol: str,
    current_date: str,
    holdings: pd.DataFrame,
    analysis: ChangeAnalysis
) -> Optional[str]
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `etf_symbol` | `str` | ETF 代码（如 "ARKK"） |
| `current_date` | `str` | 当前日期（YYYY-MM-DD） |
| `holdings` | `pd.DataFrame` | 当日持仓数据 |
| `analysis` | `ChangeAnalysis` | 持仓变化分析结果 |

**返回值**:
- **类型**: `Optional[str]`
- **说明**: 长图文件路径，失败则返回 `None`

**输出路径**:
```
data/images/{ETF}/{YYYY-MM-DD}_comprehensive.png
```

**长图结构**:
1. **Part 1**: 基金市值趋势（1个月 + 3个月，数据足够时）
2. **Part 2**: Top 10 个股持股数趋势（1个月 + 3个月）
3. **Part 3**: 新增持仓股票趋势
4. **Part 4**: 持仓变化柱状图（显著增持/减持）
5. **Part 5**: 完整持仓表格

---

### 方法2：generate_summary_image

**功能**: 生成汇总报告长图

**签名**:
```python
def generate_summary_image(
    self,
    summary: SummaryAnalysis,
    current_date: str,
    all_holdings: Dict[str, pd.DataFrame]
) -> Optional[str]
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `summary` | `SummaryAnalysis` | 汇总分析结果 |
| `current_date` | `str` | 当前日期 |
| `all_holdings` | `Dict[str, pd.DataFrame]` | 所有基金持仓数据 |

**返回值**:
- **类型**: `Optional[str]`
- **说明**: 汇总长图文件路径

**输出路径**:
```
data/images/SUMMARY/{YYYY-MM-DD}_summary.png
```

**长图结构**:
1. **Part 1**: 统计摘要（5只基金对比表格）
2. **Part 2**: 跨基金重叠 Top 10 + 趋势图
3. **Part 3**: 各基金 Top 5 持仓
4. **Part 4**: 独家持仓亮点
5. **Part 5**: 今日重点变化

---

### 方法3：_draw_fund_trend（私有）

**功能**: 绘制基金市值趋势图

**签名**:
```python
def _draw_fund_trend(
    self,
    etf_symbol: str,
    days: int = 30
) -> Optional[Image.Image]
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `etf_symbol` | `str` | - | ETF 代码 |
| `days` | `int` | `30` | 天数（30 或 90） |

**返回值**:
- **类型**: `Optional[Image.Image]`
- **说明**: PIL Image 对象，数据不足则返回 `None`

**图表元素**:
- X 轴：日期（MM-DD）
- Y 轴：基金总市值（格式化为 M/B 单位）
- 标题："{ETF} 基金市值趋势 ({days}天)"
- 网格线：浅灰色
- 曲线颜色：蓝色

---

### 方法4：_draw_top10_trend（私有）

**功能**: 绘制 Top 10 个股持股数趋势图

**签名**:
```python
def _draw_top10_trend(
    self,
    etf_symbol: str,
    top10_tickers: List[str],
    days: int = 30
) -> Optional[Image.Image]
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `etf_symbol` | `str` | - | ETF 代码 |
| `top10_tickers` | `List[str]` | - | Top 10 股票代码列表 |
| `days` | `int` | `30` | 天数 |

**返回值**:
- **类型**: `Optional[Image.Image]`
- **说明**: PIL Image 对象

**图表元素**:
- X 轴：日期（MM-DD）
- Y 轴：持股数（格式化为 M/K 单位）⭐
- 标题："{ETF} Top 10 个股持股数趋势 ({days}天)"
- 多条曲线（不同颜色）
- 图例：股票代码

**Y 轴格式化**:
```python
# 示例
1,234,567 → "1.2M"
345,000   → "345K"
12,500    → "12.5K"
```

---

### 方法5：_draw_change_bar（私有）

**功能**: 绘制持仓变化柱状图

**签名**:
```python
def _draw_change_bar(
    self,
    analysis: ChangeAnalysis
) -> Optional[Image.Image]
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `analysis` | `ChangeAnalysis` | 持仓变化分析 |

**返回值**:
- **类型**: `Optional[Image.Image]`
- **说明**: PIL Image 对象

**图表元素**:
- X 轴：股票代码
- Y 轴：变化百分比（%）
- 颜色：
  - 绿色：增持
  - 红色：减持
- 标题："持仓变化（显著增持/减持）"
- 显示数量：最多 15 只股票

---

### 方法6：_stitch_images（私有）

**功能**: 拼接多个图片为长图

**签名**:
```python
def _stitch_images(
    self,
    images: List[Image.Image],
    spacing: int = 20
) -> Image.Image
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `images` | `List[Image.Image]` | - | 图片列表 |
| `spacing` | `int` | `20` | 图片间距（像素） |

**返回值**:
- **类型**: `Image.Image`
- **说明**: 拼接后的长图

**拼接规则**:
- 垂直拼接（从上到下）
- 宽度：取所有图片最大宽度
- 高度：所有图片高度之和 + 间距
- 背景色：白色

---

## 📦 配置参数

### 图表尺寸

```python
# 单个图表默认尺寸
CHART_WIDTH = 1200   # 像素
CHART_HEIGHT = 600   # 像素
DPI = 100            # 分辨率
```

### 字体设置

```python
# 中文字体（macOS）
FONT_PATH = "/System/Library/Fonts/PingFang.ttc"

# 字体大小
TITLE_SIZE = 16
LABEL_SIZE = 12
TICK_SIZE = 10
LEGEND_SIZE = 10
```

### 颜色方案

```python
# 曲线颜色（循环使用）
COLORS = [
    '#1f77b4',  # 蓝色
    '#ff7f0e',  # 橙色
    '#2ca02c',  # 绿色
    '#d62728',  # 红色
    '#9467bd',  # 紫色
    # ... 更多颜色
]

# 柱状图颜色
BAR_COLOR_INCREASE = '#2ca02c'  # 绿色（增持）
BAR_COLOR_DECREASE = '#d62728'  # 红色（减持）
```

---

## 🔗 依赖关系

### 内部依赖
- `src.utils` - 配置加载、日志记录
- `src.analyzer` - 使用 `ChangeAnalysis` 数据模型
- `src.summary_analyzer` - 使用 `SummaryAnalysis` 数据模型

### 外部依赖
- `matplotlib` - 图表绘制
- `Pillow (PIL)` - 图片拼接
- `pandas` - 数据处理
- `numpy` - 数值计算
- `logging` - 日志记录

### 被依赖
- `main.py` - 调用 `generate_comprehensive_image()`
- `src.summary_notifier` - 调用 `generate_summary_image()`

---

## 🚫 职责边界

### ✅ 负责
- 所有趋势图绘制
- 柱状图绘制
- 表格渲染（可选）
- 图片拼接
- 图片保存
- Y 轴格式化（M/K 单位）

### ❌ 不负责
- 数据分析计算（由 `analyzer` 和 `summary_analyzer` 负责）
- 历史数据加载（由 `fetcher` 负责）
- 图片推送（由 `notifier` 和 `summary_notifier` 负责）
- 文件路径管理（由 `utils` 负责）

---

## 📝 使用示例

```python
from src.image_generator import ImageGenerator
from src.utils import load_config

# 初始化
config = load_config()
generator = ImageGenerator(config)

# 生成单基金长图
image_path = generator.generate_comprehensive_image(
    etf_symbol='ARKK',
    current_date='2025-11-14',
    holdings=arkk_df,
    analysis=arkk_analysis
)

if image_path:
    logger.info(f"✅ 长图已保存: {image_path}")
else:
    logger.warning("⚠️ 长图生成失败（历史数据不足）")
```

---

## ⚠️ 注意事项

1. **历史数据要求**:
   - 1个月趋势图：需要 ≥30 天历史数据
   - 3个月趋势图：需要 ≥90 天历史数据
   - 数据不足时跳过对应图表

2. **图片大小限制**:
   - 企业微信限制单张图片 ≤ 20MB
   - 如果长图过大，需优化分辨率或拆分

3. **中文字体**:
   - macOS 使用 `PingFang.ttc`
   - Linux 需安装中文字体（如 `WenQuanYi`）

4. **性能优化**:
   - 趋势图绘制耗时约 2-5 秒/张
   - 长图拼接耗时约 1 秒
   - 总耗时 <30 秒（5个基金 + 1个汇总）

5. **错误处理**:
   - 图表绘制失败不中断程序
   - 返回 `None` 并记录错误日志
   - 调用方可选择跳过图片推送

---

## 🧪 测试要点

### 单元测试
- `test_draw_fund_trend()` - 测试基金趋势图绘制
- `test_draw_top10_trend()` - 测试 Top 10 趋势图
- `test_draw_change_bar()` - 测试柱状图绘制
- `test_stitch_images()` - 测试图片拼接
- `test_format_y_axis()` - 测试 Y 轴格式化（M/K 单位）

### 集成测试
- 使用真实历史数据生成完整长图
- 验证图片大小 <20MB
- 验证中文显示正常

---

## 🎨 图表设计规范

### 标题格式

```python
"{ETF} 基金市值趋势 (30天)"
"{ETF} Top 10 个股持股数趋势 (90天)"
"持仓变化（显著增持/减持）"
```

### 坐标轴标签

```python
# X 轴
"日期"  # 中文

# Y 轴
"总市值"       # 基金趋势图
"持股数"       # 个股趋势图
"变化百分比 (%)" # 柱状图
```

### 图例位置

```python
# matplotlib 配置
ax.legend(loc='best')  # 自动选择最佳位置
```

---

**契约状态**: ✅ 已实现  
**测试覆盖率**: 75%+  
**最后审核**: 2025-11-14
