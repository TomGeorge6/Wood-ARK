"""
ARK 全系列基金汇总报告推送生成器

生成卡片式微信推送内容
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class SummaryNotifier:
    """汇总报告推送内容生成器"""
    
    def generate_wechat_markdown(self, summary_result: dict) -> str:
        """
        生成企业微信 Markdown 推送内容（卡片式）
        
        Args:
            summary_result: 汇总分析结果
        
        Returns:
            Markdown 格式的推送内容
        """
        date = summary_result['date']
        stats = summary_result['statistics']
        summaries = summary_result['etf_summaries']
        overlapping = summary_result['overlapping_stocks']
        changes = summary_result.get('top_changes', [])
        
        # 构建 Markdown
        lines = []
        
        # 标题
        lines.append("# 📊 ARK 全系列基金监控日报")
        lines.append(f"## 🗓️ {date}")
        lines.append("")
        
        # 分隔线
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        
        # 今日概况
        lines.append("### 📈 今日概况")
        
        total_change = self._calculate_total_change(summaries)
        lines.append(f"· 总持仓: **{stats['total_stocks']} 只** {total_change}")
        lines.append(f"· 跨基金重叠: **{stats['overlapping_count']} 只**")
        lines.append(f"· 单基金独有: **{stats['exclusive_count']} 只**")
        
        # 如果有新增重叠股票
        new_overlap_changes = [c for c in changes if c['type'] in ['new_overlap', 'new_multi']]
        if new_overlap_changes:
            change = new_overlap_changes[0]
            lines.append(f"· 🆕 新增重叠: **{change['ticker']}** {change['description']}")
        
        lines.append("")
        
        # 分隔线
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        
        # 核心持仓 Top 5
        lines.append("### 🔥 核心持仓 Top 5")
        
        for i, stock in enumerate(overlapping[:5], 1):
            ticker = stock['ticker']
            company = stock['company'][:15]
            num_funds = stock['num_funds']
            total_weight = stock['total_weight']
            
            # 查找是否有变化
            change_icon = self._get_change_icon(ticker, changes)
            
            lines.append(
                f"{i}. **{ticker}** {total_weight:.2f}% "
                f"({num_funds}基金) {change_icon}"
            )
            
            # 显示分布
            dist = ' | '.join([
                f"{h['etf']} {h['weight']:.1f}%" 
                for h in stock['holdings'][:2]
            ])
            lines.append(f"   {dist}")
        
        lines.append("")
        
        # 分隔线
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        
        # 各基金快速对比
        lines.append("### 📋 各基金快速对比")
        lines.append("")
        
        for etf_symbol in ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']:
            if etf_symbol not in summaries:
                continue
            
            summary = summaries[etf_symbol]
            info = summary['info']
            holdings_count = summary['holdings_count']
            top_holdings = summary['top_holdings'][:10]
            
            flag = ' ⭐' if info.is_flagship else ''
            
            # 计算持仓数变化（如果有）
            count_change = self._get_holdings_count_change(etf_symbol, summaries)
            
            lines.append(f"**{info.emoji} {etf_symbol}{flag}** {info.name_cn}")
            lines.append(f"{info.focus[:30]}... | {holdings_count} 只 {count_change}")
            
            # Top 10
            top10_str = ' · '.join([
                f"{h.get('ticker', 'N/A')} {h.get('weight', 0):.1f}%"
                for h in top_holdings
            ])
            lines.append(f"Top 10: {top10_str}")
            lines.append("")
        
        # 分隔线
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        
        # 今日亮点
        if changes:
            lines.append("### 💡 今日亮点")
            
            for change in changes[:3]:  # 显示前3条
                icon = self._get_change_type_icon(change['type'])
                ticker = change['ticker']
                desc = change['description']
                lines.append(f"· {icon} **{ticker}** - {desc}")
            
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━")
        
        # 底部提示
        lines.append("")
        lines.append("详细报告见长图 👇")
        
        return '\n'.join(lines)
    
    def _calculate_total_change(self, summaries: dict) -> str:
        """计算总持仓数变化（占位符，需要历史数据）"""
        # TODO: 实现历史数据对比
        return ""
    
    def _get_change_icon(self, ticker: str, changes: list) -> str:
        """获取股票变化图标"""
        for change in changes:
            if change['ticker'] == ticker:
                if change['type'] == 'multi_increase':
                    return '📈'
                elif change['type'] == 'multi_decrease':
                    return '📉'
                elif change['type'] in ['new_overlap', 'new_multi']:
                    return '🆕'
        return ''
    
    def _get_holdings_count_change(self, etf: str, summaries: dict) -> str:
        """获取持仓数变化（占位符）"""
        # TODO: 实现历史数据对比
        return ""
    
    def _get_change_type_icon(self, change_type: str) -> str:
        """获取变化类型图标"""
        icons = {
            'multi_increase': '📈',
            'multi_decrease': '📉',
            'new_overlap': '🔄',
            'new_multi': '⭐',
            'removed_multi': '❌'
        }
        return icons.get(change_type, '•')
