# Wood-ARK: ARK ETF 持仓监控工具

自动监控 ARK Invest 旗下 ETF 的每日持仓变化，生成可视化报告并推送到企业微信。

## ✨ 主要功能

### 🆕 **ARK 全系列基金汇总报告**（v2.0）

**一眼看穿 Wood 姐的整体投资布局！**

- 📊 **统计摘要**：5只基金全景对比
- 🔥 **核心持仓**：跨基金重叠股票 Top 10
- 📈 **各基金Top 5**：快速对比持仓重点
- 💎 **独家持仓**：各基金特色股票
- 🎯 **重点变化**：多基金同时增持/减持

**详细说明**：[汇总功能指南](docs/SUMMARY_FEATURE_GUIDE.md)

---

### 📊 **单基金持仓监控**

- 📊 **自动获取数据**：每日从真实API下载最新持仓数据
- 📈 **综合长图报告**：生成包含持仓表格、基金趋势、个股分析的长图
- 📱 **企业微信推送**：每天推送 **6条消息**（1个汇总 + 5个单基金）
- 🗄️ **智能数据管理**：自动清理过期数据，节省存储空间
- 📅 **定时执行**：支持 Cron 定时任务

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2. 配置企业微信 Webhook

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填写 Webhook 地址
nano .env
```

```.env
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
```

### 3. 首次运行

```bash
# 测试 Webhook 连接
python3 main.py --test-webhook

# 手动执行一次（生成报告并推送）
python3 main.py --manual
```

### 4. 设置自动化（推荐）

```bash
# 一键部署定时任务（每天 19:00 执行）
./scripts/setup_launchd.sh
```

**完成！** 系统将每天自动运行，无需人工干预。

---

## 📖 详细文档

- **[使用指南](docs/USAGE.md)** - 所有命令行参数说明
- **[配置说明](docs/CONFIGURATION.md)** - 详细配置参数
- **[部署指南](docs/DEPLOYMENT.md)** - 自动化部署与数据策略
- **[常见问题](docs/FAQ.md)** - 故障排除与答疑
- **[变更日志](CHANGELOG.md)** - 版本更新记录

## 📊 数据说明

### ⚠️ 重要限制

**ARKFunds.io API 只能获取当日最新数据，不支持历史日期查询**

- ❌ **无法补齐缺失数据**：电脑关机期间的数据永久缺失
- ❌ **无法获取历史数据**：API 只返回当天最新数据
- ✅ **必须每天运行**：唯一获取历史数据的方式是每天定时运行，自然累积
- ✅ **数据准确性优先**：不做任何补齐操作，避免数据错乱

### 历史数据策略

系统采用**每日自动累积**策略：
- ✅ 每天运行自动保存当日数据
- ✅ 30天后：1个月趋势图自动激活
- ✅ 90天后：3个月趋势图自动激活

**重要**: 
- ⚠️ ARKFunds.io API 只能获取当日最新数据
- ⚠️ GitHub 镜像数据已过时（停止在 2021-09）
- ✅ 建议每天定时运行，自然累积历史数据

详细说明请参考 [部署指南](docs/DEPLOYMENT.md#数据累积策略)

## 📈 长图报告

### 报告内容

综合长图包含三大部分：

1. **持仓排名表格**（Top 15）
   - 排名、股票代码、公司名称
   - 持股数、市值、权重

2. **基金总市值趋势**（1 个月 + 3 个月）
   - 总市值折线图 + 日度变化率
   - 左右对比（1m vs 3m）

3. **Top 10 个股权重趋势**（1 个月 + 3 个月）
   - 10 只股票的权重变化
   - 多条折线对比

### 示例图表

![综合报告长图示例](docs/example_comprehensive_image.png)

## 🛠️ 常用命令

```bash
# 手动执行（忽略工作日检查）
python3 main.py --manual

# 指定日期
python3 main.py --date 2025-11-14 --manual

# 只处理指定 ETF
python3 main.py --etf ARKK --manual

# 检查数据完整性
python3 scripts/check_data_integrity.py

# 测试 Webhook
python3 main.py --test-webhook
```

**更多参数**: 查看 [使用指南](docs/USAGE.md)

## 📁 项目结构

```
Wood-ARK/
├── main.py              # 主程序入口
├── config.yaml          # 配置文件
├── .env                 # 环境变量（需手动创建）
├── requirements.txt     # Python 依赖
├── src/                 # 核心模块
├── data/                # 数据目录
├── logs/                # 日志文件
├── scripts/             # 辅助脚本
├── tests/               # 测试文件
├── docs/                # 文档
└── specs/               # 功能规格（Spec-Kit）
```

---

## ⚠️ 数据来源说明

本项目使用 **ARK Invest 官方真实数据**，通过以下API获取：

- **ARKFunds.io API** (推荐)
  - 开源项目：https://github.com/frefrik/ark-invest-api
  - 数据来源：ARK Invest 官方
  - 更新频率：每个交易日
  - 可靠性：⭐⭐⭐⭐⭐

---

## 📞 支持

- **使用问题**: 查看 [常见问题](docs/FAQ.md)
- **Bug 反馈**: 查看 [故障排除](docs/TROUBLESHOOTING.md)
- **功能建议**: 提交 Issue

---

**最后更新**: 2025-11-14  
**版本**: 2.0.0
