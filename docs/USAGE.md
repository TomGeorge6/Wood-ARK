# 使用指南

本文档详细说明 Wood-ARK 的所有命令行参数和使用方式。

---

## 命令行参数

### 基本语法

```bash
python3 main.py [选项]
```

### 可用参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `--manual` | flag | 手动模式：强制执行，忽略工作日检查 | False |
| `--etf` | string | 指定单个 ETF 代码（ARKK/ARKW/ARKG/ARKQ/ARKF） | 所有ETF |
| `--date` | string | 指定日期（YYYY-MM-DD 格式） | 今天 |
| `--test-webhook` | flag | 测试企业微信 Webhook 连接 | False |
| `--check-missed` | flag | 检查缺失数据（仅查看，无法补齐）| False |
| `--backfill` | flag | **[已废弃]** 补充历史数据模式 | False |
| `--days` | int | **[已废弃]** 指定下载天数 | 90 |
| `--skip-summary` | flag | 跳过汇总报告，只生成单基金报告 | False |
| `--skip-notification` | flag | 跳过企业微信推送（仅生成报告） | False |

---

## 使用场景

### 1. 自动模式（定时任务）

**场景**: 通过 Launchd/Cron 每天自动执行

```bash
python3 main.py
```

**行为**:
- ✅ 自动检测工作日（周一到周五）
- ✅ 周末/节假日自动跳过
- ✅ 下载所有5个ETF的最新数据
- ✅ 生成汇总报告 + 5个单基金长图
- ✅ 推送6条企业微信消息

**日志**:
```
2025-11-14 19:00:01 - INFO - 今天是工作日，开始执行任务...
2025-11-14 19:00:05 - INFO - ✅ ARKK 数据下载成功
2025-11-14 19:00:10 - INFO - ✅ 汇总报告推送成功
```

---

### 2. 手动模式（强制执行）

**场景**: 立即执行，忽略工作日检查

```bash
python3 main.py --manual
```

**用途**:
- 🔧 调试测试
- 🔧 补充缺失的某一天数据
- 🔧 周末手动运行

**行为**:
- ✅ 忽略工作日检测
- ✅ 立即下载最新数据并推送

---

### 3. 指定单个 ETF

**场景**: 只处理某一个基金（节省时间）

```bash
# 只处理 ARKK
python3 main.py --etf ARKK --manual

# 只处理 ARKW
python3 main.py --etf ARKW --manual
```

**行为**:
- ✅ 只下载指定 ETF 数据
- ✅ 只生成该 ETF 的长图报告
- ⚠️ 不生成汇总报告（需要所有ETF数据）

---

### 4. 指定日期

**场景**: 获取历史某一天的数据

```bash
# 获取 2025-11-10 的数据
python3 main.py --date 2025-11-10 --manual
```

**注意**:
- ⚠️ ARKFunds.io API **只能获取当日最新数据**
- ⚠️ 历史日期会尝试从 GitHub 镜像下载（但数据可能过时）
- ✅ 建议每天定时运行，自然累积历史数据

---

### 5. 补充历史数据

**场景**: 首次安装或数据缺失时，批量下载历史数据

```bash
# 下载最近 90 天的历史数据
python3 main.py --backfill --days 90
```

**行为**:
- ✅ 从 GitHub 镜像下载历史 CSV 文件
- ✅ 按日期分组保存到 `data/holdings/{ETF}/{YYYY-MM-DD}.csv`
- ⚠️ GitHub 数据停止在 2021-09-08（已过时）
- ✅ 适合初始化或补充旧数据

**输出示例**:
```
开始下载 ARKK 最近 90 天的历史数据
从 GitHub 下载历史数据: https://raw.githubusercontent.com/.../ARKK.csv
历史数据时间范围: 2021-08-01 至 2021-09-08
✅ ARKK 历史数据下载完成: 新增 28 个文件
```

---

### 6. 测试 Webhook

**场景**: 验证企业微信 Webhook 配置是否正确

```bash
python3 main.py --test-webhook
```

**行为**:
- ✅ 发送测试消息到企业微信
- ✅ 显示连接状态

**输出示例**:
```
测试企业微信 Webhook 连接...
✅ Webhook 连接成功！
测试消息已发送，请检查企业微信群。
```

---

### 7. 检查缺失数据（仅查看）

**场景**: 查看最近是否有数据缺失

```bash
python3 main.py --check-missed
```

**行为**:
- ✅ 扫描最近 7 天的数据文件
- ✅ 列出缺失的工作日日期
- ⚠️ **仅查看，无法补齐**（API 限制）

**输出示例**:
```
检查最近 7 天的数据完整性...

⚠️  发现缺失数据:
  ARKK: 2025-11-11, 2025-11-12
  ARKW: 2025-11-11, 2025-11-12, 2025-11-13

💡 提示：
   由于 ARKFunds.io API 只能获取当日数据，无法补齐历史缺失数据。
   建议每天定时运行，自然累积数据。
```

**重要说明**：
- ❌ 无法自动补齐缺失数据（API 限制）
- ❌ 电脑关机期间的数据永久缺失
- ✅ 唯一避免缺失的方式：每天定时运行

---

### 8. 跳过汇总报告

**场景**: 只生成单基金长图，不生成汇总报告

```bash
python3 main.py --skip-summary --manual
```

**用途**:
- 🔧 调试单基金功能
- 🔧 节省时间

---

### 9. 跳过推送（仅生成报告）

**场景**: 生成报告文件和图片，但不推送到企业微信

```bash
python3 main.py --skip-notification --manual
```

**用途**:
- 🔧 本地测试
- 🔧 避免打扰群成员

**行为**:
- ✅ 下载数据
- ✅ 生成 Markdown 报告
- ✅ 生成长图 PNG 文件
- ❌ 不推送到企业微信

---

## 组合使用

### 场景1: 调试单个 ETF，不推送

```bash
python3 main.py --etf ARKK --skip-notification --manual
```

### 场景2: 获取指定日期的 ARKW 数据

```bash
python3 main.py --etf ARKW --date 2025-11-10 --manual
```

### 场景3: 补充历史数据后立即运行测试

```bash
# 1. 补充历史数据
python3 main.py --backfill --days 30

# 2. 运行测试（不推送）
python3 main.py --skip-notification --manual
```

---

## 数据文件位置

### 持仓数据

```
data/holdings/
├── ARKK/
│   ├── 2025-11-10.csv
│   ├── 2025-11-11.csv
│   └── 2025-11-14.csv
├── ARKW/
├── ARKG/
├── ARKQ/
└── ARKF/
```

### 报告文件

```
data/reports/
├── ARKK/
│   ├── 2025-11-14.md
│   └── 2025-11-14.png
├── summary/
│   └── 2025-11-14.md
└── ...
```

### 图片文件

```
data/images/
├── ARKK_2025-11-14.png
├── ARKW_2025-11-14.png
└── summary_2025-11-14.png
```

---

## 日志文件

### 应用日志

```
logs/wood_ark.log
```

**查看最新日志**:
```bash
tail -50 logs/wood_ark.log
```

**实时监控**:
```bash
tail -f logs/wood_ark.log
```

### Launchd 日志

```
logs/launchd.log         # 标准输出
logs/launchd_error.log   # 错误输出
```

---

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 一般错误（数据下载失败、文件读写错误等） |
| 2 | 配置错误（环境变量未设置等） |
| 3 | 网络错误（API 无法访问） |

---

## 常见问题

### Q1: 如何查看某一天的历史数据？

**A**: 直接查看 CSV 文件
```bash
cat data/holdings/ARKK/2025-11-10.csv
```

或使用 pandas:
```python
import pandas as pd
df = pd.read_csv('data/holdings/ARKK/2025-11-10.csv')
print(df.head())
```

### Q2: 如何重新生成某一天的报告？

**A**: 
```bash
# 如果数据文件已存在，只需重新运行
python3 main.py --date 2025-11-10 --skip-notification --manual
```

### Q3: 如何清空所有数据重新开始？

**A**:
```bash
# 备份（可选）
mv data data_backup

# 清空数据
rm -rf data/holdings/* data/reports/* data/images/*

# 重新下载
python3 main.py --manual
```

---

## 性能参考

| 操作 | 耗时 | 网络流量 |
|------|------|---------|
| 下载单个 ETF | ~3秒 | ~50KB |
| 下载所有5个 ETF | ~15秒 | ~250KB |
| 生成单个长图 | ~5秒 | - |
| 生成汇总报告 | ~3秒 | - |
| 推送企业微信（单条） | ~1秒 | ~10KB |
| **完整流程** | **~30秒** | **~300KB** |

---

## 下一步

- 📖 [配置说明](CONFIGURATION.md) - 详细配置参数
- 🚀 [部署指南](DEPLOYMENT.md) - 自动化部署
- ❓ [常见问题](FAQ.md) - 故障排除

---

**最后更新**: 2025-11-14  
**版本**: 2.0.0
