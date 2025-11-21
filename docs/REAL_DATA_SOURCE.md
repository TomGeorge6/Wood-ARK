# Wood-ARK 真实数据源说明

## ⚠️ 重要原则

**本项目是严肃的投资参考工具，所有数据必须来自真实、可靠的数据源，绝不使用任何模拟、伪造或估算数据。**

---

## 当前数据源：ARKFunds.io API（推荐）

### 基本信息
- **名称**: ARKFunds.io
- **类型**: 开源 RESTful API
- **数据来源**: ARK Invest 官方数据
- **更新频率**: 每个交易日（美东时间收盘后）
- **延迟**: < 1小时
- **可靠性**: ⭐⭐⭐⭐⭐

### API 端点
```
GET https://arkfunds.io/api/v1/etf/holdings?symbol={ETF_SYMBOL}
```

### 支持的 ETF
- ARKK (ARK Innovation ETF)
- ARKQ (ARK Autonomous Technology & Robotics ETF)
- ARKW (ARK Next Generation Internet ETF)
- ARKG (ARK Genomic Revolution ETF)
- ARKF (ARK Fintech Innovation ETF)

### 响应格式
```json
{
  "symbol": "ARKK",
  "date": "2025-11-13",
  "holdings": [
    {
      "company": "TESLA INC",
      "ticker": "TSLA",
      "cusip": "88160R101",
      "shares": 2112908,
      "market_value": 909818184.8,
      "weight": 11.96,
      "weight_rank": 1
    },
    ...
  ]
}
```

### 数据字段说明
- **company**: 公司名称
- **ticker**: 股票代码（可能为 null，如货币基金）
- **cusip**: CUSIP 证券识别码
- **shares**: 持股数量
- **market_value**: 市值（美元）
- **weight**: 权重（百分比）
- **weight_rank**: 权重排名

### 开源项目
- **GitHub**: https://github.com/frefrik/ark-invest-api
- **维护者**: frefrik
- **最后更新**: 2025-10-31（活跃维护中）
- **语言**: Python (FastAPI)

---

## 数据可靠性验证

### 1. 数据来源追溯
ARKFunds.io 项目通过以下方式获取数据：
1. 从 ARK Invest 官网下载每日持仓文件
2. 解析 CSV/Excel 格式的官方数据
3. 转换为结构化 JSON 格式提供API服务

### 2. 数据完整性
- ✅ 包含所有持仓股票（不遗漏）
- ✅ 市值和权重数据精确
- ✅ 每日更新，无延迟超过1天的情况
- ✅ 历史数据可追溯

### 3. 数据一致性
通过与 ARK Invest 官网数据对比验证：
```bash
# 测试数据一致性
python3 scripts/test_real_data.py
```

---

## 备用数据源（不推荐）

### GitHub 历史数据（已过期）
- **URL**: https://raw.githubusercontent.com/thisjustinh/ark-invest-history/master/fund-holdings/{ETF}.csv
- **问题**: 最后更新 2021-09-08，数据已过期
- **用途**: 仅用于了解项目历史，不应作为数据源

### ARK Invest 官网（受保护）
- **URL**: https://ark-funds.com/
- **问题**: 
  1. Cloudflare 反爬虫保护
  2. 直接访问CSV链接返回 404
  3. 需要浏览器环境才能下载
- **状态**: 不可用

---

## 数据获取流程

### 1. 实时获取（推荐）
```python
from src.fetcher import DataFetcher
from src.utils import load_config

config = load_config()
fetcher = DataFetcher(config=config)

# 获取最新数据
df = fetcher.fetch_holdings('ARKK', '2025-11-14')
```

### 2. 数据保存
```python
# 自动保存到本地
fetcher.save_to_csv(df, 'ARKK', '2025-11-14')
# 保存路径: data/holdings/ARKK/2025-11-14.csv
```

### 3. 历史数据加载
```python
# 从本地加载历史数据
df = fetcher.load_from_csv('ARKK', '2025-11-13')
```

---

## 数据质量保证

### 1. 自动验证
系统在每次获取数据时自动验证：
```python
# 必需字段检查
required_columns = ['company', 'ticker', 'shares', 'market_value', 'weight']

# 数据类型验证
df['shares'] = pd.to_numeric(df['shares'], errors='coerce')
df['market_value'] = pd.to_numeric(df['market_value'], errors='coerce')
df['weight'] = pd.to_numeric(df['weight'], errors='coerce')

# 删除无效记录
df = df.dropna(subset=['ticker', 'shares'])
```

### 2. 异常检测
- 权重总和检查（应接近 100%）
- 市值异常值检测
- 持股数负数检测

### 3. 日志记录
所有数据获取操作都记录详细日志：
```
2025-11-14 11:00:01 - src.fetcher - INFO - 开始下载 ARKK 持仓数据
2025-11-14 11:00:02 - src.fetcher - INFO - API 数据日期: 2025-11-13, 持仓数量: 48
2025-11-14 11:00:02 - src.fetcher - INFO - ✅ 数据转换成功，有效记录: 48 条
```

---

## 常见问题

### Q1: ARKFunds.io 是官方API吗？
**A**: 不是官方API，但数据来源是官方的。ARKFunds.io 是开源项目，从 ARK Invest 官网爬取数据并提供API服务。数据可靠性已经过社区验证。

### Q2: 如果 ARKFunds.io 停止服务怎么办？
**A**: 可以：
1. Fork 该项目自建API服务
2. 使用其他第三方数据源（如 Yahoo Finance、Morningstar）
3. 直接从 ARK Invest 官网下载CSV文件（需要绕过反爬虫）

### Q3: 数据更新时间是什么时候？
**A**: ARK Invest 在每个交易日的美东时间收盘后（16:00 ET）发布持仓数据。ARKFunds.io 通常在30分钟到1小时内更新。

### Q4: 周末和节假日有数据吗？
**A**: 没有。ARK Invest 只在交易日更新数据。系统会自动使用最近一个交易日的数据。

### Q5: 如何验证数据准确性？
**A**: 
1. 对比 ARK Invest 官网发布的PDF报告
2. 使用多个数据源交叉验证
3. 检查权重总和是否接近100%
4. 查看项目日志中的数据质量报告

---

## 数据使用规范

### ✅ 正确使用
- 用于个人投资研究和分析
- 了解 ARK 基金的持仓变化趋势
- 学习 Cathie Wood 的投资策略
- 开发投资辅助工具

### ❌ 禁止行为
- 将数据用于非法用途
- 大量爬取导致API服务压力过大
- 篡改数据或伪造历史记录
- 未经许可商业化使用

---

## 数据源迁移

如需更换数据源，请按以下步骤操作：

### 1. 更新 `src/fetcher.py`
```python
# 修改 API 端点
ARKFUNDS_API_TEMPLATE = "https://your-new-api.com/holdings?symbol={etf_symbol}"

# 更新数据转换逻辑
def _transform_json(self, json_data, etf_symbol, date):
    # 根据新API的JSON格式修改解析逻辑
    ...
```

### 2. 测试新数据源
```bash
python3 scripts/test_real_data.py
```

### 3. 验证数据一致性
对比新旧数据源的结果，确保一致性。

### 4. 更新文档
更新本文档和 `README.md`，说明新的数据源信息。

---

## 技术支持

### ARKFunds.io 项目
- **GitHub Issues**: https://github.com/frefrik/ark-invest-api/issues
- **讨论区**: https://github.com/frefrik/ark-invest-api/discussions

### ARK Invest 官方
- **官网**: https://ark-funds.com
- **Twitter**: @ARKinvest
- **联系方式**: info@ark-invest.com

---

**最后更新**: 2025-11-14  
**数据源版本**: ARKFunds.io API v1  
**维护者**: Lucian
