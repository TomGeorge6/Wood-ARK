# 文档清理与重组计划

## 当前文档状态分析

### 根目录下的 MD 文件（13个）

| 文件名 | 大小 | 类型 | 状态 |
|--------|------|------|------|
| README.md | 8.7K | 主文档 | ✅ 保留 |
| PROJECT_DESIGN.md | 53K | 设计文档 | ⚠️ 过时，需更新 |
| CHANGELOG_20251114.md | 2.6K | 临时日志 | ❌ 删除（合并到 CHANGELOG.md） |
| FINAL_SUMMARY.md | 8.5K | 临时总结 | ❌ 删除（内容合并） |
| OPTION_A_REVIEW.md | 11K | 临时分析 | ❌ 删除（内容合并） |
| FIXES_20251114.md | 8.0K | 临时修复记录 | ❌ 删除 |
| FIXES_20251114_v2.md | 4.3K | 临时修复记录 | ❌ 删除 |
| FIXES_SUMMARY.md | 5.5K | 临时总结 | ❌ 删除 |
| FIX_SUMMARY.md | 3.1K | 临时总结 | ❌ 删除 |
| IMPLEMENTATION_SUMMARY.md | 12K | 临时总结 | ❌ 删除 |
| UPDATES_20251114_FINAL.md | 8.0K | 临时更新记录 | ❌ 删除 |
| UPDATES_SUMMARY.md | 5.7K | 临时总结 | ❌ 删除 |
| QUICK_START_v2.md | 6.5K | 快速开始 | ⚠️ 合并到 README.md |

**问题**：
- 🔴 大量临时文档（FIXES_*, UPDATES_*, SUMMARY_*）导致混乱
- 🔴 重复内容（多个 SUMMARY 文档）
- 🔴 过时内容（v2 后缀表示有旧版本）

### specs/ 目录（Spec-Kit 文档）

```
specs/001-ark-monitor/
├── spec.md              # 功能规格
├── plan.md              # 实施计划
├── tasks.md             # 任务列表
├── quickstart.md        # 快速开始
├── research.md          # 研究文档
├── data-model.md        # 数据模型
└── contracts/           # 模块契约
    ├── fetcher.md
    ├── analyzer.md
    ├── reporter.md
    ├── notifier.md
    ├── scheduler.md
    └── utils.md
```

**状态**: ✅ 结构良好，但需要更新内容以反映最新需求变化

### docs/ 目录（用户文档）

```
docs/
├── SUMMARY_FEATURE_GUIDE.md
├── API.md
├── CONFIGURATION.md
├── DEPLOYMENT.md
├── DEVELOPMENT.md
├── FAQ.md
├── TROUBLESHOOTING.md
└── examples/
```

**状态**: ⚠️ 部分文档存在，但不完整

---

## 清理方案

### 阶段1: 删除临时文档（❌ 删除9个文件）

**删除列表**:
1. CHANGELOG_20251114.md
2. FINAL_SUMMARY.md
3. OPTION_A_REVIEW.md
4. FIXES_20251114.md
5. FIXES_20251114_v2.md
6. FIXES_SUMMARY.md
7. FIX_SUMMARY.md
8. IMPLEMENTATION_SUMMARY.md
9. UPDATES_20251114_FINAL.md
10. UPDATES_SUMMARY.md
11. QUICK_START_v2.md

**保留的有价值内容**:
- ✅ 历史数据问题说明 → 合并到 docs/FAQ.md
- ✅ 选项A可行性分析 → 合并到 docs/DEPLOYMENT.md
- ✅ 快速开始 → 合并到 README.md

### 阶段2: 重组核心文档

#### 2.1 根目录（4个文件）

```
/
├── README.md              # 项目概览 + 快速开始 + 使用指南
├── CHANGELOG.md           # 版本变更日志（新建）
├── CONTRIBUTING.md        # 贡献指南（新建）
└── LICENSE                # 许可证（如需要）
```

#### 2.2 docs/ 目录（用户文档）

```
docs/
├── QUICK_START.md         # 快速开始（详细版）
├── CONFIGURATION.md       # 配置说明
├── DEPLOYMENT.md          # 部署指南（包含选项A说明）
├── USAGE.md               # 使用指南（命令参数）
├── FAQ.md                 # 常见问题（包含历史数据说明）
├── TROUBLESHOOTING.md     # 故障排除
├── SUMMARY_FEATURE_GUIDE.md  # 汇总功能指南（已存在）
└── examples/              # 示例
    ├── webhook-message.json
    └── report-sample.md
```

#### 2.3 specs/ 目录（Spec-Kit 文档）

```
specs/001-ark-monitor/
├── spec.md              # ✅ 功能规格（更新）
├── plan.md              # ✅ 实施计划（更新）
├── tasks.md             # ✅ 任务列表（更新）
├── data-model.md        # ✅ 数据模型（更新）
├── architecture.md      # 🆕 架构设计（从 PROJECT_DESIGN.md 提取）
└── contracts/           # ✅ 模块契约（更新）
    ├── fetcher.md
    ├── analyzer.md
    ├── reporter.md
    ├── notifier.md
    ├── scheduler.md
    ├── summary_analyzer.md   # 🆕 新增
    ├── summary_notifier.md   # 🆕 新增
    ├── image_generator.md    # 🆕 新增
    └── utils.md
```

#### 2.4 PROJECT_DESIGN.md 处理

**方案**: 拆分为多个文档
- 架构设计 → `specs/001-ark-monitor/architecture.md`
- 部署方案 → `docs/DEPLOYMENT.md`
- 开发计划 → `specs/001-ark-monitor/plan.md`（更新）
- 数据结构 → `specs/001-ark-monitor/data-model.md`（更新）

**删除**: PROJECT_DESIGN.md（内容已全部迁移）

---

## 更新方案（Spec-Kit 方法论）

### 1. spec.md - 功能规格

**更新内容**:
- ✅ 新增 User Story 3: 查看汇总报告
- ✅ 新增 User Story 4: 查看趋势图
- ✅ 更新数据源说明（ARKFunds.io + 历史数据策略）
- ✅ 更新推送格式（6条消息：1汇总 + 5单基金）

### 2. plan.md - 实施计划

**更新内容**:
- ✅ 标记已完成的里程碑
- ✅ 添加 v2.0 汇总功能里程碑
- ✅ 添加数据累积策略里程碑

### 3. tasks.md - 任务列表

**更新内容**:
- ✅ 标记已完成的任务
- ✅ 添加文档整理任务
- ✅ 添加部署自动化任务

### 4. contracts/ - 模块契约

**新增模块**:
- `summary_analyzer.md` - 汇总分析器契约
- `summary_notifier.md` - 汇总推送器契约
- `image_generator.md` - 图片生成器契约

**更新现有契约**:
- `fetcher.md` - 更新 CSV 格式说明（sep=','）
- `analyzer.md` - 更新持股数趋势说明

---

## 新建文档

### docs/USAGE.md - 使用指南（新建）

**内容**:
```markdown
# 使用指南

## 命令行参数

### 1. 自动模式（默认）
自动检测工作日，只在周一到周五执行。

### 2. 手动模式
强制执行，忽略工作日检查。

### 3. 指定ETF
只处理指定的ETF。

### 4. 指定日期
获取指定日期的数据。

### 5. 补充历史数据
下载最近N天的历史数据。

### 6. 测试模式
测试企业微信推送。

## 使用示例
...
```

### CHANGELOG.md - 变更日志（新建）

**内容**:
```markdown
# 变更日志

## [2.0.0] - 2025-11-14

### 新增
- 🆕 ARK 全系列基金汇总报告
- 🆕 长图报告生成（包含趋势图）
- 🆕 持股数趋势图（替代权重趋势）
- 🆕 自动化部署脚本

### 修复
- 🐛 CSV 文件格式问题（添加 sep=','）
- 🐛 历史数据下载逻辑

### 变更
- 📊 Top 3 改为 Top 10
- 📈 权重趋势改为持股数趋势

## [1.0.0] - 2025-11-13

### 初始版本
- ✅ 基础持仓监控功能
...
```

---

## 执行顺序

1. ✅ **备份当前文档**（防止误删）
2. ✅ **删除临时文档**（11个文件）
3. ✅ **提取有价值内容** → 合并到新文档
4. ✅ **更新 Spec-Kit 文档**（spec.md, plan.md, tasks.md）
5. ✅ **新建用户文档**（USAGE.md, CHANGELOG.md）
6. ✅ **更新 README.md**（整合 QUICK_START_v2.md）
7. ✅ **删除 PROJECT_DESIGN.md**（内容已迁移）
8. ✅ **验证文档链接**（确保无死链）

---

## 最终文档结构

```
Wood-ARK/
├── README.md                      # 项目概览 + 快速开始
├── CHANGELOG.md                   # 变更日志
├── CONTRIBUTING.md                # 贡献指南
│
├── docs/                          # 用户文档
│   ├── QUICK_START.md            # 快速开始（详细）
│   ├── USAGE.md                  # 使用指南（命令参数）★ 新建
│   ├── CONFIGURATION.md          # 配置说明
│   ├── DEPLOYMENT.md             # 部署指南
│   ├── FAQ.md                    # 常见问题
│   ├── TROUBLESHOOTING.md        # 故障排除
│   ├── SUMMARY_FEATURE_GUIDE.md  # 汇总功能指南
│   └── examples/
│
├── specs/001-ark-monitor/         # Spec-Kit 文档
│   ├── spec.md                   # 功能规格 ★ 更新
│   ├── plan.md                   # 实施计划 ★ 更新
│   ├── tasks.md                  # 任务列表 ★ 更新
│   ├── data-model.md             # 数据模型 ★ 更新
│   ├── architecture.md           # 架构设计 ★ 新建
│   └── contracts/                # 模块契约 ★ 更新+新增
│       ├── fetcher.md
│       ├── analyzer.md
│       ├── reporter.md
│       ├── notifier.md
│       ├── scheduler.md
│       ├── summary_analyzer.md   # ★ 新增
│       ├── summary_notifier.md   # ★ 新增
│       ├── image_generator.md    # ★ 新增
│       └── utils.md
│
└── scripts/                       # 脚本
    ├── setup_launchd.sh
    └── check_data_integrity.py
```

**文件数量对比**:
- 当前根目录 MD: 13个 → 清理后: 3个 ✅
- 冗余度: 高 → 低 ✅
- 结构清晰度: 差 → 优 ✅

---

**下一步**: 开始执行清理计划
