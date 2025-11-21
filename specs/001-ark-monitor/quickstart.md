# Quick Start Guide: ARK 持仓监控系统

**Version**: 1.0.0  
**Last Updated**: 2025-11-13

---

## 📋 前置要求

- **Python**: 3.9 或更高版本
- **操作系统**: macOS（测试环境）或 Linux
- **网络**: 能访问 ark-funds.com 和企业微信 API
- **企业微信**: 已创建群机器人并获取 Webhook URL

---

## 🚀 安装步骤

### 1. 克隆项目

```bash
git clone <repository_url>
cd Wood-ARK
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# Windows 用户
# venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

**requirements.txt 内容**:
```
pandas>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
PyYAML>=6.0.0
pytest>=7.0.0
```

### 4. 配置环境变量

```bash
# 复制模板文件
cp .env.example .env

# 编辑 .env 文件，填写企业微信 Webhook URL
nano .env
```

**.env 文件示例**:
```bash
# 企业微信 Webhook URL（必填）
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE
```

**获取 Webhook URL 的方法**:
1. 打开企业微信客户端
2. 进入目标群聊
3. 右上角 "..." → 群机器人 → 添加群机器人
4. 复制生成的 Webhook 地址

### 5. 配置系统参数

```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 根据需要调整配置（可选）
nano config.yaml
```

**config.yaml 默认配置**:
```yaml
schedule:
  enabled: true            # 是否启用定时任务
  cron_time: "11:00"       # 执行时间（北京时间）
  timezone: "Asia/Shanghai"

data:
  etfs: ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"]  # 监控的 ETF
  data_dir: "./data"       # 数据存储目录
  log_dir: "./logs"        # 日志存储目录

analysis:
  change_threshold: 5.0    # 显著变化阈值（百分比）

notification:
  webhook_url: "${WECHAT_WEBHOOK_URL}"  # 引用 .env 中的变量
  enable_error_alert: true  # 是否发送错误告警

retry:
  max_retries: 3           # 最大重试次数
  retry_delays: [1, 2, 4]  # 重试延迟（秒）

log:
  retention_days: 30       # 日志保留天数
  level: "INFO"            # 日志级别
```

---

## ✅ 测试安装

### 测试 1: 验证 Webhook 连接

```bash
python main.py --test-webhook
```

**预期输出**:
```
✅ Webhook 连接测试成功
企业微信群机器人已收到测试消息
```

如果失败,检查:
- `.env` 文件中 `WECHAT_WEBHOOK_URL` 是否正确
- 网络是否能访问企业微信 API
- Webhook URL 是否过期（群机器人删除后 URL 失效）

### 测试 2: 手动执行一次

```bash
python main.py --manual
```

**预期输出**:
```
[INFO] 2025-01-15 14:30:00 - 开始执行 ARK 持仓监控任务
[INFO] 2025-01-15 14:30:05 - ARKK 数据下载成功 (42 只股票)
[INFO] 2025-01-15 14:30:06 - ARKW 数据下载成功 (35 只股票)
[INFO] 2025-01-15 14:30:07 - ARKG 数据下载成功 (45 只股票)
[INFO] 2025-01-15 14:30:08 - ARKQ 数据下载成功 (38 只股票)
[INFO] 2025-01-15 14:30:09 - ARKF 数据下载成功 (42 只股票)
[INFO] 2025-01-15 14:30:12 - 报告已推送到企业微信
[INFO] 2025-01-15 14:30:12 - 任务执行完成
```

**企业微信群效果**:
群机器人会推送一条 Markdown 消息,包含当日持仓变化摘要。

---

## 📅 安装定时任务

### macOS / Linux (cron)

**方法 1: 使用自动安装脚本**

```bash
./scripts/install_cron.sh
```

**方法 2: 手动配置**

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天北京时间 11:00 执行，周一到周五）
0 11 * * 1-5 cd /Users/lucian/Documents/个人/Investment/Tools/Wood-ARK && /usr/local/bin/python3 main.py >> logs/cron.log 2>&1
```

**注意事项**:
- ✅ 使用绝对路径（`which python3` 查看）
- ✅ 使用 `cd` 切换到项目目录
- ✅ 重定向输出到日志文件

**验证安装**:

```bash
crontab -l
# 应该看到刚添加的定时任务
```

---

## 🔧 常用命令

### 手动执行（忽略工作日检查）

```bash
python main.py --manual
```

### 查询指定日期数据

```bash
python main.py --date 2025-01-15
```

### 检测并补偿缺失日期

```bash
python main.py --check-missed
```

**用途**: 电脑关机导致错过推送时,运行此命令补偿缺失数据

**示例输出**:
```
[INFO] 检测到 3 个缺失日期: 2025-01-13, 2025-01-14, 2025-01-15
[INFO] 正在处理 2025-01-13...
[INFO] 2025-01-13 报告已推送
[INFO] 正在处理 2025-01-14...
[INFO] 2025-01-14 报告已推送
[INFO] 正在处理 2025-01-15...
[INFO] 2025-01-15 报告已推送
[INFO] 补偿任务完成
```

### 测试 Webhook 连接

```bash
python main.py --test-webhook
```

---

## 📂 目录结构

安装完成后,项目目录结构如下:

```
Wood-ARK/
├── config.yaml              # 配置文件
├── .env                     # 环境变量（不提交 Git）
├── main.py                  # 程序入口
├── requirements.txt         # Python 依赖
│
├── src/                     # 核心模块
│   ├── fetcher.py
│   ├── analyzer.py
│   ├── reporter.py
│   ├── notifier.py
│   ├── scheduler.py
│   └── utils.py
│
├── data/                    # 数据存储（自动创建）
│   ├── holdings/
│   │   ├── ARKK/
│   │   │   └── 2025-01-15.csv
│   │   └── ...
│   ├── reports/
│   └── cache/
│       └── push_status.json
│
├── logs/                    # 日志文件（自动创建）
│   └── 2025-01-15.log
│
└── scripts/                 # 辅助脚本
    └── install_cron.sh
```

---

## 🐛 常见问题排查

### 问题 1: Webhook 推送失败

**症状**: 日志显示 "推送失败: invalid webhook url"

**解决方案**:
1. 检查 `.env` 文件中 `WECHAT_WEBHOOK_URL` 是否正确
2. 确认 URL 以 `https://qyapi.weixin.qq.com` 开头
3. 测试 Webhook: `python main.py --test-webhook`
4. 如果群机器人被删除,需重新添加并更新 URL

### 问题 2: cron 任务未执行

**症状**: 定时任务没有在预定时间运行

**排查步骤**:
```bash
# 1. 检查 cron 任务是否添加
crontab -l

# 2. 检查 cron 日志
tail -f logs/cron.log

# 3. 检查系统日志
tail -f /var/log/system.log | grep cron  # macOS

# 4. 手动运行完整命令测试
cd /path/to/Wood-ARK && /usr/local/bin/python3 main.py
```

**常见原因**:
- 电脑处于休眠状态（cron 不会唤醒电脑）
- Python 路径不正确（使用 `which python3` 查看绝对路径）
- 环境变量未加载（cron 环境与交互式 shell 不同）

### 问题 3: CSV 下载失败

**症状**: 日志显示 "ARKK 数据下载失败: Timeout"

**解决方案**:
1. 检查网络连接
2. 访问 https://ark-funds.com 确认官网可访问
3. 检查是否需要配置代理
4. 系统会自动重试 3 次,通常网络恢复后可成功

### 问题 4: 首次运行无对比分析

**症状**: 报告显示 "首次运行,明日开始对比分析"

**说明**: 这是正常行为。首次运行时没有历史数据,系统仅下载当日数据。第二天运行时会对比前后两日变化。

**加速方案**（可选）:
1. 克隆历史数据仓库: `git clone https://github.com/thisjustinh/ark-invest-history`
2. 复制前一日的 CSV 到 `data/holdings/{ETF}/`
3. 重新运行: `python main.py --manual`

---

## 📚 下一步

- ✅ **定期检查**: 每周运行 `python main.py --check-missed` 补偿缺失
- ✅ **调整阈值**: 编辑 `config.yaml` 修改 `change_threshold`
- ✅ **查看日志**: 定期检查 `logs/` 目录下的日志文件
- ✅ **更新依赖**: `pip install --upgrade -r requirements.txt`

---

## 🆘 获取帮助

- **项目文档**: `docs/README.md`
- **故障排查**: `docs/TROUBLESHOOTING.md`
- **变更日志**: `docs/CHANGELOG.md`
- **GitHub Issues**: <repository_url>/issues

---

**Quick Start Status**: ✅ Complete | **Last Updated**: 2025-11-13
