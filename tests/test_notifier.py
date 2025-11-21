"""
测试企业微信推送模块

测试 src/notifier.py 中的 WeChatNotifier 类
"""

import pytest
from unittest.mock import Mock, patch
from src.notifier import WeChatNotifier


# ==================== Fixtures ====================

@pytest.fixture
def webhook_url():
    """测试用 Webhook URL"""
    return "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test-key"


@pytest.fixture
def notifier(webhook_url):
    """创建 WeChatNotifier 实例"""
    return WeChatNotifier(webhook_url, max_retries=3)


# ==================== 测试消息发送 ====================

class TestSendMessage:
    """测试消息发送功能"""
    
    @patch('src.notifier.requests.post')
    def test_send_markdown_success(self, mock_post, notifier):
        """测试成功发送 Markdown 消息"""
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_post.return_value = mock_response
        
        # 发送消息
        content = "# 测试报告\n\n这是一条测试消息"
        result = notifier.send_markdown(content)
        
        # 验证成功
        assert result is True
        
        # 验证请求参数
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # 验证 URL
        assert call_args[0][0] == notifier.webhook_url
        
        # 验证请求体
        json_data = call_args[1]['json']
        assert json_data['msgtype'] == 'markdown'
        assert json_data['markdown']['content'] == content
    
    @patch('src.notifier.requests.post')
    def test_send_markdown_retry_on_failure(self, mock_post, notifier):
        """测试失败后重试"""
        # Mock: 前 2 次失败，第 3 次成功
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.json.return_value = {'errcode': 500, 'errmsg': 'Internal Server Error'}
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        
        mock_post.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]
        
        # 发送消息
        content = "# 测试报告"
        result = notifier.send_markdown(content)
        
        # 验证最终成功
        assert result is True
        
        # 验证重试了 3 次
        assert mock_post.call_count == 3
    
    @patch('src.notifier.requests.post')
    def test_send_markdown_max_retries_exceeded(self, mock_post, notifier):
        """测试超过最大重试次数后失败"""
        # Mock: 所有请求都失败
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'errcode': 500, 'errmsg': 'Internal Server Error'}
        mock_post.return_value = mock_response
        
        # 发送消息
        content = "# 测试报告"
        result = notifier.send_markdown(content)
        
        # 验证失败
        assert result is False
        
        # 验证重试了 3 次
        assert mock_post.call_count == 3
    
    @patch('src.notifier.requests.post')
    def test_send_markdown_with_timeout(self, mock_post, notifier):
        """测试请求超时"""
        # Mock 超时异常
        mock_post.side_effect = Exception("Request timeout")
        
        # 发送消息
        content = "# 测试报告"
        result = notifier.send_markdown(content)
        
        # 验证失败
        assert result is False
        
        # 验证重试了 3 次
        assert mock_post.call_count == 3
    
    @patch('src.notifier.requests.post')
    def test_send_error_alert(self, mock_post, notifier):
        """测试发送错误告警"""
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_post.return_value = mock_response
        
        # 发送错误告警
        error_message = "数据获取失败：网络超时"
        result = notifier.send_error_alert(error_message)
        
        # 验证成功
        assert result is True
        
        # 验证请求体包含错误信息
        call_args = mock_post.call_args
        json_data = call_args[1]['json']
        
        # 错误告警应该是 text 类型或包含错误标识
        assert 'text' in json_data or 'markdown' in json_data
        content = json_data.get('text', {}).get('content') or json_data.get('markdown', {}).get('content')
        assert error_message in content or '错误' in content


# ==================== 测试连接测试 ====================

class TestConnectionTest:
    """测试 Webhook 连接测试"""
    
    @patch('src.notifier.requests.post')
    def test_connection_success(self, mock_post, notifier):
        """测试 Webhook 连接正常"""
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_post.return_value = mock_response
        
        # 测试连接
        result = notifier.test_connection()
        
        # 验证成功
        assert result is True
        
        # 验证发送了测试消息
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        json_data = call_args[1]['json']
        
        # 验证消息内容包含 "测试"
        content = json_data.get('text', {}).get('content') or json_data.get('markdown', {}).get('content', '')
        assert '测试' in content or 'test' in content.lower()
    
    @patch('src.notifier.requests.post')
    def test_connection_failure(self, mock_post, notifier):
        """测试 Webhook 连接失败"""
        # Mock HTTP 响应失败
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'errcode': 404, 'errmsg': 'Not Found'}
        mock_post.return_value = mock_response
        
        # 测试连接
        result = notifier.test_connection()
        
        # 验证失败
        assert result is False


# ==================== 测试参数验证 ====================

class TestParameterValidation:
    """测试参数验证"""
    
    def test_invalid_webhook_url(self):
        """测试无效的 Webhook URL"""
        # 空 URL
        with pytest.raises(ValueError):
            WeChatNotifier("", max_retries=3)
        
        # None
        with pytest.raises(ValueError):
            WeChatNotifier(None, max_retries=3)
    
    def test_invalid_max_retries(self, webhook_url):
        """测试无效的最大重试次数"""
        # 负数
        with pytest.raises(ValueError):
            WeChatNotifier(webhook_url, max_retries=-1)
        
        # 零
        with pytest.raises(ValueError):
            WeChatNotifier(webhook_url, max_retries=0)


# ==================== 测试消息格式 ====================

class TestMessageFormat:
    """测试消息格式"""
    
    @patch('src.notifier.requests.post')
    def test_markdown_message_structure(self, mock_post, notifier):
        """测试 Markdown 消息结构"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_post.return_value = mock_response
        
        content = "# ARK 持仓变化\n\n## ARKK\n- 新增：TSLA"
        notifier.send_markdown(content)
        
        # 验证请求体格式
        call_args = mock_post.call_args
        json_data = call_args[1]['json']
        
        assert 'msgtype' in json_data
        assert json_data['msgtype'] == 'markdown'
        assert 'markdown' in json_data
        assert 'content' in json_data['markdown']
        assert json_data['markdown']['content'] == content
    
    @patch('src.notifier.requests.post')
    def test_text_message_structure(self, mock_post, notifier):
        """测试纯文本消息结构（错误告警）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_post.return_value = mock_response
        
        notifier.send_error_alert("测试错误")
        
        # 验证请求体格式
        call_args = mock_post.call_args
        json_data = call_args[1]['json']
        
        # 错误告警可以是 text 或 markdown 类型
        assert 'msgtype' in json_data
        assert json_data['msgtype'] in ['text', 'markdown']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
