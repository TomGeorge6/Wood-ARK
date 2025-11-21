# Tasks: ARK 持仓监控与企微推送系统

**Feature**: 001-ark-monitor  
**Branch**: `001-ark-monitor`  
**Date**: 2025-11-14（最后更新）  
**Prerequisites**: ✅ spec.md, ✅ plan.md, ✅ research.md, ✅ data-model.md, ✅ contracts/

**项目状态**: ✅ 已完成并上线（v2.0）

---

## Overview

本任务列表将项目分解为 **18 个独立任务**，按 Constitution 要求组织为 5 个阶段：

1. **Phase 1: Setup** - 项目初始化（1 任务）
2. **Phase 2: Foundational** - 核心工具类（2 任务）
3. **Phase 3: Core Modules** - 5+1 模块实现（6 任务）
4. **Phase 4: Testing** - 单元测试 + 集成测试（7 任务）
5. **Phase 5: Deployment** - 部署脚本 + 文档（2 任务）

**执行策略**:
- Phase 1-2 顺序执行（基础设施）
- Phase 3 可部分并行（不同模块）
- Phase 4 在对应模块完成后并行执行
- Phase 5 在所有测试通过后执行

---

## Phase 1: Setup (项目初始化)

**目标**: 建立项目骨架，完成基础配置

### T001 ✅ 创建项目结构和配置文件

**描述**: 按照 plan.md 定义的项目结构，创建所有目录和配置模板文件

**交付物**:
- [ ] 创建目录结构:
  ```bash
  mkdir -p src tests/fixtures data/{holdings,reports,cache} logs scripts docs
  ```
- [ ] 创建 `requirements.txt`:
  ```txt
  pandas>=2.0.0
  requests>=2.31.0
  python-dotenv>=1.0.0
  PyYAML>=6.0.0
  pytest>=7.0.0
  ```
- [ ] 创建 `.env.example`:
  ```bash
  WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
  ```
- [ ] 创建 `config.yaml.example`:
  ```yaml
  schedule:
    enabled: true
    cron_time: "11:00"
    timezone: "Asia/Shanghai"
  
  data:
    etfs: ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"]
    data_dir: "./data"
    log_dir: "./logs"
  
  analysis:
    change_threshold: 5.0
  
  notification:
    webhook_url: "${WECHAT_WEBHOOK_URL}"
    enable_error_alert: true
  
  retry:
    max_retries: 3
    retry_delays: [1, 2, 4]
  
  log:
    retention_days: 30
    level: "INFO"
  ```
- [ ] 创建 `.gitignore`:
  ```
  .env
  data/
  logs/
  __pycache__/
  *.pyc
  .pytest_cache/
  venv/
  ```
- [ ] 创建空文件:
  - `src/__init__.py`
  - `tests/__init__.py`
  - `main.py`（预留入口）

**验收标准**:
- ✅ 所有目录存在
- ✅ `pip install -r requirements.txt` 成功
- ✅ 配置模板文件可复制并编辑

---

## Phase 2: Foundational (基础工具类)

**目标**: 实现核心工具类，后续所有模块依赖这些工具

**⚠️ CRITICAL**: Phase 3 所有任务依赖此阶段完成

### T002 [P] 实现 src/utils.py - 配置加载和验证

**描述**: 实现配置管理工具函数，支持 YAML + .env 组合加载

**依赖**: T001 完成

**文件**: `src/utils.py`

**必须实现的函数**:
1. `load_config(config_path: str = 'config.yaml') -> Config`
   - 加载 .env 文件（python-dotenv）
   - 读取 config.yaml（PyYAML）
   - 替换 `${VAR}` 语法为环境变量值
   - 返回 Config 对象

2. `validate_config(config: Config) -> None`
   - 验证 webhook_url 非空且格式正确
   - 验证 change_threshold 在 0.1-100 范围
   - 验证 etfs 列表非空
   - 抛出 ValueError 如果不合法

**测试要求** (在 T010 实现):
- ✅ 正常配置加载成功
- ✅ webhook_url 缺失时抛出异常
- ✅ 环境变量替换正确

**验收标准**:
```python
from src.utils import load_config, validate_config

config = load_config()
validate_config(config)
print(config.notification.webhook_url)  # 应输出 .env 中的 URL
```

---

### T003 [P] 实现 src/utils.py - 日志和日期工具

**描述**: 实现日志配置、日期处理、日志清理工具函数

**依赖**: T001 完成（可与 T002 并行）

**文件**: `src/utils.py`（续）

**必须实现的函数**:
1. `setup_logging(log_dir: str, log_level: str = 'INFO') -> None`
   - 创建日志目录（如不存在）
   - 配置日志格式：`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
   - 日志文件命名：`{YYYY-MM-DD}.log`
   - 同时输出到文件和控制台

2. `cleanup_old_logs(log_dir: str, retention_days: int) -> None`
   - 删除 retention_days 天前的日志文件
   - 使用日期解析判断文件是否过期

3. `get_current_date() -> str`
   - 返回北京时间当前日期（YYYY-MM-DD）

4. `get_previous_date(date: str) -> str`
   - 返回前一天日期（YYYY-MM-DD）

5. `get_recent_dates(days: int) -> List[str]`
   - 返回最近 N 天的日期列表（倒序）

**测试要求** (在 T010 实现):
- ✅ 日志文件正确创建
- ✅ 日期计算正确
- ✅ 过期日志清理成功

**验收标准**:
```python
from src.utils import setup_logging, get_current_date, get_previous_date

setup_logging('./logs', 'INFO')
print(get_current_date())      # 2025-01-15
print(get_previous_date('2025-01-15'))  # 2025-01-14
```

---

## Phase 3: Core Modules (核心业务模块)

**目标**: 实现 5+1 模块架构的所有业务逻辑

**依赖**: Phase 2 完成（T002, T003）

### T004 实现 src/fetcher.py - DataFetcher 类

**描述**: 实现 ARK CSV 数据下载、保存、加载功能

**依赖**: T002, T003

**文件**: `src/fetcher.py`

**契约文档**: `specs/001-ark-monitor/contracts/fetcher.md`

**必须实现**:
1. `DataFetcher.__init__(config: Config)`
2. `fetch_holdings(etf_symbol: str, date: str) -> pd.DataFrame`
   - URL 模板：`https://ark-funds.com/wp-content/fundsiteliterature/csv/{etf_symbol}_HOLDINGS.csv`
   - 超时时间：30 秒
   - 重试机制：3 次，指数退避 [1, 2, 4] 秒
   - CSV 转换：按 data-model.md 的转换规则处理
3. `save_to_csv(df: pd.DataFrame, etf_symbol: str, date: str) -> None`
   - 路径：`data/holdings/{etf_symbol}/{date}.csv`
   - 如文件已存在，记录警告但不覆盖
4. `load_from_csv(etf_symbol: str, date: str) -> pd.DataFrame`
   - 读取本地 CSV 文件
   - 抛出 FileNotFoundError 如果不存在

**测试要求** (在 T011 实现):
- ✅ Mock HTTP 请求测试下载逻辑
- ✅ 测试 CSV 保存和加载
- ✅ 测试重试机制

**验收标准**:
```python
from src.fetcher import DataFetcher
from src.utils import load_config

config = load_config()
fetcher = DataFetcher(config)
df = fetcher.fetch_holdings('ARKK', '2025-01-15')
print(df.head())  # 应输出持仓数据
```

---

### T005 实现 src/analyzer.py - Analyzer 类

**描述**: 实现持仓对比算法，生成 ChangeAnalysis 对象

**依赖**: T002, T003

**文件**: `src/analyzer.py`

**契约文档**: `specs/001-ark-monitor/contracts/analyzer.md`

**必须实现**:
1. `Analyzer.__init__(threshold: float = 5.0)`
2. `compare_holdings(current: pd.DataFrame, previous: pd.DataFrame, etf_symbol: str, current_date: str, previous_date: str) -> ChangeAnalysis`
   - 使用 pandas merge 找出新增/移除/变化股票
   - 计算持股数变化百分比
   - 过滤显著变化（绝对值 >= threshold）
   - 返回 ChangeAnalysis 对象

**数据模型**: 参考 `specs/001-ark-monitor/data-model.md` 中的 ChangeAnalysis 定义

**测试要求** (在 T012 实现):
- ✅ 测试新增股票识别
- ✅ 测试移除股票识别
- ✅ 测试增持/减持计算
- ✅ 测试阈值过滤

**验收标准**:
```python
from src.analyzer import Analyzer
import pandas as pd

analyzer = Analyzer(threshold=5.0)
current = pd.read_csv('tests/fixtures/arkk_2025-01-15.csv')
previous = pd.read_csv('tests/fixtures/arkk_2025-01-14.csv')
result = analyzer.compare_holdings(current, previous, 'ARKK', '2025-01-15', '2025-01-14')
print(f"新增: {len(result.added)} 只")
print(f"增持: {len(result.increased)} 只")
```

---

### T006 实现 src/reporter.py - ReportGenerator 类

**描述**: 实现 Markdown 报告生成逻辑

**依赖**: T002, T003

**文件**: `src/reporter.py`

**契约文档**: `specs/001-ark-monitor/contracts/reporter.md`

**必须实现**:
1. `ReportGenerator.__init__()`
2. `generate_markdown(analyses: List[ChangeAnalysis], execution_time: str) -> str`
   - 生成完整 Markdown 报告
   - 格式参考 data-model.md 中的示例
   - 字符长度限制：<4096（如超过则截断并提示）
3. `save_report(content: str, etf_symbol: str, date: str) -> None`
   - 路径：`data/reports/{etf_symbol}/{date}.md`

**测试要求** (在 T013 实现):
- ✅ 测试 Markdown 格式正确性
- ✅ 测试字符长度截断
- ✅ 测试报告保存

**验收标准**:
```python
from src.reporter import ReportGenerator

generator = ReportGenerator()
markdown = generator.generate_markdown([analysis1, analysis2], '11:05:23')
print(markdown[:200])  # 应输出格式化的 Markdown
```

---

### T007 实现 src/notifier.py - WeChatNotifier 类

**描述**: 实现企业微信 Webhook 推送功能

**依赖**: T002, T003

**文件**: `src/notifier.py`

**契约文档**: `specs/001-ark-monitor/contracts/notifier.md`

**必须实现**:
1. `WeChatNotifier.__init__(webhook_url: str, max_retries: int = 3)`
2. `send_markdown(content: str) -> bool`
   - 请求体：`{"msgtype": "markdown", "markdown": {"content": content}}`
   - 重试策略：3 次，每次间隔 5 秒
   - 返回 True 表示成功
3. `send_error_alert(error_message: str) -> bool`
   - 发送纯文本错误告警
4. `test_connection() -> bool`
   - 发送测试消息验证连接

**测试要求** (在 T014 实现):
- ✅ Mock HTTP 请求测试推送逻辑
- ✅ 测试重试机制
- ✅ 测试连接测试功能

**验收标准**:
```python
from src.notifier import WeChatNotifier
import os

webhook_url = os.getenv('WECHAT_WEBHOOK_URL')
notifier = WeChatNotifier(webhook_url, max_retries=3)
success = notifier.test_connection()
print(f"连接测试: {'成功' if success else '失败'}")
```

---

### T008 实现 src/scheduler.py - Scheduler 类

**描述**: 实现任务调度和状态管理逻辑

**依赖**: T002, T003, T004, T005, T006, T007

**文件**: `src/scheduler.py`

**契约文档**: `specs/001-ark-monitor/contracts/scheduler.md`

**必须实现**:
1. `Scheduler.__init__(config: Config)`
2. `should_run_today() -> bool`
   - 检查今天是否为周一到周五
3. `get_previous_trading_day(current_date: str) -> str`
   - 简化实现：返回前一天（不考虑节假日）
4. `check_missed_dates(days: int = 7) -> List[str]`
   - 检测最近 N 天缺失的持仓数据
5. `is_already_pushed(date: str) -> bool`
   - 读取 `data/cache/push_status.json`
6. `mark_pushed(date: str, success: bool, etfs: List[str]) -> None`
   - 更新推送状态文件
7. `run_daily_task(date: str, force: bool = False) -> None`
   - 编排完整流程：下载 → 分析 → 报告 → 推送

**测试要求** (在 T015 实现):
- ✅ 测试工作日判断
- ✅ 测试缺失日期检测
- ✅ 测试状态文件读写
- ✅ Mock 集成测试完整流程

**验收标准**:
```python
from src.scheduler import Scheduler
from src.utils import load_config

config = load_config()
scheduler = Scheduler(config)
missed = scheduler.check_missed_dates(7)
print(f"缺失日期: {missed}")
```

---

### T009 实现 main.py - CLI 入口

**描述**: 实现命令行接口，支持所有执行模式

**依赖**: T008 完成

**文件**: `main.py`

**必须支持的参数**:
```bash
python main.py                    # 自动模式（检查工作日）
python main.py --manual           # 手动强制执行
python main.py --date 2025-01-15  # 指定日期
python main.py --check-missed     # 检查缺失日期
python main.py --test-webhook     # 测试 Webhook
```

**实现要求**:
1. 使用 argparse 解析参数
2. 调用 Scheduler.run_daily_task() 执行任务
3. 异常处理和日志记录
4. 退出码：成功=0，失败=1

**测试要求** (在 T016 实现):
- ✅ 测试所有参数组合
- ✅ 测试异常处理

**验收标准**:
```bash
python main.py --test-webhook
# 预期输出：✅ Webhook 连接正常
```

---

## Phase 4: Testing (测试覆盖)

**目标**: 确保所有模块有完整的单元测试和集成测试

**依赖**: Phase 3 对应模块完成

### T010 [P] 编写 tests/test_utils.py

**描述**: 测试 utils.py 中的所有工具函数

**依赖**: T002, T003

**文件**: `tests/test_utils.py`

**测试用例**:
1. `test_load_config_success()` - 正常加载配置
2. `test_load_config_missing_env()` - webhook_url 缺失时抛出异常
3. `test_validate_config_invalid_threshold()` - 阈值超出范围
4. `test_setup_logging()` - 日志文件创建成功
5. `test_get_current_date()` - 日期格式正确
6. `test_get_previous_date()` - 前一天计算正确
7. `test_cleanup_old_logs()` - 过期日志清理成功

**验收标准**:
```bash
pytest tests/test_utils.py -v
# 所有测试通过
```

---

### T011 [P] 编写 tests/test_fetcher.py

**描述**: 测试 DataFetcher 类

**依赖**: T004

**文件**: `tests/test_fetcher.py`

**测试用例**:
1. `test_fetch_holdings_success()` - Mock HTTP 请求，测试下载成功
2. `test_fetch_holdings_retry()` - Mock 失败 2 次后成功，验证重试
3. `test_save_to_csv()` - 测试 CSV 保存
4. `test_load_from_csv()` - 测试 CSV 加载
5. `test_load_from_csv_not_found()` - 文件不存在时抛出异常

**验收标准**:
```bash
pytest tests/test_fetcher.py -v
# 所有测试通过
```

---

### T012 [P] 编写 tests/test_analyzer.py

**描述**: 测试 Analyzer 类

**依赖**: T005

**文件**: `tests/test_analyzer.py`

**准备 fixtures**:
- `tests/fixtures/arkk_2025-01-14.csv`（前一日持仓）
- `tests/fixtures/arkk_2025-01-15.csv`（当前持仓）

**测试用例**:
1. `test_compare_holdings_added()` - 识别新增股票
2. `test_compare_holdings_removed()` - 识别移除股票
3. `test_compare_holdings_increased()` - 识别增持
4. `test_compare_holdings_decreased()` - 识别减持
5. `test_compare_holdings_threshold()` - 阈值过滤正确

**验收标准**:
```bash
pytest tests/test_analyzer.py -v
# 所有测试通过
```

---

### T013 [P] 编写 tests/test_reporter.py

**描述**: 测试 ReportGenerator 类

**依赖**: T006

**文件**: `tests/test_reporter.py`

**测试用例**:
1. `test_generate_markdown()` - Markdown 格式正确
2. `test_generate_markdown_truncate()` - 超过 4096 字符截断
3. `test_save_report()` - 报告保存成功

**验收标准**:
```bash
pytest tests/test_reporter.py -v
# 所有测试通过
```

---

### T014 [P] 编写 tests/test_notifier.py

**描述**: 测试 WeChatNotifier 类

**依赖**: T007

**文件**: `tests/test_notifier.py`

**测试用例**:
1. `test_send_markdown_success()` - Mock HTTP 请求成功
2. `test_send_markdown_retry()` - Mock 失败 2 次后成功
3. `test_send_error_alert()` - 发送错误告警
4. `test_test_connection()` - 连接测试

**验收标准**:
```bash
pytest tests/test_notifier.py -v
# 所有测试通过
```

---

### T015 [P] 编写 tests/test_scheduler.py

**描述**: 测试 Scheduler 类

**依赖**: T008

**文件**: `tests/test_scheduler.py`

**测试用例**:
1. `test_should_run_today_weekday()` - 工作日返回 True
2. `test_should_run_today_weekend()` - 周末返回 False
3. `test_check_missed_dates()` - 缺失日期检测
4. `test_is_already_pushed()` - 状态文件读取
5. `test_mark_pushed()` - 状态文件更新

**验收标准**:
```bash
pytest tests/test_scheduler.py -v
# 所有测试通过
```

---

### T016 编写 tests/test_integration.py

**描述**: 端到端集成测试，覆盖完整流程

**依赖**: T004-T009 全部完成

**文件**: `tests/test_integration.py`

**测试场景**:
1. `test_full_workflow_manual()` - 手动模式完整流程
   - Mock HTTP 下载 ARK CSV
   - Mock 企业微信推送
   - 验证持仓数据保存
   - 验证报告生成
   - 验证状态文件更新

2. `test_full_workflow_check_missed()` - 补偿模式
   - Mock 缺失 3 天数据
   - 验证自动补充
   - 验证推送正确

**验收标准**:
```bash
pytest tests/test_integration.py -v
# 所有测试通过
```

---

## Phase 5: Deployment (部署与文档)

**目标**: 提供自动化部署脚本和用户文档

**依赖**: Phase 4 全部测试通过

### T017 编写部署脚本

**描述**: 创建 cron 安装/卸载脚本

**依赖**: T009, T016

**交付物**:

1. **scripts/install_cron.sh**
   ```bash
   #!/bin/bash
   # 安装 cron 任务
   
   PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
   PYTHON_BIN="$(which python3)"
   CRON_TIME="0 11 * * 1-5"  # 周一到周五 11:00
   
   # 添加 cron 任务
   (crontab -l 2>/dev/null; echo "$CRON_TIME cd $PROJECT_DIR && $PYTHON_BIN main.py") | crontab -
   
   echo "✅ Cron 任务安装成功！"
   echo "验证: crontab -l"
   ```

2. **scripts/uninstall_cron.sh**
   ```bash
   #!/bin/bash
   # 卸载 cron 任务
   
   crontab -l | grep -v "main.py" | crontab -
   echo "✅ Cron 任务卸载成功！"
   ```

3. **scripts/cleanup_logs.sh**
   ```bash
   #!/bin/bash
   # 手动清理过期日志
   
   find logs/ -name "*.log" -mtime +30 -delete
   echo "✅ 过期日志清理完成！"
   ```

**验收标准**:
```bash
./scripts/install_cron.sh
crontab -l  # 应显示新添加的 cron 任务
```

---

### T018 编写项目文档

**描述**: 创建用户文档和故障排查指南

**依赖**: T017

**交付物**:

1. **docs/README.md** - 项目说明
   - 项目概述
   - 功能列表
   - 安装步骤（参考 quickstart.md）
   - 使用方法
   - 配置说明

2. **docs/CHANGELOG.md** - 版本变更日志
   ```markdown
   # Changelog
   
   ## [1.0.0] - 2025-01-15
   
   ### Added
   - 初始版本发布
   - 支持 ARKK、ARKW、ARKG、ARKQ、ARKF 五只 ETF 监控
   - 企业微信推送功能
   - 手动补偿模式
   ```

3. **docs/TROUBLESHOOTING.md** - 常见问题排查
   - cron 任务不执行
   - 企业微信推送失败
   - 网络代理配置
   - 数据下载失败

**验收标准**:
- ✅ 文档内容完整清晰
- ✅ 按照文档能完成安装和配置
- ✅ 常见问题有解决方案

---

## Dependencies & Execution Order

### 阶段依赖关系

```
Phase 1: Setup (T001)
    ↓
Phase 2: Foundational (T002 || T003)
    ↓
Phase 3: Core Modules
    ├─ T004 (fetcher)
    ├─ T005 (analyzer)
    ├─ T006 (reporter)
    ├─ T007 (notifier)
    ├─ T008 (scheduler) ← 依赖 T004-T007
    └─ T009 (main) ← 依赖 T008
    ↓
Phase 4: Testing
    ├─ T010 || T011 || T012 || T013 || T014 || T015 (单元测试)
    └─ T016 (集成测试) ← 依赖所有单元测试
    ↓
Phase 5: Deployment
    ├─ T017 (脚本)
    └─ T018 (文档)
```

### 任务依赖矩阵

| 任务 | 依赖任务 | 可并行任务 |
|------|---------|-----------|
| T001 | 无 | - |
| T002 | T001 | T003 |
| T003 | T001 | T002 |
| T004 | T002, T003 | T005, T006, T007 |
| T005 | T002, T003 | T004, T006, T007 |
| T006 | T002, T003 | T004, T005, T007 |
| T007 | T002, T003 | T004, T005, T006 |
| T008 | T004, T005, T006, T007 | - |
| T009 | T008 | - |
| T010 | T002, T003 | T011-T015 |
| T011 | T004 | T010, T012-T015 |
| T012 | T005 | T010-T011, T013-T015 |
| T013 | T006 | T010-T012, T014-T015 |
| T014 | T007 | T010-T013, T015 |
| T015 | T008 | T010-T014 |
| T016 | T010-T015 | - |
| T017 | T009, T016 | T018 |
| T018 | T017 | - |

### 并行执行机会

**阶段内并行**:
- Phase 2: T002 || T003
- Phase 3: T004 || T005 || T006 || T007（所有核心模块）
- Phase 4: T010 || T011 || T012 || T013 || T014 || T015（所有单元测试）

**建议执行顺序**（单人开发）:
1. T001
2. T002 → T003（顺序）
3. T004 → T011（完成一个模块立即测试）
4. T005 → T012
5. T006 → T013
6. T007 → T014
7. T010（补充 utils 测试）
8. T008 → T015
9. T009
10. T016（集成测试）
11. T017 → T018

**多人协作执行顺序**:
- **开发者 A**: T001 → T002 → T004 → T011 → T008
- **开发者 B**: T003 → T005 → T012 → T015
- **开发者 C**: T006 → T013 → T007 → T014
- **开发者 D**: T010 → T009 → T016 → T017 → T018

---

## Implementation Strategy

### MVP First (最小可行产品)

**阶段 1: 基础功能（T001-T009）**
- 目标：能手动执行一次完整流程
- 交付：`python main.py --manual` 成功推送报告
- 时间：约 2-3 天

**阶段 2: 测试覆盖（T010-T016）**
- 目标：所有模块有测试覆盖
- 交付：`pytest` 全部通过
- 时间：约 1-2 天

**阶段 3: 自动化部署（T017-T018）**
- 目标：能通过 cron 自动执行
- 交付：文档齐全，可交付用户使用
- 时间：约 0.5-1 天

### Checkpoints

**Checkpoint 1: Phase 2 完成**
- ✅ 配置文件能正常加载
- ✅ 日志系统工作正常
- ✅ 日期工具函数正确

**Checkpoint 2: Phase 3 完成**
- ✅ 能从 ARK 下载 CSV 数据
- ✅ 能分析持仓变化
- ✅ 能生成 Markdown 报告
- ✅ 能推送到企业微信
- ✅ `python main.py --manual` 成功执行

**Checkpoint 3: Phase 4 完成**
- ✅ 所有单元测试通过
- ✅ 集成测试通过
- ✅ 测试覆盖率 >80%

**Checkpoint 4: Phase 5 完成**
- ✅ cron 任务安装成功
- ✅ 文档齐全
- ✅ 项目可交付

---

## Notes

- **[P]** 标记：可并行执行的任务
- **测试优先**: 在实现模块前准备 fixtures，实现后立即编写测试
- **提交策略**: 每完成一个任务提交一次 git commit
- **Code Review**: T008, T009, T016 完成后进行代码审查
- **文档同步**: 修改代码时同步更新契约文档（contracts/）

---

**Tasks Status**: ✅ Ready for Implementation | **Total Tasks**: 18 | **Estimated Time**: 4-6 days

