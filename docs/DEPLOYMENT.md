# 部署指南

本文档介绍如何部署 Wood-ARK 系统并实现自动化运行。

---

## 🚀 快速部署（推荐）

### 一键部署脚本

使用提供的部署脚本，3 分钟完成配置：

```bash
# 1. 配置 Webhook
cp .env.example .env
nano .env  # 填写 WECHAT_WEBHOOK_URL

# 2. 运行部署脚本
./scripts/setup_launchd.sh

# 3. 验证安装
launchctl list | grep wood-ark
```

**完成！** 系统将每天 19:00 自动运行。

---

## 📋 手动部署步骤

### 1. 环境准备

**系统要求**:
- macOS 10.14+
- Python 3.9+
- 至少 500MB 可用磁盘空间

**安装依赖**:
```bash
# 克隆项目
git clone <repo_url>
cd Wood-ARK

# 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip3 install -r requirements.txt
```

---

### 2. 配置文件

#### 2.1 企业微信 Webhook

```bash
# 复制模板
cp .env.example .env

# 编辑 .env
nano .env
```

```.env
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
```

**获取 Webhook URL**:
1. 打开企业微信群聊
2. 点击右上角 `···` → 群机器人 → 添加机器人
3. 选择"自定义机器人"
4. 复制 Webhook 地址

#### 2.2 系统配置（可选）

```bash
# 复制模板
cp config.yaml.example config.yaml

# 编辑配置
nano config.yaml
```

**关键配置**:
- `schedule.cron_time`: 执行时间（默认 19:00）
- `data.etfs`: 监控的 ETF 列表
- `analysis.change_threshold`: 显著变化阈值

详细说明见 [配置文档](CONFIGURATION.md)。

---

### 3. 测试运行

#### 3.1 测试 Webhook 连接

```bash
python3 main.py --test-webhook
```

**预期输出**:
```
✅ Webhook 连接正常
测试消息已发送到企业微信
```

#### 3.2 手动执行一次

```bash
python3 main.py --manual
```

**预期输出**:
```
[INFO] 开始执行 ARK 持仓监控...
[1/6] 处理 ARKK...
[2/6] 处理 ARKW...
...
[6/6] 生成汇总报告...
✅ 所有报告已推送
```

**检查企业微信**:
- 应收到 6 条消息（1个汇总 + 5个单基金长图）

---

### 4. 设置定时任务

#### 方法A：使用一键脚本（推荐）

```bash
./scripts/setup_launchd.sh
```

脚本会自动：
1. 创建 Launchd 配置文件
2. 加载定时任务
3. 验证安装

#### 方法B：手动配置 Launchd

**创建配置文件**:

```bash
nano ~/Library/LaunchAgents/com.lucian.wood-ark.plist
```

**内容**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lucian.wood-ark</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/main.py</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>19</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>WorkingDirectory</key>
    <string>/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK</string>
    
    <key>StandardOutPath</key>
    <string>/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/logs/launchd.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/lucian/Documents/个人/Investment/Tools/Wood-ARK/logs/launchd_error.log</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

**⚠️ 注意**:
- 替换所有路径为你的实际项目路径
- `Hour` 设置为北京时间（19 = 晚上7点）

**加载任务**:
```bash
# 加载配置
launchctl load ~/Library/LaunchAgents/com.lucian.wood-ark.plist

# 验证加载
launchctl list | grep wood-ark
```

---

### 5. 验证部署

#### 5.1 检查定时任务

```bash
# 查看任务状态
launchctl list | grep wood-ark

# 预期输出（PID 为0表示未运行中，正常）
-	0	com.lucian.wood-ark
```

#### 5.2 手动触发测试

```bash
# 手动触发定时任务（不等到19:00）
launchctl start com.lucian.wood-ark

# 查看日志
tail -f logs/launchd.log
```

#### 5.3 等待自动运行

第二天 19:00 检查企业微信是否收到推送。

---

## 📊 数据累积策略

### 历史数据来源

**重要说明**:
- ✅ ARKFunds.io API 仅提供当日最新数据
- ❌ GitHub 镜像数据已停止更新（2021-09-08）
- ✅ 系统采用**每日自动累积**策略

### 数据累积时间线

| 天数 | 可用功能 | 说明 |
|------|---------|------|
| 第 1 天 | 持仓表格 | 无历史数据，仅显示当日持仓 |
| 第 2-29 天 | 持仓表格 + 持仓变化 | 可对比前一日变化 |
| 第 30 天 | 上述 + 1个月趋势图 ⭐ | 激活1个月趋势图 |
| 第 31-89 天 | 持仓表格 + 变化 + 1个月趋势 | 趋势图持续更新 |
| 第 90 天 | 上述 + 3个月趋势图 ⭐⭐ | 激活3个月趋势图 |
| 第 91天+ | **完整功能** | 所有功能可用 |

### 快速累积数据（可选）

如果你有其他历史数据源，可手动放置 CSV 文件：

```bash
# 数据格式
data/holdings/ARKK/2025-11-01.csv
data/holdings/ARKK/2025-11-02.csv
...
```

**CSV 格式要求**:
```csv
date,etf_symbol,company,ticker,cusip,shares,market_value,weight
2025-11-01,ARKK,Tesla Inc,TSLA,88160R101,1234567,280000000,10.5
```

---

## 🔄 维护与管理

### 查看日志

```bash
# 主日志
tail -f logs/wood_ark.log

# Launchd 日志
tail -f logs/launchd.log

# 错误日志
tail -f logs/launchd_error.log
```

### 手动补偿缺失数据

电脑关机期间错过的更新可手动补偿：

```bash
# 自动检测缺失日期
python3 main.py --check-missed

# 预期输出
检测到缺失日期: 2025-11-10, 2025-11-11, 2025-11-12
开始补偿...
[1/3] 补偿 2025-11-10...
[2/3] 补偿 2025-11-11...
[3/3] 补偿 2025-11-12...
✅ 补偿完成
```

### 修改配置

```bash
# 修改配置
nano config.yaml

# 测试配置
python3 main.py --manual

# 无需重启定时任务，下次执行自动生效
```

### 卸载定时任务

```bash
# 卸载 Launchd 任务
launchctl unload ~/Library/LaunchAgents/com.lucian.wood-ark.plist

# 删除配置文件
rm ~/Library/LaunchAgents/com.lucian.wood-ark.plist
```

---

## 📦 数据管理

### 磁盘占用估算

| 类型 | 单日大小 | 30天 | 90天 | 1年 |
|------|---------|------|------|-----|
| CSV 数据 | ~50KB | 1.5MB | 4.5MB | 18MB |
| 长图报告 | ~200KB | 6MB | 18MB | 73MB |
| 日志文件 | ~500KB | 15MB | - | - |
| **总计** | ~750KB | ~23MB | ~23MB | ~91MB |

**说明**:
- 日志默认保留 30 天，自动清理
- 长图可选择性保留（需要可永久保留）
- CSV 数据建议永久保留（用于趋势分析）

### 清理数据

```bash
# 清理过期日志（30天前）
python3 scripts/cleanup_logs.py

# 清理过期图片（可选，30天前）
find data/images -name "*.png" -mtime +30 -delete

# 清理所有数据重新开始（谨慎！）
rm -rf data/holdings/*
rm -rf data/images/*
```

---

## 🛠️ 故障排除

### 问题1：定时任务不执行

**症状**: 19:00 没有收到推送

**排查步骤**:
```bash
# 1. 检查任务是否加载
launchctl list | grep wood-ark

# 2. 检查日志
tail -f logs/launchd_error.log

# 3. 手动触发测试
launchctl start com.lucian.wood-ark
```

**常见原因**:
- 电脑休眠/关机
- 路径配置错误
- Python 环境变量未设置

### 问题2：推送失败

**症状**: 日志显示执行成功，但未收到企业微信消息

**排查步骤**:
```bash
# 测试 Webhook
python3 main.py --test-webhook

# 检查配置
cat .env  # 确认 Webhook URL 正确
```

**常见原因**:
- Webhook URL 错误或过期
- 网络代理设置
- 企业微信机器人被删除

### 问题3：数据下载失败

**症状**: 报告为空或显示"数据获取失败"

**排查步骤**:
```bash
# 查看详细日志
tail -50 logs/wood_ark.log

# 测试网络连接
curl https://arkfunds.io/api/v2/etf/arkk
```

**常见原因**:
- 网络故障
- API 临时不可用（重试）
- 防火墙拦截

---

## 📚 进阶配置

### 监控多个环境

如果需要同时监控不同配置（如测试/生产）：

```bash
# 创建多个配置文件
config.prod.yaml
config.test.yaml

# 指定配置运行
CONFIG_FILE=config.test.yaml python3 main.py --manual
```

### 自定义数据源

如果 ARKFunds.io API 不可用，可切换数据源：

修改 `src/fetcher.py`:
```python
# 当前数据源
URL = "https://arkfunds.io/api/v2/etf/{symbol}"

# 备用数据源（需自行实现解析）
URL = "https://your-custom-api.com/{symbol}"
```

---

## ✅ 检查清单

部署完成后，确认以下事项：

- [ ] ✅ Webhook 测试成功
- [ ] ✅ 手动执行成功（收到 6 条消息）
- [ ] ✅ Launchd 任务已加载
- [ ] ✅ 日志文件正常生成
- [ ] ✅ 第二天 19:00 自动收到推送
- [ ] ✅ 数据文件正常保存（`data/holdings/`）
- [ ] ✅ 长图生成正常（`data/images/`）

---

## 🔗 相关文档

- [配置参数说明](CONFIGURATION.md)
- [使用指南](USAGE.md)
- [常见问题](FAQ.md)
- [变更日志](../CHANGELOG.md)

---

**最后更新**: 2025-11-14  
**版本**: v2.0  
**部署方式**: Launchd（macOS）
