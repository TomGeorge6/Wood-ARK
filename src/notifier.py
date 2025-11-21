"""
企业微信通知模块

通过企业微信 Webhook 发送 Markdown 消息和图片。
"""

import logging
import requests
import time
import base64
import hashlib
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class WeChatNotifier:
    """企业微信通知器"""
    
    def __init__(
        self,
        webhook_url: str,
        max_retries: int = 3,
        retry_delays: List[int] = None
    ):
        """
        初始化通知器
        
        Args:
            webhook_url: 企业微信 Webhook URL
            max_retries: 最大重试次数
            retry_delays: 重试延迟列表（秒）
        """
        self.webhook_url = webhook_url
        self.max_retries = max_retries
        self.retry_delays = retry_delays or [1, 2, 4]
        
        logger.info(f"初始化 WeChatNotifier，最大重试次数: {max_retries}")
    
    def send_markdown(self, content: str, max_length: int = 4096) -> bool:
        """
        发送 Markdown 消息
        
        Args:
            content: Markdown 内容
            max_length: 消息最大长度（企业微信限制 4096 字符）
        
        Returns:
            是否发送成功
        """
        # 检查内容长度
        if len(content) > max_length:
            logger.warning(f"消息内容过长 ({len(content)} 字符)，截断到 {max_length} 字符")
            content = content[:max_length - 100] + "\n\n...\n\n*（内容已截断，详细信息请查看完整报告）*"
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        return self._send_with_retry(payload)
    
    def send_text(self, text: str) -> bool:
        """
        发送纯文本消息
        
        Args:
            text: 文本内容
        
        Returns:
            是否发送成功
        """
        payload = {
            "msgtype": "text",
            "text": {
                "content": text
            }
        }
        
        return self._send_with_retry(payload)
    
    def send_error_alert(self, error_msg: str, etf_symbol: str = "") -> bool:
        """
        发送错误告警消息
        
        Args:
            error_msg: 错误信息
            etf_symbol: ETF 代码（可选）
        
        Returns:
            是否发送成功
        """
        title = f"⚠️ Wood-ARK 错误告警"
        if etf_symbol:
            title += f" - {etf_symbol}"
        
        content = f"{title}\n\n**错误信息**:\n{error_msg}\n\n**时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_markdown(content)
    
    def send_image(self, image_path: str) -> bool:
        """
        发送图片消息
        
        Args:
            image_path: 图片文件路径
        
        Returns:
            是否发送成功
        """
        logger.info(f"准备发送图片: {image_path}")
        
        try:
            # 读取图片文件
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Base64 编码
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # 计算 MD5
            md5 = hashlib.md5(image_data).hexdigest()
            
            payload = {
                "msgtype": "image",
                "image": {
                    "base64": base64_data,
                    "md5": md5
                }
            }
            
            return self._send_with_retry(payload)
        
        except FileNotFoundError:
            logger.error(f"图片文件不存在: {image_path}")
            return False
        except Exception as e:
            logger.error(f"读取图片文件失败: {e}")
            return False
    
    def send_markdown_with_images(
        self,
        markdown_content: str,
        image_paths: List[str]
    ) -> bool:
        """
        发送 Markdown 消息和多张图片
        
        Args:
            markdown_content: Markdown 内容
            image_paths: 图片路径列表
        
        Returns:
            是否全部发送成功
        """
        # 先发送文本
        if not self.send_markdown(markdown_content):
            logger.error("发送 Markdown 消息失败")
            return False
        
        # 发送图片
        success_count = 0
        for image_path in image_paths:
            if self.send_image(image_path):
                success_count += 1
                time.sleep(0.5)  # 避免发送过快
            else:
                logger.warning(f"图片发送失败: {image_path}")
        
        logger.info(f"图片发送完成: {success_count}/{len(image_paths)} 成功")
        return success_count == len(image_paths)
    
    def test_connection(self) -> bool:
        """
        测试 Webhook 连接
        
        Returns:
            连接是否正常
        """
        test_message = "Wood-ARK 测试消息\n\n✅ Webhook 连接正常"
        
        logger.info("测试企业微信 Webhook 连接")
        result = self.send_text(test_message)
        
        if result:
            logger.info("✅ Webhook 测试成功")
        else:
            logger.error("❌ Webhook 测试失败")
        
        return result
    
    def _send_with_retry(self, payload: dict) -> bool:
        """
        带重试机制的发送方法
        
        Args:
            payload: 消息负载
        
        Returns:
            是否发送成功
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"发送企业微信消息（第 {attempt}/{self.max_retries} 次）")
                
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                )
                
                response.raise_for_status()
                
                # 检查企业微信 API 返回
                result = response.json()
                
                if result.get('errcode') == 0:
                    logger.info("✅ 消息发送成功")
                    return True
                else:
                    error_msg = result.get('errmsg', '未知错误')
                    logger.error(f"❌ 企业微信 API 返回错误: {error_msg}")
                    
                    # 某些错误不需要重试（如 Webhook 地址错误）
                    if 'invalid webhook url' in error_msg.lower():
                        logger.error("Webhook URL 无效，停止重试")
                        return False
            
            except requests.RequestException as e:
                logger.error(f"❌ 网络请求失败: {e}")
            
            except Exception as e:
                logger.error(f"❌ 发送消息时发生未知错误: {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries:
                delay = self.retry_delays[min(attempt - 1, len(self.retry_delays) - 1)]
                logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
        
        logger.error(f"❌ 消息发送失败，已重试 {self.max_retries} 次")
        return False
    
    def send_daily_report(
        self,
        etf_symbol: str,
        date: str,
        markdown_content: str
    ) -> bool:
        """
        发送每日报告
        
        Args:
            etf_symbol: ETF 代码
            date: 日期
            markdown_content: 报告内容
        
        Returns:
            是否发送成功
        """
        # 添加标题前缀
        prefixed_content = f"# 📊 {etf_symbol} 持仓变化 ({date})\n\n{markdown_content}"
        
        return self.send_markdown(prefixed_content)
    
    def generate_etf_wechat_markdown(
        self,
        etf_symbol: str,
        date: str,
        prev_date: str,
        curr_date: str,
        analysis_result: dict
    ) -> str:
        """
        生成单个 ETF 的企业微信推送内容
        
        Args:
            etf_symbol: ETF 代码
            date: 日期
            prev_date: 前一日日期
            curr_date: 当前日期
            analysis_result: 分析结果
        
        Returns:
            Markdown 格式的推送内容
        """
        # ETF 基本信息
        etf_info_map = {
            'ARKK': {'name': 'ARK 创新ETF', 'focus': '破坏性创新技术（AI、电动车、太空探索、区块链）', 'emoji': '🚀'},
            'ARKW': {'name': 'ARK 下一代互联网ETF', 'focus': '互联网、云计算、区块链、元宇宙', 'emoji': '🌐'},
            'ARKG': {'name': 'ARK 基因革命ETF', 'focus': '基因编辑、精准医疗、生物科技', 'emoji': '🧬'},
            'ARKQ': {'name': 'ARK 自动化技术ETF', 'focus': '自动驾驶、机器人、航天、3D打印', 'emoji': '🤖'},
            'ARKF': {'name': 'ARK 金融科技ETF', 'focus': '数字支付、区块链、金融创新、去中心化金融', 'emoji': '💰'}
        }
        
        info = etf_info_map.get(etf_symbol, {'name': etf_symbol, 'focus': '', 'emoji': '📊'})
        
        lines = []
        lines.append(f"# {info['emoji']} {etf_symbol} 持仓变化 ({date})")
        lines.append(f"**{info['name']}**")
        lines.append(f"{info['focus']}")
        lines.append("")
        lines.append("## 概览")
        lines.append(f"- 对比日期: {prev_date} → {curr_date}")
        lines.append(f"- 新增: {len(analysis_result['added'])} | 移除: {len(analysis_result['removed'])}")
        lines.append(f"- 增持: {len(analysis_result['increased'])} | 减持: {len(analysis_result['decreased'])}")
        lines.append("")
        lines.append("详细数据请查看下方图表 👇")
        
        return '\n'.join(lines)
