# Wood-ARK 持仓监控系统

## 📊 项目简介

Wood-ARK 是一个轻量级的本地工具，用于**自动监控 ARK Invest 基金的持仓变化**，并通过企业微信推送每日报告。

- **木头姐** (Cathie Wood) 管理的 ARK 基金是科技创新领域的风向标
- 每日自动下载 5 只 ARK ETF 的持仓数据 (ARKK, ARKW, ARKG, ARKQ, ARKF)
- 智能分析持仓变化（新增、移除、增持、减持）
- 自动生成 Markdown 格式报告并推送到企业微信

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| **自动监控** | 每天上午 11:00 自动执行（周一到周五，可配置） |
| **智能分析** | 识别新增/移除持仓、显著增持/减持（阈值可配置） |
| **企微推送** | Markdown 格式报告，美观易读 |
| **手动补偿** | 支持指定日期查询和缺失数据补偿 |
| **本地存储** | 所有数据保存为 CSV 文件，无需数据库 |
| **容错机制** | 网络重试、单 ETF 失败隔离、推送状态跟踪 |

## 📦 安装

### 1. 环境要求

- **操作系统**: macOS / Linux
- **Python**: 3.9+
- **依赖**: pandas, requests, python-dotenv, PyYAML

### 2. 克隆项目

```bash
git clone <repository-url>
cd Wood-ARK
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入企业微信 Webhook URL
# .env
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
```

**获取 Webhook URL**:
1. 在企业微信群聊中添加 "群机器人"
2. 复制 Webhook 地址
3. 粘贴到 `.env` 文件

### 5. 配置系统参数（可选）

```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 编辑 config.yaml（根据需要调整）
vim config.yaml
```

**关键配置项**:
- `schedule.cron_time`: 定时执行时间（默认 11:00）
- `data.etfs`: 监控的 ETF 列表（默认全部 5 只）
- `analysis.change_threshold`: 显著变化阈值（默认 5%）

### 6. 测试连接

```bash
# 测试企业微信 Webhook
python3 main.py --test-webhook
```

如果成功，企业微信群会收到测试消息。

## 🚀 使用方法

### 自动模式（推荐）

安装 cron 定时任务，每天自动执行：

```bash
# 安装 cron（周一到周五 11:00 自动执行）
./scripts/install_cron.sh

# 验证安装
crontab -l

# 查看日志
tail -f logs/$(date +%Y-%m-%d).log
```

### 手动模式

```bash
# 强制执行今天的任务（忽略工作日检查）
python3 main.py --manual

# 查询指定日期
python3 main.py --date 2025-01-15

# 检查并补偿缺失日期（最近 7 天）
python3 main.py --check-missed

# 只监控特定 ETF
python3 main.py --manual --etf ARKK
```

### 卸载

```bash
# 删除 cron 任务
./scripts/uninstall_cron.sh

# 手动清理日志（保留 30 天）
./scripts/cleanup_logs.sh
```

## 📝 报告示例

推送到企业微信的报告格式：

```markdown
# ARK 持仓变化 (2025-01-15)

## ARKK

### 📊 概览
- 对比日期: 2025-01-14 → 2025-01-15
- 新增持仓: 1 只
- 移除持仓: 1 只
- 显著增持: 1 只
- 显著减持: 1 只

### ✅ 新增持仓
| 股票代码 | 公司名称 | 持股数 | 权重 |
|---------|---------|--------|------|
| PATH | UiPath Inc | 500K | 0.98% |

### ❌ 移除持仓
| 股票代码 | 公司名称 | 之前权重 |
|---------|---------|---------|
| SHOP | Shopify Inc | 1.26% |

### 📈 显著增持 (>5%)
| 股票代码 | 公司名称 | 变化 | 当前权重 |
|---------|---------|------|---------|
| TSLA | Tesla Inc | +20.0% | 11.80% |

### 📉 显著减持 (>5%)
| 股票代码 | 公司名称 | 变化 | 当前权重 |
|---------|---------|------|---------|
| COIN | Coinbase Global Inc | -10.0% | 3.50% |

---
执行时间: 11:05:23 | [完整持仓数据](./data/holdings/ARKK/2025-01-15.csv)
```

## 📂 项目结构

```
Wood-ARK/
├── src/                    # 源代码
│   ├── fetcher.py         # 数据获取
│   ├── analyzer.py        # 持仓分析
│   ├── reporter.py        # 报告生成
│   ├── notifier.py        # 企微推送
│   ├── scheduler.py       # 调度逻辑
│   └── utils.py           # 工具函数
├── tests/                 # 测试代码
├── data/                  # 数据存储
│   ├── holdings/          # CSV 持仓数据
│   ├── reports/           # Markdown 报告
│   └── cache/             # 推送状态缓存
├── logs/                  # 日志文件
├── scripts/               # 部署脚本
│   ├── install_cron.sh    # 安装 cron
│   ├── uninstall_cron.sh  # 卸载 cron
│   └── cleanup_logs.sh    # 清理日志
├── docs/                  # 文档
├── main.py                # 程序入口
├── config.yaml            # 配置文件
├── .env                   # 环境变量（敏感信息）
└── requirements.txt       # 依赖列表
```

## 🔧 配置说明

### .env（环境变量）

```bash
# 必需配置
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
```

### config.yaml（系统配置）

```yaml
schedule:
  enabled: true              # 是否启用定时检查
  cron_time: "11:00"         # 执行时间（北京时间）
  timezone: "Asia/Shanghai"  # 时区

data:
  etfs: ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"]  # 监控的 ETF
  data_dir: "./data"         # 数据目录
  log_dir: "./logs"          # 日志目录

analysis:
  change_threshold: 5.0      # 显著变化阈值（%）

notification:
  webhook_url: "${WECHAT_WEBHOOK_URL}"  # 引用环境变量
  enable_error_alert: true   # 是否发送错误告警

retry:
  max_retries: 3             # 最大重试次数
  retry_delays: [1, 2, 4]    # 重试延迟（秒）

log:
  retention_days: 30         # 日志保留天数
  level: "INFO"              # 日志级别
```

## 🛠️ 常见问题

参考 [docs/TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## 📊 数据来源

- **主数据源**: [thisjustinh/ark-invest-history](https://github.com/thisjustinh/ark-invest-history) (GitHub 镜像)
- **数据特点**: 包含完整历史数据，每日自动同步 ARK 官网
- **选择理由**: ARK 官网存在反爬虫机制，GitHub 镜像更稳定可靠

## 📄 许可证

MIT License

## 🙏 致谢

- [ARK Invest](https://ark-invest.com/) - 数据来源
- [thisjustinh/ark-invest-history](https://github.com/thisjustinh/ark-invest-history) - GitHub 镜像仓库
- 企业微信 - 推送服务

## 📮 联系方式

如有问题或建议，请提交 Issue。

---

**版本**: 1.0.0  
**最后更新**: 2025-11-13
