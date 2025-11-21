# Module Contract: ReportGenerator

**Module**: `src/reporter.py`  
**Purpose**: 负责生成 Markdown 格式的持仓变化报告

---

## Class Definition

```python
class ReportGenerator:
    """持仓变化报告生成器"""
    
    def __init__(self, max_length: int = 4096):
        """初始化 ReportGenerator
        
        Args:
            max_length: 报告最大字符长度（企业微信限制 4096）
        """
        self.max_length = max_length
        self.logger = logging.getLogger(__name__)
```

---

## Public Methods

### 1. generate_markdown()

**签名**:

```python
def generate_markdown(
    self,
    analyses: List[ChangeAnalysis],
    execution_time: str
) -> str:
    """生成完整的 Markdown 报告
    
    Args:
        analyses: 所有 ETF 的分析结果列表
        execution_time: 执行时间（如 '11:05:23'）
        
    Returns:
        Markdown 格式字符串，字符长度 ≤ max_length
        
    Report Structure:
        ## 🚀 ARK 持仓日报 (YYYY-MM-DD)
        
        ### 📊 整体概况
        - 监控 ETF: 5 只
        - 有变化: 3 只
        - 执行时间: 11:05:23
        
        ### 🔥 ARKK - 创新科技 ETF
        **✅ 新增持仓** (1):
        - HOOD Robinhood Markets Inc (0.5%)
        
        **❌ 移除持仓** (1):
        - SPOT Spotify Technology SA (之前 1.2%)
        
        **📈 显著增持** (>5%):
        - TSLA Tesla Inc: +15.9% (8.2% → 9.15%)
        
        **📉 显著减持** (>5%):
        - COIN Coinbase Global Inc: -8.4% (4.84% → 4.44%)
        
        **📋 前 5 大持仓**:
        1. TSLA Tesla Inc (9.15%)
        2. COIN Coinbase Global Inc (4.44%)
        ...
        
    Character Limit Handling:
        - 如报告超过 max_length，自动截断
        - 优先保留：整体概况 + ARKK 详情
        - 截断位置添加提示："\n\n⚠️ 报告过长，详情查看日志: logs/YYYY-MM-DD.log"
    """
    pass
```

**Example Usage**:

```python
reporter = ReportGenerator(max_length=4096)

analyses = [
    analyzer.compare_holdings(...),  # ARKK
    analyzer.compare_holdings(...),  # ARKW
    # ...
]

markdown = reporter.generate_markdown(analyses, '11:05:23')

print(len(markdown))  # 确保 ≤ 4096
print(markdown)
```

---

### 2. save_report()

**签名**:

```python
def save_report(
    self,
    content: str,
    etf_symbol: str,
    date: str,
    failed: bool = False
) -> None:
    """保存报告到本地文件
    
    Args:
        content: Markdown 内容
        etf_symbol: ETF 代码（用于分目录存储）
        date: 日期字符串 YYYY-MM-DD
        failed: 是否为推送失败的报告（失败报告保存到 failed/ 子目录）
        
    Side Effects:
        - 成功报告保存到: {data_dir}/reports/{etf_symbol}/{date}.md
        - 失败报告保存到: {data_dir}/reports/failed/{date}.md
        - 自动创建目录（如不存在）
        
    Implementation Details:
        1. 构造文件路径
        2. 检查目录是否存在，不存在则创建
        3. 写入文件（UTF-8 编码）
        4. 记录日志
    """
    pass
```

**Example Usage**:

```python
reporter = ReportGenerator()

# 保存成功推送的报告
reporter.save_report(markdown, 'ARKK', '2025-01-15', failed=False)
# 结果: ./data/reports/ARKK/2025-01-15.md

# 保存推送失败的报告
reporter.save_report(markdown, 'ARKK', '2025-01-15', failed=True)
# 结果: ./data/reports/failed/2025-01-15.md
```

---

## Private Methods

### _generate_summary_section()

```python
def _generate_summary_section(
    self,
    analyses: List[ChangeAnalysis],
    execution_time: str
) -> str:
    """生成整体概况部分
    
    Returns:
        ### 📊 整体概况
        - 监控 ETF: 5 只
        - 有变化: 3 只
        - 执行时间: 11:05:23
    """
    changed_count = sum(
        1 for a in analyses 
        if a.added or a.removed or a.increased or a.decreased
    )
    
    lines = [
        "### 📊 整体概况",
        f"- 监控 ETF: {len(analyses)} 只",
        f"- 有变化: {changed_count} 只",
        f"- 执行时间: {execution_time}",
        ""
    ]
    return "\n".join(lines)
```

### _generate_etf_section()

```python
def _generate_etf_section(self, analysis: ChangeAnalysis) -> str:
    """生成单个 ETF 的详细变化部分
    
    Args:
        analysis: 单个 ETF 的分析结果
        
    Returns:
        ### 🔥 ARKK - 创新科技 ETF
        **✅ 新增持仓** (1):
        - HOOD Robinhood Markets Inc (0.5%)
        ...
    """
    lines = [f"### 🔥 {analysis.etf_symbol}"]
    
    # 新增
    if analysis.added:
        lines.append(f"**✅ 新增持仓** ({len(analysis.added)}):")
        for record in analysis.added:
            lines.append(
                f"- **{record['ticker']}** {record['company']} "
                f"({record['weight']:.2f}%)"
            )
        lines.append("")
    
    # 移除
    if analysis.removed:
        lines.append(f"**❌ 移除持仓** ({len(analysis.removed)}):")
        for record in analysis.removed:
            lines.append(
                f"- **{record['ticker']}** {record['company']} "
                f"(之前 {record['weight']:.2f}%)"
            )
        lines.append("")
    
    # 增持
    if analysis.increased:
        lines.append(f"**📈 显著增持** (>5%):")
        for change in analysis.increased:
            lines.append(
                f"- **{change['ticker']}** {change['company']}: "
                f"+{change['shares_change_pct']:.1f}% "
                f"({change['previous_weight']:.2f}% → {change['current_weight']:.2f}%)"
            )
        lines.append("")
    
    # 减持
    if analysis.decreased:
        lines.append(f"**📉 显著减持** (>5%):")
        for change in analysis.decreased:
            lines.append(
                f"- **{change['ticker']}** {change['company']}: "
                f"{change['shares_change_pct']:.1f}% "
                f"({change['previous_weight']:.2f}% → {change['current_weight']:.2f}%)"
            )
        lines.append("")
    
    # 前 5 大持仓
    if analysis.top5_holdings:
        lines.append("**📋 前 5 大持仓**:")
        for i, holding in enumerate(analysis.top5_holdings, 1):
            lines.append(
                f"{i}. **{holding['ticker']}** {holding['company']} "
                f"({holding['weight']:.2f}%)"
            )
        lines.append("")
    
    return "\n".join(lines)
```

### _truncate_if_needed()

```python
def _truncate_if_needed(self, content: str, date: str) -> str:
    """如果内容超长，自动截断并添加提示
    
    Args:
        content: 原始 Markdown 内容
        date: 日期（用于日志文件路径提示）
        
    Returns:
        截断后的内容（如需要）
        
    Strategy:
        1. 如果 len(content) <= max_length，直接返回
        2. 如果超长：
           a. 保留整体概况部分
           b. 保留 ARKK 详情（最重要的 ETF）
           c. 其他 ETF 仅显示摘要（"有 X 只新增、Y 只减持"）
           d. 末尾添加："\n\n⚠️ 报告过长，详情查看日志: logs/{date}.log"
    """
    if len(content) <= self.max_length:
        return content
    
    # 截断逻辑
    warning = f"\n\n⚠️ 报告过长，详情查看日志: logs/{date}.log"
    target_length = self.max_length - len(warning)
    
    truncated = content[:target_length]
    
    # 确保在完整行结束处截断
    last_newline = truncated.rfind('\n')
    if last_newline > 0:
        truncated = truncated[:last_newline]
    
    return truncated + warning
```

### _format_no_change_message()

```python
def _format_no_change_message(self, analysis: ChangeAnalysis) -> str:
    """格式化无变化消息
    
    Returns:
        **ℹ️ 今日无重大变化**
        
        **📋 前 5 大持仓**:
        1. TSLA Tesla Inc (9.15%)
        ...
    """
    lines = [
        "**ℹ️ 今日无重大变化**",
        ""
    ]
    
    # 仍然显示前 5 大持仓
    if analysis.top5_holdings:
        lines.append("**📋 前 5 大持仓**:")
        for i, holding in enumerate(analysis.top5_holdings, 1):
            lines.append(
                f"{i}. **{holding['ticker']}** {holding['company']} "
                f"({holding['weight']:.2f}%)"
            )
    
    return "\n".join(lines)
```

---

## Testing

```python
# tests/test_reporter.py

def test_generate_markdown_basic():
    """测试基本报告生成"""
    analysis = ChangeAnalysis(
        etf_symbol='ARKK',
        current_date='2025-01-15',
        previous_date='2025-01-14',
        added=[{'ticker': 'HOOD', 'company': 'Robinhood', 'weight': 0.5}],
        removed=[],
        increased=[],
        decreased=[],
        top5_holdings=[{'ticker': 'TSLA', 'company': 'Tesla', 'weight': 9.15}],
        total_holdings_count=42
    )
    
    reporter = ReportGenerator()
    markdown = reporter.generate_markdown([analysis], '11:05:23')
    
    assert '🚀 ARK 持仓日报' in markdown
    assert 'ARKK' in markdown
    assert 'HOOD' in markdown
    assert '11:05:23' in markdown

def test_generate_markdown_truncate():
    """测试超长报告自动截断"""
    # 构造超长 analysis（很多股票变化）
    large_analysis = ChangeAnalysis(...)  # 省略
    
    reporter = ReportGenerator(max_length=100)  # 设置很小的限制
    markdown = reporter.generate_markdown([large_analysis], '11:05:23')
    
    assert len(markdown) <= 100
    assert '⚠️ 报告过长' in markdown

def test_save_report_creates_directory(tmp_path):
    """测试自动创建目录"""
    reporter = ReportGenerator()
    reporter.config = Config(data=DataConfig(data_dir=str(tmp_path)))
    
    reporter.save_report("# Test", 'ARKK', '2025-01-15', failed=False)
    
    assert (tmp_path / 'reports' / 'ARKK' / '2025-01-15.md').exists()

def test_save_report_failed_location(tmp_path):
    """测试失败报告保存位置"""
    reporter = ReportGenerator()
    reporter.config = Config(data=DataConfig(data_dir=str(tmp_path)))
    
    reporter.save_report("# Test", 'ARKK', '2025-01-15', failed=True)
    
    assert (tmp_path / 'reports' / 'failed' / '2025-01-15.md').exists()
```

---

## Markdown Formatting Rules

### Emoji Usage

| Emoji | 用途 | 示例 |
|-------|------|------|
| 🚀 | 标题 | `## 🚀 ARK 持仓日报` |
| 📊 | 整体概况 | `### 📊 整体概况` |
| 🔥 | ETF 名称 | `### 🔥 ARKK` |
| ✅ | 新增持仓 | `**✅ 新增持仓**` |
| ❌ | 移除持仓 | `**❌ 移除持仓**` |
| 📈 | 增持 | `**📈 显著增持**` |
| 📉 | 减持 | `**📉 显著减持**` |
| 📋 | 前 5 持仓 | `**📋 前 5 大持仓**` |
| ℹ️ | 无变化 | `**ℹ️ 今日无重大变化**` |
| ⚠️ | 警告/截断 | `⚠️ 报告过长` |

### Number Formatting

```python
# 权重：保留 2 位小数
f"{weight:.2f}%"  # 9.15%

# 变化百分比：保留 1 位小数，正数加 + 号
f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"  # +15.9% 或 -8.4%

# 持股数：使用 M/K 缩写（可选，目前直接显示百分比）
# 3245678 → 3.2M
```

### Text Escaping

企业微信 Markdown 不需要转义特殊字符（如 `*`, `_`, `[`），但需注意：
- ✅ 公司名称可能包含 `&`（如 `AT&T`）→ 保持原样
- ✅ 股票代码不包含特殊字符 → 无需处理

---

## Performance Considerations

- **生成时间**: 单个报告 <2 秒（5 只 ETF）
- **内存占用**: ~10KB（Markdown 字符串）
- **字符统计**: 平均 2500 字符（正常情况），最大 4096

---

**Contract Status**: ✅ Defined | **Last Updated**: 2025-11-13
