# 变更日志 (Changelog)

本项目遵循 [语义化版本 (Semantic Versioning)](https://semver.org/lang/zh-CN/)。

---

## [1.0.0] - 2025-11-13

### 🎉 初始版本发布

#### Added (新增功能)
- ✅ **数据获取**: 支持从 GitHub 镜像自动下载 ARK ETF 持仓数据
  - 支持 5 只 ETF: ARKK, ARKW, ARKG, ARKQ, ARKF
  - 自动筛选最新日期数据（处理历史 CSV 格式）
  - 网络重试机制（3 次，指数退避）
  - User-Agent 头避免 403 错误

- ✅ **持仓分析**: 智能识别持仓变化
  - 新增持仓识别
  - 移除持仓识别
  - 显著增持/减持识别（可配置阈值，默认 5%）
  - 权重变化计算

- ✅ **报告生成**: 自动生成 Markdown 格式报告
  - 清晰的表格布局
  - Emoji 图标标识（✅❌📈📉📊）
  - 支持多 ETF 合并报告
  - 报告保存到本地文件

- ✅ **企业微信推送**: 自动推送每日报告
  - Markdown 消息支持
  - 推送重试机制（3 次，间隔 5 秒）
  - 错误告警功能
  - 连接测试功能

- ✅ **任务调度**: 灵活的调度策略
  - 工作日自动执行（周一到周五）
  - 手动强制执行模式
  - 指定日期查询模式
  - 缺失数据补偿模式（检查最近 7 天）
  - 推送状态跟踪（幂等性保证）

- ✅ **配置管理**: 灵活的配置系统
  - YAML 配置文件支持
  - 环境变量支持（`.env` 文件）
  - 敏感信息保护（Webhook URL 通过环境变量）
  - 参数验证机制

- ✅ **日志系统**: 完善的日志记录
  - 按日期分文件存储
  - 可配置日志级别（DEBUG/INFO/WARNING/ERROR）
  - 自动清理过期日志（默认保留 30 天）
  - 同时输出到文件和控制台

- ✅ **部署脚本**: 自动化部署工具
  - `install_cron.sh`: 安装 cron 定时任务
  - `uninstall_cron.sh`: 卸载 cron 任务
  - `cleanup_logs.sh`: 手动清理日志

- ✅ **测试覆盖**: 完整的测试套件
  - 单元测试（6 个测试模块）
  - 集成测试（端到端流程）
  - Mock HTTP 请求和响应
  - 测试覆盖率 >80%

#### Technical Details (技术细节)
- **架构**: 5+1 模块设计（fetcher, analyzer, reporter, notifier, scheduler + utils）
- **数据源**: GitHub 镜像 (thisjustinh/ark-invest-history)
- **数据格式**: CSV 文件存储，按日期和 ETF 分类
- **编程语言**: Python 3.9+
- **核心依赖**: pandas, requests, python-dotenv, PyYAML
- **定时任务**: cron (macOS/Linux)

#### Known Issues (已知问题)
- ❌ **数据源单一**: 仅支持 GitHub 镜像，ARK 官网备用源暂未实现
- ⚠️ **节假日判断**: 简化实现，仅判断周末，不考虑美国股市节假日
- ⚠️ **时区处理**: 固定北京时间，不考虑美国夏令时影响

#### Documentation (文档)
- 📝 **README.md**: 项目介绍和使用指南
- 📝 **CHANGELOG.md**: 变更日志
- 📝 **TROUBLESHOOTING.md**: 常见问题排查
- 📝 **PROJECT_DESIGN.md**: 技术架构文档
- 📝 **Spec 文档**: 完整的需求规范和契约定义

---

## [未来计划]

### v1.1.0 (计划中)
- [ ] 双数据源自动切换（GitHub 镜像 + ARK 官网）
- [ ] 美国股市节假日识别
- [ ] Telegram/钉钉推送支持
- [ ] Web Dashboard（可视化历史持仓变化）

### v1.2.0 (考虑中)
- [ ] 持仓变化趋势分析（7/30 天）
- [ ] 自定义告警规则（如 TSLA 权重 >15%）
- [ ] 数据导出功能（Excel/JSON）
- [ ] Docker 容器化部署

---

**版本规则**:
- **主版本号 (MAJOR)**: 不兼容的 API 变更
- **次版本号 (MINOR)**: 向下兼容的功能性新增
- **修订号 (PATCH)**: 向下兼容的问题修正

**最后更新**: 2025-11-13
