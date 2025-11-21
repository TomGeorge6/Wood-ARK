# Wood-ARK 修复总结 (2025-11-14 最终版)

## 核心问题

### 问题根源
**CSV 文件保存时缺少逗号分隔符**

### 表现症状
1. **历史数据显示为0**：趋势图无法读取历史CSV文件（因为缺少分隔符导致解析失败）
2. **Top 10 趋势图只显示部分线条**：因为数据读取失败，只有部分数据可见

## 修复方案

### 1. CSV保存修复（核心修复）
**文件**: `src/fetcher.py`

**问题**: `to_csv()` 方法未显式指定分隔符
```python
# 修复前
df.to_csv(file_path, index=False, encoding='utf-8')

# 修复后
df.to_csv(file_path, index=False, encoding='utf-8', sep=',')
```

### 2. CSV读取修复
**文件**: `src/fetcher.py`

**问题**: GitHub历史数据使用空格分隔符，需智能检测
```python
# 修复：智能检测分隔符类型
text_sample = response.text[:1000]

if '\t' in text_sample:
    sep = '\t'
elif ',' in text_sample.split('\n')[0]:
    sep = ','
else:
    sep = r'\s+'
```

### 3. Top 3 改为 Top 10
**文件**: `src/summary_notifier.py`

```python
# 修复前
top_holdings = summary['top_holdings'][:3]
lines.append(f"Top 3: {top3_str}")

# 修复后
top_holdings = summary['top_holdings'][:10]
lines.append(f"Top 10: {top10_str}")
```

### 4. 权重趋势改为持股数趋势
**文件**: `src/image_generator.py`

**修改方法**:
- `_draw_top10_trend()`: Top 10 个股趋势
- `_draw_new_stocks_trend()`: 新增股票趋势

**关键变更**:
```python
# 修复前
stock_weights_1m = {ticker: [] for ticker in current_top10}
weight = row.iloc[0]['weight'] if len(row) > 0 else 0
ax1.set_ylabel('权重 (%)', fontsize=10)

# 修复后
stock_shares_1m = {ticker: [] for ticker in current_top10}
shares = row.iloc[0]['shares'] if len(row) > 0 else 0
ax1.set_ylabel('持股数', fontsize=10)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'
))
```

## 测试验证

### 验证CSV格式
```bash
# 检查CSV文件是否有逗号分隔符
head -1 data/holdings/ARKK/2025-11-14.csv
# 应输出: date,etf_symbol,company,ticker,cusip,shares,market_value,weight
```

### 重新下载历史数据
```bash
# 清空旧数据
rm -rf data/holdings/* data/images/*

# 下载最近90天历史数据
python3 main.py --backfill --days 90

# 运行测试
python3 main.py --manual
```

### 验证结果
- [ ] CSV文件有逗号分隔符
- [ ] 汇总报告显示 Top 10
- [ ] 趋势图Y轴显示"持股数"（格式为 1.2M）
- [ ] 历史数据趋势正常显示

## 注意事项

1. **GitHub历史数据限制**: GitHub数据只更新到 2021-09-08，不适合长期使用
2. **建议**: 启用 `config.yaml` 中的 `auto_download_history: true`，让系统每天自动保存数据
3. **CSV格式标准**: 所有CSV文件必须使用逗号分隔符（`,`），不能使用空格或Tab

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `src/fetcher.py` | CSV保存/读取修复 |
| `src/summary_notifier.py` | Top 3 → Top 10 |
| `src/image_generator.py` | 权重趋势 → 持股数趋势 |

---

**修复完成时间**: 2025-11-14  
**修复版本**: v3（最终版）
