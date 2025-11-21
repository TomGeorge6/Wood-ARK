# Module Contract: WeChatNotifier

**Module**: `src/notifier.py`  
**Purpose**: 负责通过企业微信 Webhook 推送 Markdown 消息

---

## Class Definition

```python
class WeChatNotifier:
    """企业微信消息推送器"""
    
    def __init__(self, webhook_url: str, max_retries: int = 3, retry_delay: int = 5):
        """初始化 WeChatNotifier
        
        Args:
            webhook_url: 企业微信 Webhook URL
            max_retries: 最大重试次数（默认 3）
            retry_delay: 重试间隔（秒，默认 5）
        """
        self.webhook_url = webhook_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
```

---

## Public Methods

### 1. send_markdown()

**签名**:

```python
def send_markdown(self, content: str) -> bool:
    """发送 Markdown 消息到企业微信
    
    Args:
        content: Markdown 文本内容（≤4096 字符）
        
    Returns:
        True: 推送成功
        False: 推送失败（重试 max_retries 次后仍失败）
        
    Request Body:
        {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
    Success Response (HTTP 200):
        {
            "errcode": 0,
            "errmsg": "ok"
        }
        
    Error Response (HTTP 200):
        {
            "errcode": 93000,
            "errmsg": "invalid webhook url"
        }
        
    Retry Strategy:
        - 最多重试 max_retries 次
        - 每次间隔 retry_delay 秒（固定间隔，非指数退避）
        - 仅在网络错误时重试（errcode ≠ 0 不重试）
        
    Implementation Details:
        1. 构造请求体 JSON
        2. 发送 POST 请求
        3. 检查 HTTP 状态码
        4. 检查响应 JSON 的 errcode
        5. 如 errcode=0，返回 True
        6. 如网络错误，等待后重试
        7. 如 errcode ≠ 0（如 URL 无效），记录错误并返回 False
    """
    pass
```

**Example Usage**:

```python
notifier = WeChatNotifier(
    webhook_url=config.notification.webhook_url,
    max_retries=3,
    retry_delay=5
)

markdown = "## 🚀 测试消息\n\n- 第一项\n- 第二项"
success = notifier.send_markdown(markdown)

if success:
    print("✅ 推送成功")
else:
    print("❌ 推送失败")
```

---

### 2. send_error_alert()

**签名**:

```python
def send_error_alert(self, error_message: str, context: dict = None) -> bool:
    """发送错误告警到企业微信（可选功能）
    
    Args:
        error_message: 错误描述
        context: 上下文信息（如 ETF 名称、日期等）
        
    Returns:
        True: 推送成功
        False: 推送失败或未启用错误告警
        
    Message Format:
        ⚠️ ARK 监控系统错误
        
        **错误类型**: CSV 下载失败
        **ETF**: ARKK
        **日期**: 2025-01-15
        **详情**: requests.Timeout: 连接超时
        
        请检查网络连接或 ARK 官网状态。
        
    Implementation Details:
        1. 检查配置中是否启用错误告警
        2. 如未启用，直接返回 False
        3. 如启用，格式化错误消息
        4. 调用 send_markdown() 推送
    """
    pass
```

**Example Usage**:

```python
notifier = WeChatNotifier(webhook_url, max_retries=3)

try:
    df = fetcher.fetch_holdings('ARKK', '2025-01-15')
except requests.Timeout as e:
    notifier.send_error_alert(
        error_message=str(e),
        context={
            'etf': 'ARKK',
            'date': '2025-01-15',
            'error_type': 'CSV 下载失败'
        }
    )
```

---

### 3. test_connection()

**签名**:

```python
def test_connection(self) -> bool:
    """测试 Webhook 连接是否正常
    
    Returns:
        True: 连接正常
        False: 连接失败
        
    Test Message:
        {
            "msgtype": "text",
            "text": {
                "content": "Wood-ARK 监控系统测试消息 ✅"
            }
        }
        
    Implementation Details:
        1. 发送简单的文本消息（非 Markdown）
        2. 检查响应 errcode
        3. 记录测试结果到日志
    """
    pass
```

**Example Usage**:

```python
notifier = WeChatNotifier(webhook_url)

if notifier.test_connection():
    print("✅ Webhook 连接正常")
else:
    print("❌ Webhook 连接失败，请检查 URL")
```

---

## Private Methods

### _build_request_payload()

```python
def _build_request_payload(
    self, 
    content: str, 
    msgtype: str = 'markdown'
) -> dict:
    """构造请求体
    
    Args:
        content: 消息内容
        msgtype: 消息类型（'markdown' 或 'text'）
        
    Returns:
        {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
        或
        {
            "msgtype": "text",
            "text": {"content": content}
        }
    """
    if msgtype == 'markdown':
        return {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
    elif msgtype == 'text':
        return {
            "msgtype": "text",
            "text": {"content": content}
        }
    else:
        raise ValueError(f"不支持的消息类型: {msgtype}")
```

### _send_request()

```python
def _send_request(self, payload: dict) -> tuple[bool, str]:
    """发送 HTTP POST 请求
    
    Args:
        payload: 请求体 JSON
        
    Returns:
        (success, error_message) 元组
        - success: True/False
        - error_message: 失败原因（成功时为空字符串）
        
    Implementation Details:
        1. 发送 POST 请求（timeout=10 秒）
        2. 检查 HTTP 状态码
        3. 解析响应 JSON
        4. 返回结果
    """
    try:
        response = requests.post(
            self.webhook_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        result = response.json()
        errcode = result.get('errcode', -1)
        
        if errcode == 0:
            return True, ""
        else:
            errmsg = result.get('errmsg', 'Unknown error')
            return False, f"errcode={errcode}, errmsg={errmsg}"
    
    except requests.RequestException as e:
        return False, str(e)
```

### _format_error_alert()

```python
def _format_error_alert(
    self, 
    error_message: str, 
    context: dict = None
) -> str:
    """格式化错误告警消息
    
    Returns:
        ⚠️ ARK 监控系统错误
        
        **错误类型**: CSV 下载失败
        **ETF**: ARKK
        **日期**: 2025-01-15
        **详情**: requests.Timeout: 连接超时
    """
    lines = ["⚠️ **ARK 监控系统错误**", ""]
    
    if context:
        if 'error_type' in context:
            lines.append(f"**错误类型**: {context['error_type']}")
        if 'etf' in context:
            lines.append(f"**ETF**: {context['etf']}")
        if 'date' in context:
            lines.append(f"**日期**: {context['date']}")
    
    lines.append(f"**详情**: {error_message}")
    lines.append("")
    lines.append("请检查网络连接或 ARK 官网状态。")
    
    return "\n".join(lines)
```

---

## Error Handling

### 网络超时

```python
try:
    success = notifier.send_markdown(content)
except requests.Timeout:
    logger.error("企业微信推送超时")
    # 系统已内置重试机制，无需手动重试
```

### Webhook URL 无效

```python
success = notifier.send_markdown(content)
if not success:
    logger.error("推送失败，请检查 Webhook URL 是否正确")
    # 保存报告到本地
    reporter.save_report(content, etf, date, failed=True)
```

### 消息过长

```python
if len(content) > 4096:
    logger.warning("消息超过 4096 字符，已自动截断")
    content = content[:4093] + "..."

success = notifier.send_markdown(content)
```

---

## Testing

```python
# tests/test_notifier.py

def test_send_markdown_success(mocker):
    """测试成功推送"""
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
    
    notifier = WeChatNotifier('https://qyapi.weixin.qq.com/test')
    success = notifier.send_markdown("# Test")
    
    assert success is True
    assert mock_post.call_count == 1

def test_send_markdown_retry(mocker):
    """测试重试机制"""
    mock_post = mocker.patch('requests.post')
    mock_post.side_effect = [
        requests.Timeout(),  # 第1次失败
        requests.Timeout(),  # 第2次失败
        mocker.Mock(status_code=200, json=lambda: {'errcode': 0})  # 第3次成功
    ]
    
    notifier = WeChatNotifier('https://qyapi.weixin.qq.com/test', max_retries=3)
    success = notifier.send_markdown("# Test")
    
    assert success is True
    assert mock_post.call_count == 3

def test_send_markdown_invalid_url(mocker):
    """测试 URL 无效场景"""
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        'errcode': 93000,
        'errmsg': 'invalid webhook url'
    }
    
    notifier = WeChatNotifier('https://qyapi.weixin.qq.com/test')
    success = notifier.send_markdown("# Test")
    
    assert success is False
    assert mock_post.call_count == 1  # URL 无效不重试

def test_test_connection(mocker):
    """测试连接测试功能"""
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'errcode': 0}
    
    notifier = WeChatNotifier('https://qyapi.weixin.qq.com/test')
    result = notifier.test_connection()
    
    assert result is True
    
    # 验证发送的是文本消息
    call_args = mock_post.call_args
    payload = call_args[1]['json']
    assert payload['msgtype'] == 'text'
    assert 'Wood-ARK' in payload['text']['content']
```

---

## API Rate Limits

企业微信群机器人 Webhook API 限制：
- **频率限制**: 20 次/分钟
- **字符限制**: 4096 字符/消息
- **并发限制**: 无明确限制

**应对策略**:
- ✅ 本项目每天仅推送 1 次，远低于频率限制
- ✅ ReportGenerator 已实现字符长度控制
- ✅ 无需实现并发控制

---

## Security Considerations

### Webhook URL 保护

```python
# ❌ 错误：硬编码 Webhook URL
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=abc123"

# ✅ 正确：从环境变量读取
import os
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv('WECHAT_WEBHOOK_URL')
```

### 日志脱敏

```python
# 日志中仅显示 URL 前缀，隐藏 key 参数
masked_url = self.webhook_url[:50] + "***"
logger.info(f"推送到: {masked_url}")
```

---

## Dependencies

- **requests**: HTTP 请求
- **logging**: 日志记录
- **time**: 重试延迟

---

## Performance Considerations

- **推送时间**: 单次请求 <3 秒（正常网络）
- **重试开销**: 最多 3 次 × 5 秒延迟 = 15 秒
- **内存占用**: ~5KB（请求/响应 JSON）

---

**Contract Status**: ✅ Defined | **Last Updated**: 2025-11-13
