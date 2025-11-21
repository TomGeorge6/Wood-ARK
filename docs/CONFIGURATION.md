# 配置参数详细说明

本文档详细介绍 Wood-ARK 的所有配置参数。

---

## 📁 配置文件

系统使用**两个配置文件**：

1. **`config.yaml`** - 非敏感配置（版本控制）
2. **`.env`** - 敏感配置（不提交到 Git）

---

## 🔐 .env 环境变量

### WECHAT_WEBHOOK_URL

企业微信群机器人 Webhook 地址。

**类型**: String（必需）  
**示例**:
```bash
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

**获取方法**:
1. 打开企业微信群聊
2. 右上角 `···` → 群机器人 → 添加机器人
3. 复制 Webhook 地址

**⚠️ 注意**:
- 必须以 `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=` 开头
- 不要泄露此地址（有安全风险）
- 如需更换，删除旧机器人并创建新机器人

---

## ⚙️ config.yaml 参数

### 1. schedule - 定时任务配置

```yaml
schedule:
  enabled: true          # 是否启用定时任务
  cron_time: "19:00"     # 执行时间（24小时制）
  timezone: "Asia/Shanghai"  # 时区
```

#### enabled
**类型**: Boolean  
**默认值**: `true`  
**说明**: 控制是否启用定时任务。设为 `false` 时仅支持手动执行。

#### cron_time
**类型**: String (HH:MM 格式)  
**默认值**: `"19:00"`  
**说明**: 每天执行时间（北京时间）。

**推荐时间**:
- `19:00` - 美东时间数据已更新（推荐）
- `11:00` - 早上查看前一日数据

#### timezone
**类型**: String  
**默认值**: `"Asia/Shanghai"`  
**说明**: 时区设置，影响日期计算。

**可选值**:
- `Asia/Shanghai` - 北京时间（UTC+8）
- `America/New_York` - 美东时间（UTC-5/-4）
- `UTC` - 世界标准时间

---

### 2. data - 数据源配置

```yaml
data:
  etfs: ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"]
  data_dir: "./data"
  log_dir: "./logs"
  images_dir: "./data/images"
```

#### etfs
**类型**: Array[String]  
**默认值**: `["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"]`  
**说明**: 监控的 ETF 列表。

**可选值**:
- `ARKK` - ARK Innovation ETF（旗舰基金）⭐
- `ARKW` - ARK Next Generation Internet ETF
- `ARKG` - ARK Genomic Revolution ETF
- `ARKQ` - ARK Autonomous Tech & Robotics ETF
- `ARKF` - ARK Fintech Innovation ETF

**示例**（仅监控 ARKK 和 ARKW）:
```yaml
etfs: ["ARKK", "ARKW"]
```

#### data_dir
**类型**: String  
**默认值**: `"./data"`  
**说明**: 数据存储根目录。

**目录结构**:
```
data/
├── holdings/     # CSV 持仓数据
├── images/       # 长图报告
└── cache/        # 状态缓存
```

#### log_dir
**类型**: String  
**默认值**: `"./logs"`  
**说明**: 日志文件目录。

#### images_dir
**类型**: String  
**默认值**: `"./data/images"`  
**说明**: 趋势图存储目录。

---

### 3. analysis - 分析参数

```yaml
analysis:
  change_threshold: 5.0      # 显著变化阈值（百分比）
  exclusive_threshold: 3.0   # 独家持仓权重阈值（百分比）
```

#### change_threshold
**类型**: Float  
**默认值**: `5.0`  
**说明**: 持仓变化阈值（百分比）。低于此值的变化不显示在报告中。

**推荐值**:
- `3.0` - 激进投资者（捕捉更多变化）
- `5.0` - 普通投资者（推荐）
- `10.0` - 保守投资者（仅看重大调整）

**示例**:
- 某股票持股数从 100万 增加到 106万（+6%）
  - `threshold = 5.0` → ✅ 显示
  - `threshold = 10.0` → ❌ 不显示

#### exclusive_threshold
**类型**: Float  
**默认值**: `3.0`  
**说明**: 独家持仓权重阈值。仅在单一基金中且权重 ≥ 此值的股票显示为"独家持仓"。

---

### 4. notification - 通知配置

```yaml
notification:
  webhook_url: "${WECHAT_WEBHOOK_URL}"  # 从 .env 读取
  enable_error_alert: true               # 错误告警开关
  skip_summary: false                    # 跳过汇总报告
```

#### webhook_url
**类型**: String  
**默认值**: `"${WECHAT_WEBHOOK_URL}"`  
**说明**: 自动从 `.env` 文件读取，无需修改。

#### enable_error_alert
**类型**: Boolean  
**默认值**: `true`  
**说明**: 是否在发生严重错误时推送告警到企业微信。

#### skip_summary
**类型**: Boolean  
**默认值**: `false`  
**说明**: 是否跳过汇总报告。设为 `true` 时仅推送单基金报告。

---

### 5. retry - 重试策略

```yaml
retry:
  max_retries: 3          # 最大重试次数
  retry_delays: [1, 2, 4] # 重试延迟（秒）
```

#### max_retries
**类型**: Integer  
**默认值**: `3`  
**说明**: 网络请求失败时的最大重试次数。

#### retry_delays
**类型**: Array[Integer]  
**默认值**: `[1, 2, 4]`  
**说明**: 每次重试的延迟时间（秒），采用指数退避策略。

**工作原理**:
1. 第1次失败 → 等待 1 秒后重试
2. 第2次失败 → 等待 2 秒后重试
3. 第3次失败 → 等待 4 秒后重试
4. 仍失败 → 记录错误并继续

---

### 6. log - 日志配置

```yaml
log:
  retention_days: 30      # 日志保留天数
  level: "INFO"           # 日志级别
```

#### retention_days
**类型**: Integer  
**默认值**: `30`  
**说明**: 日志文件保留天数。超过此天数的日志自动删除。

**磁盘占用估算**:
- 每天约 500KB 日志
- 30 天 ≈ 15MB
- 90 天 ≈ 45MB

#### level
**类型**: String  
**默认值**: `"INFO"`  
**说明**: 日志级别。

**可选值**:
- `DEBUG` - 详细调试信息（开发时使用）
- `INFO` - 一般信息（推荐）
- `WARNING` - 警告信息
- `ERROR` - 仅错误信息

---

### 7. trend - 趋势图配置

```yaml
trend:
  period_1m_days: 30      # 1个月天数
  period_3m_days: 90      # 3个月天数
```

#### period_1m_days
**类型**: Integer  
**默认值**: `30`  
**说明**: 1个月趋势图的天数。历史数据达到此天数后激活。

#### period_3m_days
**类型**: Integer  
**默认值**: `90`  
**说明**: 3个月趋势图的天数。历史数据达到此天数后激活。

---

## 📋 完整配置示例

### config.yaml（默认配置）

```yaml
# 定时任务配置
schedule:
  enabled: true
  cron_time: "19:00"
  timezone: "Asia/Shanghai"

# 数据源配置
data:
  etfs: ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"]
  data_dir: "./data"
  log_dir: "./logs"
  images_dir: "./data/images"

# 分析参数
analysis:
  change_threshold: 5.0
  exclusive_threshold: 3.0

# 通知配置
notification:
  webhook_url: "${WECHAT_WEBHOOK_URL}"
  enable_error_alert: true
  skip_summary: false

# 重试策略
retry:
  max_retries: 3
  retry_delays: [1, 2, 4]

# 日志配置
log:
  retention_days: 30
  level: "INFO"

# 趋势图配置
trend:
  period_1m_days: 30
  period_3m_days: 90
```

### .env（必需配置）

```bash
# 企业微信 Webhook URL（必填）
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE
```

---

## 🔄 配置热更新

系统支持**配置热更新**：

- ✅ 修改 `config.yaml` 后，下次执行自动生效
- ✅ 修改 `.env` 后，下次执行自动生效
- ❌ 无需重启程序或定时任务

**验证配置**:
```bash
python3 main.py --test-webhook
```

---

## ❓ 常见问题

### Q1: 修改配置后立即生效吗？

**A**: 下次执行时生效。如果定时任务已在运行中，需等本次执行完成。

### Q2: 可以只监控 ARKK 一只基金吗？

**A**: 可以，修改 `config.yaml`:
```yaml
data:
  etfs: ["ARKK"]
```

**注意**: 汇总报告最少需要 2 个基金，单基金会跳过汇总。

### Q3: Webhook 地址泄露了怎么办？

**A**: 
1. 企业微信删除旧机器人
2. 创建新机器人获取新 URL
3. 更新 `.env` 文件

### Q4: 可以同时推送到多个群吗？

**A**: 当前版本不支持。需要推送多个群，请运行多个实例（不同配置文件）。

---

**最后更新**: 2025-11-14  
**版本**: v2.0
