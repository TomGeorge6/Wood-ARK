# Wood-ARK Monitor Constitution

> **项目宪法**: Wood-ARK 持仓监控系统的开发原则和质量标准  
> **版本**: 1.1.0 | **创建**: 2025-01-13 | **最后更新**: 2025-11-13

---

## 🎯 项目使命

构建一个**可靠、简洁、本地优先**的 ARK 基金持仓监控系统，通过企业微信每日自动推送木头姐的最新投资动向，帮助投资者及时把握市场机会。

**核心价值观**:
- **可靠性 > 功能丰富度**: 99% 推送成功率是底线
- **简洁性 > 灵活性**: 本地 CSV + 3个核心依赖，拒绝过度设计
- **用户体验 > 技术炫技**: 报告要人类可读，不是机器日志

---

## 📜 核心原则 (Articles)

### Article I: 可靠性优先 (Reliability-First)

**不可协商**: 系统必须确保 **99%+ 每日持仓报告推送成功率**。

#### 1.1 本地执行架构
- **本地 cron 任务**: 每天 11:00 北京时间自动执行（可配置）
- **幂等性保证**: 通过 `data/cache/push_status.json` 防止重复推送
- **手动补偿**: `--check-missed` 模式检测并恢复错过的更新

#### 1.2 容错机制
- **部分成功策略**: 单个 ETF 失败不阻塞其他 ETF 处理
- **自动补偿**: `--check-missed` 模式检测并恢复错过的更新（最近 7 天）
- **失败告警**: 可配置是否发送错误告警到企业微信

#### 1.3 重试策略
- 网络请求: **3次重试**,指数退避 (1s, 2s, 4s)
- 企业微信推送: **3次重试**,每次间隔 5 秒
- 单个 ETF 超时: **30 秒**,超时后跳过并记录错误

---

### Article II: 模块化与职责分离 (Modularity)

**原则**: 每个功能模块必须**自包含、可独立测试、单一职责**。

#### 2.1 核心模块 (5+1 架构)

**禁止修改模块数量和职责边界**:

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **DataFetcher** | 下载 ARK CSV 并本地持久化 | ETF 名称, 日期 | DataFrame |
| **Analyzer** | 持仓对比与变化检测 | 当前/历史 DataFrame | 变化分析字典 |
| **ReportGenerator** | Markdown 报告格式化 | 分析结果字典 | Markdown 字符串 |
| **WeChatNotifier** | 企业微信 Webhook 推送 | Markdown 内容 | 布尔值 (成功/失败) |
| **Scheduler** | 任务编排与重试逻辑 | 配置, 模块实例 | 执行状态 |
| **Utils** | 共享工具函数 | 多种 | 多种 |

#### 2.2 接口契约
- **类型提示**: 所有公共方法必须有参数和返回值类型注解
- **私有方法**: 以 `_` 前缀标识实现细节
- **无跨模块状态**: 模块间仅通过返回值传递数据

#### 2.3 模块独立性验证
```python
# ✅ 正确: 模块独立可测试
def test_analyzer_without_fetcher():
    analyzer = Analyzer()
    result = analyzer.compare_holdings(mock_current, mock_previous)
    assert result['added'] == ['TSLA']

# ❌ 错误: 模块耦合
class Analyzer:
    def __init__(self, fetcher):  # 依赖其他模块实例
        self.fetcher = fetcher
```

---

### Article III: 配置驱动 (Configuration-Driven)

**原则**: **生产代码中禁止硬编码值**。所有环境相关配置必须存储在 `.env` (敏感信息) 或 `config.yaml` (非敏感配置)。

#### 3.1 必需配置项 (.env)

| 配置项 | 类型 | 默认值 | 说明 | 验证规则 |
|--------|------|--------|------|----------|
| `WECHAT_WEBHOOK_URL` | string | (必填) | 企业微信 Webhook 地址 | 必须以 `https://qyapi.weixin.qq.com` 开头 |

#### 3.2 通用配置 (config.yaml)

```yaml
schedule:
  enabled: true                # 是否启用定时任务
  cron_time: "11:00"           # 执行时间（北京时间）
  timezone: "Asia/Shanghai"    # 时区

data:
  etfs: ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"]  # 监控的 ETF 列表
  data_dir: "./data"           # 数据存储目录
  log_dir: "./logs"            # 日志存储目录

analysis:
  change_threshold: 5.0        # 显著变化阈值（%）

notification:
  webhook_url: "${WECHAT_WEBHOOK_URL}"  # 引用 .env 中的变量
  enable_error_alert: true     # 是否发送错误告警

retry:
  max_retries: 3               # 最大重试次数
  retry_delays: [1, 2, 4]      # 重试延迟（秒，指数退避）

log:
  retention_days: 30           # 日志保留天数
  level: "INFO"                # 日志级别（DEBUG/INFO/WARNING/ERROR）
```

#### 3.3 配置验证
```python
import yaml
import os
from dotenv import load_dotenv

# 加载配置
load_dotenv()
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 验证必需配置
def validate_config(config: dict) -> None:
    webhook_url = os.getenv('WECHAT_WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("❌ 未配置 WECHAT_WEBHOOK_URL，请检查 .env 文件")
    
    if not webhook_url.startswith('https://qyapi.weixin.qq.com'):
        raise ValueError("❌ WECHAT_WEBHOOK_URL 格式错误")
    
    # 验证配置文件完整性
    required_sections = ['schedule', 'data', 'analysis', 'notification', 'retry', 'log']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"❌ 配置文件缺少 {section} 章节")
```

---

### Article IV: 数据完整性与可追溯性 (Data Integrity)

**原则**: **所有数据操作必须可审计且可回溯**。

#### 4.1 不可变历史
- **禁止覆盖**: 已存在的 CSV 文件永不修改
- **文件命名**: 严格使用 `YYYY-MM-DD.csv` 格式
- **目录结构**: `data/holdings/{ETF}/{YYYY-MM-DD}.csv`

```python
# ✅ 正确: 日期命名,不覆盖
def save_holdings(df: pd.DataFrame, etf: str, date: str):
    path = f"data/holdings/{etf}/{date}.csv"
    if os.path.exists(path):
        logger.warning(f"文件已存在,跳过保存: {path}")
        return
    df.to_csv(path, index=False)

# ❌ 错误: 使用 latest.csv,会覆盖
def save_holdings(df: pd.DataFrame, etf: str):
    path = f"data/holdings/{etf}/latest.csv"  # ❌ 禁止
    df.to_csv(path, index=False)
```

#### 4.2 结构化日志
- **时间戳**: 所有日志必须包含 ISO 8601 格式时间
- **上下文**: ETF 名称、日期、操作类型
- **错误栈**: 异常必须包含完整 traceback

```python
# 日志格式示例
2025-01-15 08:00:05 [INFO] [DataFetcher] 开始下载 ARKK 持仓数据 (date=2025-01-15)
2025-01-15 08:00:08 [ERROR] [DataFetcher] ARKK 下载失败 (date=2025-01-15, error=Timeout)
Traceback (most recent call last):
  ...
```

#### 4.3 备份支持 (可选)
- 本地数据每周自动同步到腾讯云 COS
- 保留策略: 本地永久,云端 1 年
- 恢复验证: 每月测试云端数据可恢复性

---

### Article V: 用户中心的消息设计 (User-Centric)

**原则**: **报告必须可操作、易扫描、低噪音**。

#### 5.1 分层信息架构

```markdown
## 🚀 ARK 持仓日报 (2025-01-15)          # 1️⃣ 标题

### 📊 整体概况                          # 2️⃣ 摘要
- 监控 ETF: 5 只
- 有变化: 3 只
- 执行时间: 08:00:15

---

### 🔥 ARKK - 创新科技 ETF               # 3️⃣ 分 ETF 详情

**📈 新增股票** (1):                     # 4️⃣ 操作分类
- ✅ $HOOD Robinhood (0.5%)

**💹 持仓变化** (±5%):
- 📈 $TSLA +12.5% (8.2% → 9.1%)

**📌 前 5 大持仓**:                      # 5️⃣ 核心持仓
1. $TSLA Tesla (9.1%)
2. $COIN Coinbase (5.1%)
...
```

#### 5.2 阈值过滤
- **默认阈值**: ±5% 持仓变化
- **用户可配置**: 通过 `CHANGE_THRESHOLD` 环境变量调整
- **无变化场景**: 也推送报告,写明 "今日无重大变化"

#### 5.3 字符长度控制
- **企业微信限制**: 单条 Markdown 消息 ≤ 4096 字符
- **截断策略**: 
  1. 优先保留摘要和 ARKK (最重要 ETF)
  2. 其他 ETF 仅显示变化数量
  3. 末尾提示 "详情查看日志: logs/2025-01-15.log"

---

### Article VI: 性能与资源效率 (Performance)

**原则**: **为本地/云函数免费额度优化执行**。

#### 6.1 执行时间预算

| 操作 | 目标时间 | 最大时间 |
|------|---------|---------|
| 单个 ETF 下载 | 3 秒 | 30 秒 |
| 5 个 ETF 下载 | 15 秒 | 2 分钟 |
| 数据分析 | 5 秒 | 30 秒 |
| 报告生成 | 2 秒 | 10 秒 |
| 企业微信推送 | 3 秒 | 10 秒 |
| **总计** | **30 秒** | **5 分钟** |

#### 6.2 内存优化
- **目标内存**: <128MB (云函数最小配置)
- **DataFrame 清理**: 处理完立即释放 (`del df`)
- **避免全量加载**: 仅加载需要对比的两天数据

#### 6.3 I/O 优化
- **单次读取**: 每个 CSV 文件只读一次
- **批量写入**: 合并日志后一次性写入文件
- **缓存利用**: 当天数据存在则跳过下载

---

### Article VII: 防御式错误处理 (Fail-Safe)

**原则**: **错误必须触发告警,而非静默失败**。

#### 7.1 错误分类与响应

| 错误类型 | 严重级别 | 重试策略 | 告警方式 |
|---------|---------|---------|---------|
| 网络超时 | 警告 | 3次,指数退避 | 日志 |
| CSV 解析失败 | 错误 | 跳过该 ETF | 日志 + 企微告警 (可选) |
| Webhook 失败 | 严重 | 3次,固定间隔 | 日志 + 本地保存报告 |
| 配置缺失 | 致命 | 无 | 启动失败,打印错误 |

#### 7.2 部分成功策略
```python
# ✅ 正确: 单个 ETF 失败不影响其他
def fetch_all_etfs():
    results = {}
    errors = []
    
    for etf in ['ARKK', 'ARKW', 'ARKG']:
        try:
            results[etf] = fetch_single_etf(etf)
        except Exception as e:
            logger.error(f"{etf} 下载失败: {e}")
            errors.append(etf)
    
    if errors:
        send_error_alert(f"部分 ETF 下载失败: {errors}")
    
    return results  # 返回成功的部分

# ❌ 错误: 一个失败全部失败
def fetch_all_etfs():
    results = {}
    for etf in ['ARKK', 'ARKW', 'ARKG']:
        results[etf] = fetch_single_etf(etf)  # 抛出异常会中断循环
    return results
```

#### 7.3 日志轮转
- **按日分割**: 每天一个日志文件 (`logs/2025-01-15.log`)
- **保留策略**: 本地保留 30 天
- **压缩归档**: 7 天前的日志自动 gzip 压缩

---

## 🔧 技术约束 (Technical Constraints)

### 技术栈 (不可变更)

**编程语言**:
- Python **3.9+** (必须使用类型提示 Type Hints)

**核心依赖** (仅限 4 个):
1. **pandas** (2.0+): 数据处理
2. **requests** (2.31+): HTTP 请求
3. **python-dotenv** (1.0+): 环境变量管理
4. **PyYAML** (6.0+): 配置文件解析

**禁止引入**:
- ❌ 异步框架 (asyncio, aiohttp) - 项目规模不需要
- ❌ ORM 框架 (SQLAlchemy) - 无数据库
- ❌ Web 框架 (Flask, FastAPI) - 纯后台脚本
- ❌ 数据库系统 (MySQL, MongoDB) - CSV 足够

**理由**: 保持轻量级,降低维护成本,提高可靠性

---

### 部署环境

#### 本地环境
- **操作系统**: macOS (开发环境)
- **Python**: 3.9+ 安装在 `/usr/local/bin/python3`
- **定时任务**: cron (`crontab -e`)
  ```bash
  # 每天北京时间 11:00 执行
  0 11 * * 1-5 cd /Users/lucian/Documents/个人/Investment/Tools/Wood-ARK && /usr/local/bin/python3 main.py
  ```
- **数据存储**: `./data/` (相对于项目根目录)

---

### 数据源 (不可变更)

#### 主数据源
- **GitHub 镜像仓库**: `thisjustinh/ark-invest-history`
- **URL 格式**: `https://raw.githubusercontent.com/thisjustinh/ark-invest-history/master/fund-holdings/{ETF}.csv`
- **数据特点**: 包含完整历史数据,需自动筛选最新日期
- **更新时间**: 美东时间每日 19:00 (北京时间次日 07:00-08:00)
- **选择理由**: ARK 官网存在反爬虫机制 (403/404 错误),GitHub 镜像更稳定可靠

#### 备用数据源 (暂不实现)
- **ARK Invest 官网**: `https://ark-funds.com/wp-content/fundsiteliterature/csv/{ETF}_HOLDINGS.csv`
- **问题**: 反爬虫保护导致访问不稳定
- **后续优化**: 可实现双数据源自动切换机制

#### 数据源故障处理
如果 GitHub 镜像不可访问,系统发送告警（如启用），并等待下次 cron 任务重试

---

### 安全要求

#### 敏感信息管理
- **Webhook URL**: 存储在 `.env` 文件,**永不提交到 Git**
- **日志脱敏**: 日志中仅显示 Webhook URL 的前 20 个字符
- **权限控制**: `.env` 文件权限设置为 `600` (仅所有者可读写)

#### 网络访问
- **仅 HTTPS**: 所有外部请求必须使用 HTTPS
- **证书验证**: `requests` 库默认验证 SSL 证书
- **超时设置**: 所有 HTTP 请求必须设置 `timeout=30`

#### 数据隐私
- **公开数据**: ARK 持仓数据为公开信息,无隐私问题
- **无用户数据**: 系统不收集任何个人信息

---

## 📝 开发规范 (Development Standards)

### 代码质量标准

#### 1. 类型提示 (强制)
```python
# ✅ 正确
def fetch_holdings(etf: str, date: str) -> pd.DataFrame:
    pass

# ❌ 错误
def fetch_holdings(etf, date):  # 缺少类型提示
    pass
```

#### 2. 文档字符串 (强制)
```python
# ✅ 正确: Google Style Docstrings
def compare_holdings(current: pd.DataFrame, previous: pd.DataFrame) -> dict:
    """对比前后两日持仓数据
    
    Args:
        current: 当前持仓 DataFrame
        previous: 前一日持仓 DataFrame
        
    Returns:
        包含变化详情的字典:
        {
            'added': [新增股票列表],
            'removed': [移除股票列表],
            'changed': [变化股票列表]
        }
        
    Raises:
        ValueError: 如果 DataFrame 格式不正确
    """
    pass
```

#### 3. 命名规范
- **函数/变量**: `snake_case` (如 `fetch_holdings`)
- **类名**: `PascalCase` (如 `DataFetcher`)
- **常量**: `UPPER_SNAKE_CASE` (如 `MAX_RETRIES`)
- **私有方法**: `_private_method` (单下划线前缀)

#### 4. 代码风格
- **工具**: Black (自动格式化)
- **行宽**: 100 字符
- **缩进**: 4 空格

#### 5. 测试要求
- **核心模块必须测试**: Analyzer, ReportGenerator
- **测试框架**: pytest
- **覆盖率目标**: ≥ 70%

---

### Git 工作流

#### 分支策略
- **main**: 生产分支,受保护
- **develop**: 开发分支
- **feature/***: 功能分支
- **fix/***: 修复分支

#### Commit 规范 (Conventional Commits)
```bash
# 格式
<类型>(<范围>): <简短描述>

<详细描述>

# 类型
feat:     新功能
fix:      修复 bug
docs:     文档更新
style:    代码格式调整
refactor: 代码重构
test:     测试相关
chore:    构建/工具链更新

# 示例
feat(fetcher): 添加 ARK CSV 下载重试机制

- 实现 3 次指数退避重试
- 超时时间设置为 30 秒
- 添加详细错误日志

Closes #123
```

#### 文件排除 (.gitignore)
```gitignore
# 环境变量
.env

# 数据文件
data/
logs/

# Python
__pycache__/
*.pyc
venv/

# IDE
.vscode/
.idea/
```

---

### 版本控制

#### 语义化版本 (Semantic Versioning)
- **格式**: `MAJOR.MINOR.PATCH` (如 `1.2.3`)
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的 bug 修复

#### 变更日志
- 位置: `docs/CHANGELOG.md`
- 每个版本发布前必须更新

#### Git 标签
```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

---

### 部署流程

#### 本地部署检查清单
- [ ] 1. 克隆项目到本地
- [ ] 2. 安装依赖: `pip install -r requirements.txt`
- [ ] 3. 配置 `.env` 文件（Webhook URL）
- [ ] 4. 复制并修改 `config.yaml.example` 为 `config.yaml`
- [ ] 5. 测试 Webhook: `python main.py --test-webhook`
- [ ] 6. 手动执行: `python main.py --manual`
- [ ] 7. 检查日志和企微消息
- [ ] 8. 安装 cron: `scripts/install_cron.sh`
- [ ] 9. 验证 cron 任务: `crontab -l`

---

## 🏛️ 治理与合规 (Governance)

### 宪法权威

本文档是 **Wood-ARK 项目的唯一权威规范**。所有代码、文档和运维决策必须与本宪法保持一致。

**优先级顺序**:
1. **Constitution** (本文件) - 开发原则和质量标准
2. **PROJECT_DESIGN.md** - 架构设计和实现细节
3. **用户规则** (`lucian-coding-standards`) - 通用编码规范
4. **项目规则** (`wood-ark-project-constraints`) - 项目特定约束
5. **代码注释** - 实现细节说明

### 修正流程

#### 提案要求
修改宪法需要满足以下条件之一:
- 核心原则 (Article I-VII) 有明显缺陷
- 技术栈出现不可避免的升级需求
- 数据完整性保证需要调整

#### 审批流程
1. 在 GitHub Issue 中提出修正提案
2. 说明修改理由和影响范围
3. 提供向后兼容方案或迁移指南
4. 更新相关文档 (Constitution + PROJECT_DESIGN.md)
5. 项目维护者 (lucian) 批准后生效

### 合规验证

#### 代码审查要点
- ✅ 模块是否符合单一职责原则
- ✅ 是否有充分的错误处理和日志
- ✅ 配置是否外部化 (无硬编码)
- ✅ 是否有类型提示和文档字符串
- ✅ 测试是否覆盖核心逻辑

#### 测试门禁
- 所有 PR 必须通过 pytest 测试
- 手动运行 `python ark_monitor.py --manual` 成功
- 检查日志无 ERROR 级别消息

#### 运行时监控
- 每周检查 `logs/` 目录,发现异常
- 每月验证云端备份数据可恢复性
- 每季度审查依赖库安全漏洞

---

### 复杂度预算

**简洁性是特性**。拒绝不必要的抽象和过度设计。

| 指标 | 限制 | 理由 |
|------|------|------|
| 单模块文件长度 | ≤ 500 行 | 可读性 |
| 单函数长度 | ≤ 50 行 | 可测试性 |
| 圈复杂度 | ≤ 10 | 可维护性 |
| 外部依赖数量 | 4 个核心库 | 可靠性 |
| 嵌套层级 | ≤ 4 层 | 可读性 |

#### 复杂度检查
```bash
# 使用 radon 检查圈复杂度
pip install radon
radon cc src/ -s -a
# 目标: 平均复杂度 < 5
```

---

### 争议解决路径

对于本宪法未明确规定的场景,按以下顺序参考:

1. **Python PEP 8** (代码风格)
2. **Zen of Python** (设计哲学)
   ```python
   import this
   # Simple is better than complex.
   # Explicit is better than implicit.
   # Readability counts.
   ```
3. **项目维护者判断** (lucian)

---

## 📊 度量指标 (Success Metrics)

### 系统可靠性
- **推送成功率**: ≥ 99% (月度统计)
- **平均执行时间**: < 30 秒 (单次任务)
- **错误恢复时间**: < 1 小时 (自动补偿)

### 代码质量
- **测试覆盖率**: ≥ 70% (核心模块)
- **Pylint 评分**: ≥ 8.0
- **代码重复率**: < 5%

### 用户体验
- **报告可读性**: 企业微信消息阅读时间 < 30 秒
- **噪音控制**: 无变化时仅显示摘要
- **字符长度**: < 3000 字符 (< 企微限制 4096)

---

## 🔄 变更历史

| 版本 | 日期 | 变更内容 | 负责人 |
|------|------|---------|--------|
| 1.0.0 | 2025-01-13 | 初始版本 | lucian |
| 1.1.0 | 2025-11-13 | 整合 Spec-kit 工作流和项目规则 | lucian |
| 1.2.0 | 2025-11-13 | 删除云函数，改为纯本地部署；新增 config.yaml 支持 | lucian |

---

**批准**: lucian | **状态**: 生效中 | **下次审查**: 2026-01-13

---

> 💡 **提示**: 开发过程中如有疑问,优先参考本宪法,其次查阅 PROJECT_DESIGN.md
