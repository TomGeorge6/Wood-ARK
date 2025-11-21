# 综合长图功能快速上手

## 🚀 快速测试

### 1. 生成模拟数据（仅首次测试需要）
```bash
cd /Users/lucian/Documents/个人/Investment/Tools/Wood-ARK

# 为 ARKK 生成 90 天模拟数据
python3 scripts/generate_mock_data.py --etf ARKK --days 90

# 为其他 ETF 生成数据（可选）
python3 scripts/generate_mock_data.py --etf ARKW --days 90
python3 scripts/generate_mock_data.py --etf ARKG --days 90
```

### 2. 测试长图生成
```bash
# 生成 ARKK 的综合长图
python3 scripts/test_comprehensive_image.py

# 查看生成结果
open data/images/ARKK/2025-11-14_comprehensive.png
```

### 3. 完整运行（推送到企业微信）
```bash
# 手动模式（忽略工作日检查）
python3 main.py --manual

# 检查推送结果（登录企业微信查看）
```

## 📊 长图内容说明

### 第一部分：持仓排名表格（Top 15）
```
┌─────────────────────────────────────────────┐
│ 排名 │ 代码 │ 公司名称 │ 持股数 │ 市值 │ 权重 │
├─────────────────────────────────────────────┤
│  1   │ TSLA │ Tesla Inc│ 1.2M  │$280M│10.5%│
│  2   │ ...  │ ...      │ ...   │ ... │ ... │
└─────────────────────────────────────────────┘
```

### 第二部分：基金总市值趋势
```
┌──────────────────┬──────────────────┐
│ 最近 1 个月      │ 最近 3 个月      │
│  - 总市值折线图  │  - 总市值折线图  │
│  - 区域填充      │  - 区域填充      │
├──────────────────┼──────────────────┤
│ 日度变化率 (1m)  │ 日度变化率 (3m)  │
│  - 绿色：涨      │  - 绿色：涨      │
│  - 红色：跌      │  - 红色：跌      │
└──────────────────┴──────────────────┘
```

### 第三部分：Top 10 个股权重趋势
```
┌──────────────────┬──────────────────┐
│ 1 个月趋势       │ 3 个月趋势       │
│  - 10 条折线     │  - 10 条折线     │
│  - 每只股票 1 条 │  - 每只股票 1 条 │
│  - 带图例        │  - 带图例        │
└──────────────────┴──────────────────┘
```

## 🔧 常见问题

### Q1: 提示"历史数据不足"
**原因**：少于 5 天的历史数据  
**解决**：
- 方案 A（推荐）：等待几天，让系统自动累积真实数据
- 方案 B（测试）：运行 `python3 scripts/generate_mock_data.py`

### Q2: 图片太大/太小
**调整**：修改 `src/image_generator.py`
```python
# 第 481 行
total_height = 10 + 16 + 12  # 调整总高度
fig = plt.figure(figsize=(14, total_height))  # 调整宽度
```

### Q3: 企业微信显示不清晰
**原因**：DPI 设置过低  
**调整**：修改 `src/image_generator.py`
```python
# 第 529 行
plt.savefig(image_path, dpi=200)  # 提高 DPI（默认 150）
```

### Q4: 只有 ARKK 有长趋势图
**原因**：其他 ETF 只有 2 天真实数据  
**解决**：
- 等待每日运行，自动累积数据
- 或使用 `generate_mock_data.py` 为其他 ETF 生成模拟数据

## 📈 数据累积时间线

| 天数 | 显示效果 |
|------|----------|
| 1-4 天 | ⚠️ 只显示持仓表格，提示"数据不足" |
| 5-29 天 | ✅ 显示 1 个月视图（使用全部数据） |
| 30-89 天 | ✅ 显示完整 1 个月视图 |
| 90+ 天 | 🎉 显示完整 1 个月 + 3 个月视图 |

## 🎨 自定义配置

### 修改颜色主题
```python
# src/image_generator.py 第 643 行
ax1.plot(..., color='#YOUR_COLOR')  # 修改折线颜色
```

### 修改 Top N 数量
```python
# src/image_generator.py 第 552 行
self._draw_holdings_table(ax_table, holdings, etf_symbol, date, top_n=20)
```

### 修改时间范围
```python
# src/image_generator.py 第 617 行
dates_1m = dates_all[-45:]  # 改为 45 天
dates_3m = dates_all[-120:]  # 改为 120 天
```

## 📞 技术支持

遇到问题？
1. 查看日志：`logs/2025-11-14.log`
2. 查看设计文档：`docs/IMAGE_REPORT_DESIGN.md`
3. 查看变更日志：`CHANGELOG_20251114.md`

---

**更新日期**：2025-11-14  
**版本**：2.0.0
