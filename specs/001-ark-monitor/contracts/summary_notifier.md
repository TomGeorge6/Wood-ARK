# 模块契约：SummaryNotifier

**模块名称**: `src/summary_notifier.py`  
**职责**: 生成并推送 ARK 全系列基金汇总报告  
**版本**: v2.0  
**最后更新**: 2025-11-14

---

## 📋 模块概述

`SummaryNotifier` 负责将汇总分析结果转换为企业微信消息（Markdown + 长图），并推送到群聊。

**核心功能**:
- 生成卡片式 Markdown 汇总报告
- 调用 `ImageGenerator` 生成汇总长图
- 推送汇总消息到企业微信
- 处理推送失败重试

---

## 🔌 公共接口

### 类定义

```python
class SummaryNotifier:
    """汇总报告生成与推送"""
    
    def __init__(self, config: Config, webhook_url: str):
        """初始化汇总通知器
        
        Args:
            config: 系统配置对象
            webhook_url: 企业微信 Webhook URL
        """
```

---

### 方法1：generate_and_send

**功能**: 生成汇总报告并推送到企业微信

**签名**:
```python
def generate_and_send(
    self,
    summary: SummaryAnalysis,
    all_holdings: Dict[str, pd.DataFrame]
) -> bool
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `summary` | `SummaryAnalysis` | 汇总分析结果 |
| `all_holdings` | `Dict[str, pd.DataFrame]` | 所有基金的持仓数据（用于生成趋势图） |

**返回值**:
- **类型**: `bool`
- **说明**: `True` 表示推送成功，`False` 表示失败

**流程**:
1. 生成 Markdown 卡片式报告（调用 `_generate_markdown()`）
2. 生成汇总长图（调用 `image_generator.generate_summary_image()`）
3. 推送 Markdown 消息
4. 推送长图
5. 返回是否成功

---

### 方法2：_generate_markdown（私有）

**功能**: 生成卡片式 Markdown 报告

**签名**:
```python
def _generate_markdown(
    self,
    summary: SummaryAnalysis
) -> str
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `summary` | `SummaryAnalysis` | 汇总分析结果 |

**返回值**:
- **类型**: `str`
- **说明**: Markdown 格式的报告内容

**报告结构**:
```markdown
📊 ARK 全系列基金监控日报
🗓️ {date}

━━━━━━━━━━━━━━━━━━━━━
📈 今日概况
· 总持仓: {total_holdings} 只
· 跨基金重叠: {overlap_count} 只
· 单基金独有: {exclusive_count} 只

🔥 核心持仓 Top 5
1. {ticker} {total_weight}% ({fund_count}基金) {trend}
   {fund1} {weight1}% | {fund2} {weight2}% | ...
   
━━━━━━━━━━━━━━━━━━━━━
📋 各基金快速对比

🚀 ARKK ⭐ {name_cn}
{theme} | {holding_count} 只
Top 3: {ticker1} {weight1}% · {ticker2} {weight2}% · {ticker3} {weight3}%

🌐 ARKW {name_cn}
{theme} | {holding_count} 只
Top 3: ...

━━━━━━━━━━━━━━━━━━━━━
💡 今日亮点
· {highlight1}
· {highlight2}
...

详细报告见长图 👇
```

**字符限制**: ≤ 4096（企业微信限制）

---

### 方法3：_send_markdown（私有）

**功能**: 推送 Markdown 消息到企业微信

**签名**:
```python
def _send_markdown(
    self,
    content: str
) -> bool
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `content` | `str` | Markdown 内容 |

**返回值**:
- **类型**: `bool`
- **说明**: `True` 表示成功

**请求体**:
```json
{
    "msgtype": "markdown",
    "markdown": {
        "content": "..."
    }
}
```

**重试机制**:
- 最多 3 次重试
- 每次间隔 5 秒
- 失败后记录错误日志

---

### 方法4：_send_image（私有）

**功能**: 推送长图到企业微信

**签名**:
```python
def _send_image(
    self,
    image_path: str
) -> bool
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `image_path` | `str` | 长图文件路径 |

**返回值**:
- **类型**: `bool`
- **说明**: `True` 表示成功

**实现**:
1. 读取图片文件
2. Base64 编码
3. 计算 MD5 校验值
4. 构造请求体推送

**请求体**:
```json
{
    "msgtype": "image",
    "image": {
        "base64": "...",
        "md5": "..."
    }
}
```

**限制**:
- 图片大小 ≤ 20MB
- 支持格式：PNG, JPG

---

## 📦 数据模型

### 输入模型

**SummaryAnalysis**: 见 `summary_analyzer.md`

### 输出格式

**Markdown 消息**:
- 类型：`text/markdown`
- 最大长度：4096 字符
- 包含 emoji 和格式化

**图片消息**:
- 格式：PNG
- 最大大小：20MB
- Base64 编码

---

## 🔗 依赖关系

### 内部依赖
- `src.image_generator` - 生成汇总长图
- `src.utils` - 配置加载、日志记录
- `src.summary_analyzer` - 使用 `SummaryAnalysis` 数据模型

### 外部依赖
- `requests` - HTTP 请求
- `base64` - 图片编码
- `hashlib` - MD5 计算
- `logging` - 日志记录

### 被依赖
- `main.py` - 调用 `generate_and_send()`

---

## 🚫 职责边界

### ✅ 负责
- Markdown 报告文本生成
- 调用图片生成器
- 消息推送（Markdown + 图片）
- 推送失败重试
- 推送状态记录

### ❌ 不负责
- 汇总数据分析（由 `summary_analyzer` 负责）
- 长图绘制（由 `image_generator` 负责）
- 单基金报告（由各基金的 `notifier` 负责）
- 数据下载和保存（由 `fetcher` 负责）

---

## 📝 使用示例

```python
from src.summary_notifier import SummaryNotifier
from src.utils import load_config

# 初始化
config = load_config()
webhook_url = os.getenv('WECHAT_WEBHOOK_URL')
notifier = SummaryNotifier(config, webhook_url)

# 生成并推送
success = notifier.generate_and_send(summary, all_holdings)

if success:
    logger.info("✅ 汇总报告推送成功")
else:
    logger.error("❌ 汇总报告推送失败")
```

---

## ⚠️ 注意事项

1. **字符限制**: Markdown 内容必须 ≤ 4096 字符，超过则截断
2. **图片限制**: 长图大小必须 ≤ 20MB，超过则推送失败
3. **推送顺序**: 先推送 Markdown，再推送长图
4. **重试机制**: 仅对网络错误重试，业务错误（如内容过大）不重试
5. **日志记录**: 所有推送操作都记录详细日志

---

## 🎨 Markdown 格式规范

### Emoji 使用

| Emoji | 用途 | 示例 |
|-------|------|------|
| 📊 | 标题 | 📊 ARK 全系列基金监控日报 |
| 🗓️ | 日期 | 🗓️ 2025-11-14 |
| 📈 | 概况 | 📈 今日概况 |
| 🔥 | 核心持仓 | 🔥 核心持仓 Top 5 |
| 📋 | 基金对比 | 📋 各基金快速对比 |
| 💡 | 亮点 | 💡 今日亮点 |
| 🚀 | ARKK | 🚀 ARKK ⭐ 创新 ETF |
| 🌐 | ARKW | 🌐 ARKW 下一代互联网 |
| 🧬 | ARKG | 🧬 ARKG 基因革命 |
| 🤖 | ARKQ | 🤖 ARKQ 自动化科技 |
| 💰 | ARKF | 💰 ARKF 金融创新 |
| ⭐ | 旗舰标记 | ARKK ⭐ |
| 📈 | 增持 | TSLA 被 3 只基金同时增持 📈 |
| 📉 | 减持 | COIN 被 2 只基金同时减持 📉 |
| 🆕 | 新增 | PLTR 从单基金变为跨基金持仓 🆕 |

### 分隔线

使用 `━━━━━━━━━━━━━━━━━━━━━`（全角横线）分隔不同板块。

### 缩进和对齐

```markdown
🔥 核心持仓 Top 5
1. TSLA 33.57% (3基金) 📈
   ARKQ 11.92% | ARKK 11.96% | ARKW 9.69%
```

- 使用空格缩进（3个空格）
- 使用 `|` 分隔多个基金

---

## 🧪 测试要点

### 单元测试
- `test_generate_markdown()` - 测试 Markdown 生成
- `test_markdown_length_limit()` - 测试字符长度截断
- `test_send_markdown_success()` - Mock HTTP 请求成功
- `test_send_markdown_retry()` - 测试重试机制
- `test_send_image_success()` - Mock 图片推送成功
- `test_generate_and_send_full_flow()` - 测试完整流程

### 集成测试
- 使用真实 Webhook 测试推送（需配置测试 URL）
- 验证企业微信中显示的格式正确性

---

**契约状态**: ✅ 已实现  
**测试覆盖率**: 80%+  
**最后审核**: 2025-11-14
