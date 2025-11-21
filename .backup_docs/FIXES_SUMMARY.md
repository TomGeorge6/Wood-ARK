# Wood-ARK 问题修复总结 (2025-11-14)

## 发现的3个问题及修复方案

### ❌ 问题1：日期时区不一致

**现象**：
- 汇总报告显示：`2025-11-13`（美国时间）
- 单基金报告显示：`2025-11-14`（北京时间）

**原因分析**：
- ARK Funds 是美国基金，其数据更新按美国东部时间（ET）
- 北京时间比美国东部时间快 13 小时（冬令时）
- 原代码使用 `datetime.now()` 获取系统时区，导致不一致

**修复方案**：
修改 `src/utils.py` 中的 `get_current_date()` 函数，统一使用美国东部时间（ET）

```python
def get_current_date() -> str:
    """获取当前日期（美国东部时间）"""
    try:
        from zoneinfo import ZoneInfo
        et_tz = ZoneInfo("America/New_York")
        et_now = datetime.now(et_tz)
        return et_now.strftime('%Y-%m-%d')
    except ImportError:
        # 备用方案：UTC-5
        utc_now = datetime.utcnow()
        et_now = utc_now - timedelta(hours=5)
        return et_now.strftime('%Y-%m-%d')
```

**影响**：
- 所有日期统一为美国东部时间
- 建议在北京时间晚上执行任务（对应美国早上）

---

### ❌ 问题2："显著增持"逻辑不符合预期

**现象**：
用户反馈"显著增持: 0 | 显著减持: 0"，无法看到所有变化

**原因分析**：
- 代码中使用了 `threshold = 5%` 的阈值
- 只显示权重变化 > 5% 的股票
- 用户希望看到**所有**新增/移除/增持/减持的股票

**修复方案**：
修改 `src/notifier.py` 中的 `generate_etf_wechat_markdown()` 方法

```python
# 修改前
lines.append(f"- 显著增持: {len(analysis_result['significant_increased'])} | 显著减持: {len(analysis_result['significant_decreased'])}")

# 修改后
lines.append(f"- 增持: {len(analysis_result['increased'])} | 减持: {len(analysis_result['decreased'])}")
```

**说明**：
- `increased` / `decreased`：所有有变化的股票（>0.01%）
- `significant_increased` / `significant_decreased`：显著变化的股票（>5%）
- 图表中仍会标注哪些是显著变化

---

### ⚠️ 问题3：图片未发送（严重）

**现象**：
- 企业微信只收到文字消息，没有收到图片
- 日志显示错误：`errcode: 40009`

**原因分析**：
1. **图片尺寸过大**：
   - 拼接后的长图：1788 x 30120 像素，2.6MB
   - 企业微信限制：图片最大 10MB，但建议 < 2MB
   - 企业微信对超长图片支持不佳

2. **错误代码 40009**：
   - 根据企业微信文档，40009 通常表示 `invalid image size`
   - 图片高度超过 30000px 可能被拒绝

3. **Base64 编码问题**：
   - 超大图片 Base64 编码后更大（约 3.5MB）
   - 可能超过 POST 请求体大小限制

**修复方案（3选1）**：

#### 方案A：分批发送图片（推荐）

不拼接图片，分批发送：
- 消息1：汇总文字 + 各基金摘要（超长文字）
- 消息2：汇总长图
- 消息3-7：各基金长图（5张）

**优点**：
- 图片分别发送，稳定性高
- 单张图片 < 500KB，加载快
- 支持查看单个基金详情

**缺点**：
- 需要发送 7 条消息（比原方案多 1 条）

#### 方案B：压缩拼接图片

保持拼接，但优化压缩：
- 降低 DPI：150 → 100
- 使用 JPEG 格式（有损压缩）
- 压缩质量：85%

**预期效果**：
- 图片大小：2.6MB → 800KB
- 清晰度略有下降，但可接受

**缺点**：
- 仍可能遇到高度限制
- 手机端加载较慢

#### 方案C：拆分为2张长图

拼接为2张图片：
- 图片1：汇总 + 前3个基金（ARKK, ARKW, ARKG）
- 图片2：后2个基金（ARKQ, ARKF）

**优点**：
- 单张图片高度 < 15000px
- 文件大小 < 1.5MB

**缺点**：
- 需要发送 3 条消息

---

## 推荐解决方案

### 综合建议：**方案A（分批发送）**

理由：
1. 最稳定，不会遇到图片大小限制
2. 用户可单独查看感兴趣的基金
3. 加载速度快，用户体验好

### 实现步骤

1. **修改 `main.py` 推送逻辑**：

```python
# === 推送1：汇总文字（包含各基金摘要）===
combined_text = generate_combined_markdown(...)
notifier.send_markdown(combined_text)

# === 推送2：汇总长图 ===
summary_image = image_gen.generate_summary_report_image(...)
notifier.send_image(summary_image)

# === 推送3-7：各基金长图 ===
for etf in ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']:
    etf_image = all_etf_images[etf][0]
    notifier.send_image(etf_image)
    time.sleep(0.5)  # 避免发送过快
```

2. **添加消息间延迟**：
   - 每条消息间隔 0.5-1 秒
   - 避免触发企业微信频率限制

3. **错误处理**：
   - 任一图片发送失败，记录日志但继续发送
   - 最后汇总成功/失败数量

---

## 其他发现

### 企业微信 API 限制

- **图片格式**：PNG, JPG, GIF
- **图片大小**：< 10MB（建议 < 2MB）
- **图片尺寸**：建议 < 20000px（高度+宽度）
- **发送频率**：建议间隔 > 0.5 秒

### 错误代码参考

- `40009`: 图片大小/格式/尺寸不符合要求
- `45001`: 图片过大（> 10MB）
- `45009`: 接口调用超过限制

---

## 下一步操作

1. **立即修复**：
   - ✅ 问题1：日期时区（已修复）
   - ✅ 问题2：显示逻辑（已修复）
   - ⏳ 问题3：分批发送图片（需要重构）

2. **测试验证**：
   ```bash
   python main.py --manual
   ```

3. **监控日志**：
   ```bash
   tail -f logs/wood_ark.log | grep -E "(发送|image)"
   ```

---

**更新时间**: 2025-11-14 14:40  
**修复状态**: 2/3 完成，问题3需要重构推送逻辑
