# 故障排查指南 (Troubleshooting)

本文档提供常见问题的诊断和解决方案。

---

## 📋 目录

- [安装和配置问题](#安装和配置问题)
- [数据获取问题](#数据获取问题)
- [企业微信推送问题](#企业微信推送问题)
- [Cron 定时任务问题](#cron-定时任务问题)
- [性能和日志问题](#性能和日志问题)

---

## 安装和配置问题

### 1. `ModuleNotFoundError: No module named 'xxx'`

**问题**: 缺少 Python 依赖包

**解决方案**:
```bash
# 安装所有依赖
pip install -r requirements.txt

# 如果使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 2. `ValueError: webhook_url 不能为空`

**问题**: 未配置企业微信 Webhook URL

**解决方案**:
```bash
# 1. 检查 .env 文件是否存在
ls -la .env

# 2. 编辑 .env 文件
vim .env

# 3. 确保包含以下内容
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY

# 4. 测试连接
python3 main.py --test-webhook
```

---

### 3. `FileNotFoundError: config.yaml not found`

**问题**: 配置文件缺失

**解决方案**:
```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 根据需要编辑配置
vim config.yaml
```

---

## 数据获取问题

### 4. `Network error: Failed to fetch data`

**问题**: 网络请求失败（403/404/超时）

**诊断**:
```bash
# 手动测试数据源
curl -I https://raw.githubusercontent.com/thisjustinh/ark-invest-history/master/fund-holdings/ARKK.csv

# 检查网络连接
ping github.com
```

**解决方案**:

#### 方案 1: 配置代理（如果在国内）
```bash
# 临时代理
export https_proxy=http://127.0.0.1:7890
python3 main.py --manual

# 永久代理（添加到 .bashrc 或 .zshrc）
echo 'export https_proxy=http://127.0.0.1:7890' >> ~/.bashrc
source ~/.bashrc
```

#### 方案 2: 使用 GitHub 镜像加速
修改 `src/fetcher.py` 中的 URL:
```python
# 原始
GITHUB_URL_TEMPLATE = "https://raw.githubusercontent.com/..."

# 镜像（如 ghproxy）
GITHUB_URL_TEMPLATE = "https://ghproxy.com/https://raw.githubusercontent.com/..."
```

#### 方案 3: 检查重试配置
编辑 `config.yaml`:
```yaml
retry:
  max_retries: 5           # 增加重试次数
  retry_delays: [2, 4, 8]  # 延长重试间隔
```

---

### 5. `DataFrame 权重异常: 15514%`

**问题**: GitHub CSV 包含历史数据未过滤

**诊断**:
```bash
# 查看下载的 CSV 文件
head -20 data/holdings/ARKK/2025-01-15.csv
```

**解决方案**:

此问题在 v1.0.0 已修复。如果仍出现,检查代码是否包含最新日期过滤逻辑:

```python
# src/fetcher.py 应包含
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    max_date = df['date'].max()
    df = df[df['date'] == max_date].copy()
```

---

### 6. `No data for date 2025-01-20`

**问题**: ARK 官网尚未更新数据（未来日期或周末）

**解决方案**:
- ARK 数据通常在美东时间 19:00 更新（北京时间次日 07:00-08:00）
- 周末和节假日无数据更新
- 建议设置 cron 时间为北京时间 11:00（确保数据已更新）

---

## 企业微信推送问题

### 7. `企业微信推送失败: errcode 93000`

**问题**: IP 地址不在白名单或 Webhook Key 无效

**解决方案**:
```bash
# 1. 检查 Webhook URL 是否正确
cat .env | grep WECHAT_WEBHOOK_URL

# 2. 重新创建群机器人
# - 在企业微信群中删除旧机器人
# - 添加新机器人，获取新 Webhook URL
# - 更新 .env 文件

# 3. 测试连接
python3 main.py --test-webhook
```

---

### 8. `企业微信推送成功，但群里没收到消息`

**问题**: 消息格式错误或被过滤

**诊断**:
```bash
# 查看日志中的推送响应
tail -100 logs/$(date +%Y-%m-%d).log | grep -A5 "企业微信"
```

**解决方案**:
- 检查消息内容是否为空
- 检查 Markdown 格式是否正确
- 尝试发送纯文本测试消息:
  ```bash
  python3 -c "
  from src.notifier import WeChatNotifier
  import os
  from dotenv import load_dotenv
  
  load_dotenv()
  notifier = WeChatNotifier(os.getenv('WECHAT_WEBHOOK_URL'), 3)
  notifier.send_error_alert('测试消息')
  "
  ```

---

### 9. `企业微信推送超时`

**问题**: 网络延迟或企业微信服务异常

**解决方案**:
```bash
# 增加超时时间（编辑 src/notifier.py）
response = requests.post(
    self.webhook_url,
    json=message,
    timeout=30  # 增加到 30 秒
)
```

---

## Cron 定时任务问题

### 10. `Cron 任务不执行`

**诊断**:
```bash
# 1. 检查 cron 是否安装
which crontab

# 2. 查看 crontab 配置
crontab -l

# 3. 检查 cron 日志 (macOS)
log show --predicate 'process == "cron"' --info --last 1h

# 4. 检查系统日志 (Linux)
grep CRON /var/log/syslog
```

**常见原因和解决方案**:

#### 原因 1: Python 路径错误
```bash
# 手动验证 Python 路径
which python3

# 修改 crontab（使用绝对路径）
crontab -e
# 修改为:
0 11 * * 1-5 cd /absolute/path/to/Wood-ARK && /usr/local/bin/python3 main.py
```

#### 原因 2: 环境变量缺失
Cron 不会加载 shell 环境变量,需在 crontab 中显式设置:
```bash
crontab -e
# 在任务前添加:
PATH=/usr/local/bin:/usr/bin:/bin
SHELL=/bin/bash
HOME=/Users/yourusername

0 11 * * 1-5 cd /path/to/Wood-ARK && python3 main.py
```

#### 原因 3: 工作目录错误
```bash
# 确保 crontab 中包含 cd 命令
0 11 * * 1-5 cd /absolute/path/to/Wood-ARK && python3 main.py
```

#### 原因 4: 权限问题
```bash
# 检查脚本和目录权限
chmod +x main.py
chmod -R 755 /path/to/Wood-ARK
```

---

### 11. `Cron 执行了，但没有推送`

**诊断**:
```bash
# 查看日志文件
tail -100 logs/$(date +%Y-%m-%d).log

# 检查推送状态
cat data/cache/push_status.json
```

**可能原因**:
- 今天已推送过（幂等性保护）
- 今天不是工作日
- 数据获取失败

**解决方案**:
```bash
# 强制重新执行
python3 main.py --manual

# 检查推送状态文件
rm data/cache/push_status.json  # 清空状态（谨慎操作）
python3 main.py --manual
```

---

## 性能和日志问题

### 12. `日志文件过大占用磁盘`

**解决方案**:
```bash
# 方案 1: 手动清理（保留 7 天）
./scripts/cleanup_logs.sh 7

# 方案 2: 修改日志保留策略
vim config.yaml
# 修改:
log:
  retention_days: 7  # 改为 7 天

# 方案 3: 添加 logrotate (Linux)
sudo vim /etc/logrotate.d/wood-ark
# 内容:
/path/to/Wood-ARK/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

---

### 13. `程序运行缓慢`

**诊断**:
```bash
# 查看日志中的执行时间
grep "执行时间" logs/$(date +%Y-%m-%d).log

# 使用 Python profiler
python3 -m cProfile -s cumtime main.py --manual
```

**优化建议**:
- 减少监控的 ETF 数量（修改 `config.yaml` 中的 `data.etfs`）
- 检查网络连接速度
- 增加重试延迟（避免频繁重试）

---

### 14. `数据文件占用过多空间`

**解决方案**:
```bash
# 查看数据目录大小
du -sh data/

# 删除旧的持仓数据（保留最近 30 天）
find data/holdings -name "*.csv" -mtime +30 -delete

# 删除旧的报告（保留最近 30 天）
find data/reports -name "*.md" -mtime +30 -delete
```

---

## 调试技巧

### 启用 DEBUG 日志

```yaml
# config.yaml
log:
  level: "DEBUG"  # 修改为 DEBUG
```

### 手动测试单个模块

```bash
# 测试数据获取
python3 -c "
from src.fetcher import DataFetcher
from src.utils import load_config

config = load_config()
fetcher = DataFetcher(config)
df = fetcher.fetch_holdings('ARKK', '2025-01-15')
print(df.head())
"

# 测试持仓分析
python3 -c "
from src.analyzer import Analyzer
import pandas as pd

analyzer = Analyzer(threshold=5.0)
# ... 加载数据并测试
"

# 测试报告生成
python3 -c "
from src.reporter import ReportGenerator
# ... 测试
"
```

---

## 获取帮助

如果以上方案无法解决问题:

1. 查看完整日志: `cat logs/$(date +%Y-%m-%d).log`
2. 检查配置文件: `cat config.yaml`
3. 提交 Issue，附上:
   - 错误信息完整堆栈
   - 日志文件相关片段
   - Python 版本 (`python3 --version`)
   - 操作系统版本

---

**最后更新**: 2025-11-13
