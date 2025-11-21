"""
Markdown 报告生成模块

根据持仓分析结果生成格式化的 Markdown 报告。
"""

import logging
from typing import Dict, List
from pathlib import Path
from src.analyzer import ChangedHolding
from src.utils import ensure_dir

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Markdown 报告生成器"""
    
    def __init__(self, data_dir: str = "./data"):
        """
        初始化报告生成器
        
        Args:
            data_dir: 数据存储根目录
        """
        self.data_dir = Path(data_dir)
        self.report_dir = self.data_dir / "reports"
        ensure_dir(str(self.report_dir))
        logger.info(f"初始化 ReportGenerator，报告目录: {self.report_dir}")
    
    def generate_markdown(
        self,
        analysis_result: Dict,
        etf_symbol: str,
        current_holdings: List[Dict] = None
    ) -> str:
        """
        生成 Markdown 格式报告
        
        Args:
            analysis_result: Analyzer.compare_holdings() 返回的分析结果
            etf_symbol: ETF 代码（如 ARKK）
            current_holdings: 当前完整持仓列表（可选，用于生成完整持仓表）
        
        Returns:
            Markdown 格式的报告内容
        """
        logger.info(f"开始生成 {etf_symbol} 的 Markdown 报告")
        
        prev_date = analysis_result['prev_date']
        curr_date = analysis_result['curr_date']
        
        # 构建报告各部分
        sections = [
            self._generate_header(etf_symbol, curr_date),
            self._generate_summary(analysis_result, prev_date, curr_date),
            self._generate_added_section(analysis_result['added']),
            self._generate_removed_section(analysis_result['removed']),
            self._generate_increased_section(analysis_result['significant_increased']),
            self._generate_decreased_section(analysis_result['significant_decreased']),
        ]
        
        # 如果提供了完整持仓，添加完整持仓表
        if current_holdings:
            sections.append(self._generate_full_holdings(current_holdings))
        
        report = "\n\n".join(sections)
        
        logger.info(f"Markdown 报告生成完成，长度: {len(report)} 字符")
        return report
    
    def save_report(self, content: str, etf_symbol: str, date: str) -> str:
        """
        保存报告到文件
        
        Args:
            content: 报告内容
            etf_symbol: ETF 代码
            date: 日期（YYYY-MM-DD）
        
        Returns:
            保存的文件路径
        """
        etf_dir = self.report_dir / etf_symbol
        ensure_dir(str(etf_dir))
        
        file_path = etf_dir / f"{date}.md"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"报告已保存: {file_path}")
        return str(file_path)
    
    def _generate_header(self, etf_symbol: str, date: str) -> str:
        """生成报告标题"""
        return f"# {etf_symbol} 持仓变化 ({date})"
    
    def _generate_summary(self, analysis: Dict, prev_date: str, curr_date: str) -> str:
        """生成概览部分"""
        stats = {
            'added': len(analysis['added']),
            'removed': len(analysis['removed']),
            'increased': len(analysis['increased']),
            'decreased': len(analysis['decreased']),
            'sig_increased': len(analysis['significant_increased']),
            'sig_decreased': len(analysis['significant_decreased']),
        }
        
        return f"""## 📊 概览

- **对比日期**: {prev_date} → {curr_date}
- **新增持仓**: {stats['added']} 只
- **移除持仓**: {stats['removed']} 只
- **增持**: {stats['increased']} 只（显著增持 {stats['sig_increased']} 只）
- **减持**: {stats['decreased']} 只（显著减持 {stats['sig_decreased']} 只）
- **未变化**: {analysis['unchanged']} 只"""
    
    def _generate_added_section(self, added: List[ChangedHolding]) -> str:
        """生成新增持仓部分"""
        if not added:
            return "## ✅ 新增持仓\n\n暂无新增持仓"
        
        rows = []
        for i, holding in enumerate(added, 1):
            shares_str = self._format_number(holding.curr_shares)
            weight_str = f"{holding.curr_weight:.2f}%"
            company_short = holding.company[:30]
            
            rows.append(
                f"{i}. **{holding.ticker}** {company_short}\n"
                f"   持仓: {shares_str} | 权重: {weight_str}"
            )
        
        rows_text = '\n\n'.join(rows)
        return f"## ✅ 新增持仓\n\n{rows_text}"
    
    def _generate_removed_section(self, removed: List[ChangedHolding]) -> str:
        """生成移除持仓部分"""
        if not removed:
            return "## ❌ 移除持仓\n\n暂无移除持仓"
        
        rows = []
        for i, holding in enumerate(removed, 1):
            shares_str = self._format_number(holding.prev_shares)
            weight_str = f"{holding.prev_weight:.2f}%"
            company_short = holding.company[:30]
            
            rows.append(
                f"{i}. **{holding.ticker}** {company_short}\n"
                f"   原持仓: {shares_str} | 原权重: {weight_str}"
            )
        
        rows_text = '\n\n'.join(rows)
        return f"## ❌ 移除持仓\n\n{rows_text}"
    
    def _generate_increased_section(self, increased: List[ChangedHolding]) -> str:
        """生成显著增持部分"""
        if not increased:
            return "## 📈 显著增持\n\n暂无显著增持"
        
        rows = []
        for i, holding in enumerate(increased, 1):
            change_str = f"+{holding.weight_change:.2f}%"
            prev_str = f"{holding.prev_weight:.2f}%"
            curr_str = f"{holding.curr_weight:.2f}%"
            company_short = holding.company[:30]
            
            rows.append(
                f"{i}. **{holding.ticker}** {company_short}\n"
                f"   变化: {change_str} ({prev_str} → {curr_str})"
            )
        
        rows_text = '\n\n'.join(rows)
        return f"## 📈 显著增持\n\n{rows_text}"
    
    def _generate_decreased_section(self, decreased: List[ChangedHolding]) -> str:
        """生成显著减持部分"""
        if not decreased:
            return "## 📉 显著减持\n\n暂无显著减持"
        
        rows = []
        for i, holding in enumerate(decreased, 1):
            change_str = f"{holding.weight_change:.2f}%"
            prev_str = f"{holding.prev_weight:.2f}%"
            curr_str = f"{holding.curr_weight:.2f}%"
            company_short = holding.company[:30]
            
            rows.append(
                f"{i}. **{holding.ticker}** {company_short}\n"
                f"   变化: {change_str} ({prev_str} → {curr_str})"
            )
        
        rows_text = '\n\n'.join(rows)
        return f"## 📉 显著减持\n\n{rows_text}"
    
    def _generate_full_holdings(self, holdings: List[Dict]) -> str:
        """生成完整持仓表（可选）"""
        if not holdings:
            return ""
        
        # 按权重排序
        sorted_holdings = sorted(holdings, key=lambda x: x['weight'], reverse=True)
        
        rows = []
        for i, holding in enumerate(sorted_holdings[:20], 1):  # 只显示前 20 个
            shares_str = self._format_number(holding['shares'])
            value_str = self._format_currency(holding['market_value'])
            weight_str = f"{holding['weight']:.2f}%"
            company_short = holding['company'][:30]  # 限制公司名长度
            
            # 使用更紧凑的列表格式
            rows.append(
                f"{i}. **{holding['ticker']}** {company_short}\n"
                f"   持仓: {shares_str} | 市值: {value_str} | 权重: {weight_str}"
            )
        
        rows_text = '\n\n'.join(rows)
        return f"## 📋 完整持仓（前20）\n\n{rows_text}"
    
    def _format_number(self, num: float) -> str:
        """格式化数字（使用 K/M 单位）"""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return f"{num:.0f}"
    
    def _format_currency(self, amount: float) -> str:
        """格式化货币（美元）"""
        if amount >= 1_000_000_000:
            return f"${amount / 1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"${amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount / 1_000:.1f}K"
        else:
            return f"${amount:.0f}"
