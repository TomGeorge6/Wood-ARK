# 数据管理说明

## 📊 数据存储结构

```
data/
├── holdings/           # 持仓数据
│   ├── ARKK/
│   │   ├── 2025-08-18.csv
│   │   ├── 2025-08-19.csv
│   │   └── ...
│   ├── ARKW/
│   ├── ARKG/
│   ├── ARKQ/
│   └── ARKF/
├── images/             # 生成的图表
│   ├── ARKK/
│   │   └── 2025-11-14_comprehensive.png
│   └── ...
├── reports/            # Markdown 报告
│   ├── ARKK/
│   │   └── 2025-11-14.md
│   └── ...
└── pushed_status.json  # 推送状态记录
```

## 🗄️ 历史数据管理

### 数据获取策略

由于 GitHub 镜像数据已过时（最后更新 2021-09-08），系统采用以下策略：

1. **每日自动累积**：每次运行时自动下载并保存当天数据
2. **首次初始化**：可选择生成模拟历史数据（用于测试图表功能）
3. **真实数据优先**：建议运行 7-14 天后使用真实累积数据

### 初始化历史数据（可选）

如果需要立即查看趋势图（用于测试或演示），可以生成模拟历史数据：

```bash
# 为所有 ETF 生成 90 天模拟数据
cd /Users/lucian/Documents/个人/Investment/Tools/Wood-ARK

python3 scripts/generate_mock_data.py --etf ARKK --days 90
python3 scripts/generate_mock_data.py --etf ARKW --days 90
python3 scripts/generate_mock_data.py --etf ARKG --days 90
python3 scripts/generate_mock_data.py --etf ARKQ --days 90
python3 scripts/generate_mock_data.py --etf ARKF --days 90
```

**注意**：
- ⚠️ 这是基于当前数据生成的模拟数据，仅用于测试
- ✅ 真实数据会通过每日运行自然累积
- 🎯 建议运行 7-14 天后删除模拟数据，使用真实数据

## 🧹 自动清理过期数据

### 配置说明

在 `config.yaml` 中配置数据保留策略：

```yaml
data:
  retention_days: 90  # 保留最近 90 天的数据（默认 3 个月）
```

### 清理逻辑

每次运行 `main.py` 时，系统会自动：

1. **计算截止日期**：当前日期 - `retention_days`
2. **扫描数据目录**：遍历所有 ETF 的持仓数据
3. **删除过期文件**：删除早于截止日期的 CSV 文件
4. **记录日志**：输出删除统计信息

### 示例日志

```
2025-11-14 11:25:40 - src.fetcher - INFO - 开始清理过期数据（保留 90 天）
2025-11-14 11:25:40 - src.fetcher - INFO - 删除早于 2025-08-16 的数据
2025-11-14 11:25:40 - src.fetcher - INFO - ✅ ARKK: 删除 22 个过期文件
2025-11-14 11:25:40 - src.fetcher - INFO - 清理完成: 共删除 22 个过期文件
```

### 自定义保留时长

根据需求调整保留天数：

| 保留时长 | retention_days | 说明 |
|---------|----------------|------|
| 1 个月 | 30 | 仅保留最近 1 个月数据 |
| 2 个月 | 60 | 适合查看短期趋势 |
| **3 个月（推荐）** | **90** | 平衡存储空间和数据完整性 |
| 6 个月 | 180 | 适合长期趋势分析 |
| 1 年 | 365 | 需要较大存储空间 |

## 💾 存储空间估算

### 单个 CSV 文件

- **文件大小**：约 4-5 KB
- **持仓数量**：约 40-50 只股票
- **数据列**：8 列（日期、ETF、公司、代码、持股数、市值、权重等）

### 存储空间计算

| 保留时长 | 单个 ETF | 5 个 ETF | 说明 |
|---------|---------|---------|------|
| 30 天 | ~120 KB | ~600 KB | 1 个月数据 |
| **90 天** | **~360 KB** | **~1.8 MB** | **3 个月数据（推荐）** |
| 180 天 | ~720 KB | ~3.6 MB | 6 个月数据 |
| 365 天 | ~1.5 MB | ~7.5 MB | 1 年数据 |

**结论**：即使保留 1 年数据，5 个 ETF 总共仅需约 7.5 MB 存储空间。

## 📈 数据累积时间线

| 运行天数 | 数据状况 | 图表效果 |
|---------|---------|----------|
| 1-4 天 | 数据不足 | ⚠️ 只显示持仓表格，提示"历史数据不足" |
| 5-29 天 | 开始累积 | ✅ 显示 1 个月视图（使用全部数据） |
| 30-89 天 | 逐渐完整 | ✅ 显示完整 1 个月视图 |
| **90+ 天** | **数据完整** | **🎉 显示完整 1 个月 + 3 个月视图** |

## 🔧 手动管理数据

### 查看数据文件

```bash
# 查看 ARKK 的所有数据文件
ls -lh data/holdings/ARKK/

# 统计文件数量
ls data/holdings/ARKK/*.csv | wc -l

# 查看最早和最晚的文件
ls data/holdings/ARKK/*.csv | head -1
ls data/holdings/ARKK/*.csv | tail -1
```

### 手动清理数据

```bash
# 删除早于指定日期的数据（示例：2025-08-01）
find data/holdings/ARKK/ -name "2025-0[1-7]-*.csv" -delete

# 删除所有数据（重新开始）
rm -rf data/holdings/*
rm -rf data/images/*
rm -rf data/reports/*
```

### 备份数据

```bash
# 备份所有数据
tar -czf ark_data_backup_$(date +%Y%m%d).tar.gz data/

# 恢复备份
tar -xzf ark_data_backup_20251114.tar.gz
```

## 🚨 注意事项

### 数据完整性

- ✅ 已保存的历史数据**不会被覆盖**（符合不可变原则）
- ✅ 清理功能只删除过期文件，不影响保留期内的数据
- ⚠️ 删除操作**不可恢复**，建议定期备份重要数据

### 磁盘空间监控

虽然数据文件很小，但仍建议监控磁盘空间：

```bash
# 查看数据目录占用空间
du -sh data/

# 查看各 ETF 占用空间
du -sh data/holdings/*
```

### 日志清理

日志文件也会占用空间，系统会自动清理：

```yaml
log:
  retention_days: 30  # 日志保留天数
```

## 📞 常见问题

### Q1: 如何禁用自动清理？

设置 `retention_days` 为一个很大的值（如 3650 = 10 年）：

```yaml
data:
  retention_days: 3650
```

### Q2: 清理后如何恢复数据？

清理操作不可恢复，建议：
1. 定期备份数据（使用 `tar` 命令）
2. 或者增加 `retention_days` 值

### Q3: 可以只清理部分 ETF 的数据吗？

目前自动清理会应用于所有 ETF。如需单独管理，请手动删除文件。

### Q4: 数据文件损坏怎么办？

删除损坏的文件，系统会在下次运行时重新下载：

```bash
rm data/holdings/ARKK/2025-11-14.csv
python3 main.py --manual --etf ARKK
```

---

**最后更新**：2025-11-14  
**版本**：2.0.0
