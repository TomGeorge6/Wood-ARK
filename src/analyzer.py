"""
ARK ETF 持仓变化分析模块

分析两个日期之间的持仓变化，识别新增、移除、增持、减持等情况。
"""

import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)


# ==================== 数据类定义 ====================

@dataclass
class ChangeAnalysis:
    """持仓变化分析结果"""
    etf_symbol: str                    # ETF 代码
    current_date: str                  # 当前日期
    previous_date: str                 # 前一日期
    added: List[Dict]                  # 新增持仓列表
    removed: List[Dict]                # 移除持仓列表
    increased: List[Dict]              # 增持列表
    decreased: List[Dict]              # 减持列表


class ChangedHolding:
    """持仓变化记录"""
    
    def __init__(
        self,
        ticker: str,
        company: str,
        prev_shares: float = 0.0,
        curr_shares: float = 0.0,
        prev_weight: float = 0.0,
        curr_weight: float = 0.0,
        change_type: str = "",  # 'added', 'removed', 'increased', 'decreased'
        weight_change: float = 0.0
    ):
        self.ticker = ticker
        self.company = company
        self.prev_shares = prev_shares
        self.curr_shares = curr_shares
        self.prev_weight = prev_weight
        self.curr_weight = curr_weight
        self.change_type = change_type
        self.weight_change = weight_change
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'ticker': self.ticker,
            'company': self.company,
            'prev_shares': self.prev_shares,
            'curr_shares': self.curr_shares,
            'prev_weight': self.prev_weight,
            'curr_weight': self.curr_weight,
            'change_type': self.change_type,
            'weight_change': self.weight_change
        }


class Analyzer:
    """持仓变化分析器"""
    
    def __init__(self, threshold: float = 5.0):
        """
        初始化分析器
        
        Args:
            threshold: 显著变化阈值（百分比），默认 5%
        """
        self.threshold = threshold
        logger.info(f"初始化 Analyzer，显著变化阈值: {threshold}%")
    
    def compare_holdings(
        self,
        current_df: pd.DataFrame,
        previous_df: pd.DataFrame,
        prev_date: str,
        curr_date: str
    ) -> Dict:
        """
        对比两个日期的持仓变化
        
        Args:
            current_df: 当前日期的持仓数据
            previous_df: 前一日期的持仓数据
            prev_date: 前一日期（YYYY-MM-DD）
            curr_date: 当前日期（YYYY-MM-DD）
        
        Returns:
            分析结果字典，包含：
            - prev_date: 前一日期
            - curr_date: 当前日期
            - added: 新增持仓列表
            - removed: 移除持仓列表
            - increased: 增持列表
            - decreased: 减持列表
            - significant_increased: 显著增持列表
            - significant_decreased: 显著减持列表
            - unchanged: 未变化持仓数量
        """
        logger.info(f"开始对比持仓变化: {prev_date} → {curr_date}")
        
        # 确保数据格式正确
        current_df = self._ensure_dataframe_format(current_df)
        previous_df = self._ensure_dataframe_format(previous_df)
        
        # 创建 ticker 到行的映射
        prev_holdings = {row['ticker']: row for _, row in previous_df.iterrows()}
        curr_holdings = {row['ticker']: row for _, row in current_df.iterrows()}
        
        prev_tickers = set(prev_holdings.keys())
        curr_tickers = set(curr_holdings.keys())
        
        # 分类持仓变化
        added_tickers = curr_tickers - prev_tickers
        removed_tickers = prev_tickers - curr_tickers
        common_tickers = prev_tickers & curr_tickers
        
        # 新增持仓
        added = [
            ChangedHolding(
                ticker=ticker,
                company=curr_holdings[ticker]['company'],
                curr_shares=curr_holdings[ticker]['shares'],
                curr_weight=curr_holdings[ticker]['weight'],
                change_type='added'
            )
            for ticker in added_tickers
        ]
        
        # 移除持仓
        removed = [
            ChangedHolding(
                ticker=ticker,
                company=prev_holdings[ticker]['company'],
                prev_shares=prev_holdings[ticker]['shares'],
                prev_weight=prev_holdings[ticker]['weight'],
                change_type='removed'
            )
            for ticker in removed_tickers
        ]
        
        # 分析权重变化
        increased = []
        decreased = []
        unchanged_count = 0
        
        for ticker in common_tickers:
            prev_row = prev_holdings[ticker]
            curr_row = curr_holdings[ticker]
            
            prev_weight = prev_row['weight']
            curr_weight = curr_row['weight']
            weight_change = curr_weight - prev_weight
            
            if abs(weight_change) < 0.01:  # 变化小于 0.01% 视为未变化
                unchanged_count += 1
                continue
            
            changed = ChangedHolding(
                ticker=ticker,
                company=curr_row['company'],
                prev_shares=prev_row['shares'],
                curr_shares=curr_row['shares'],
                prev_weight=prev_weight,
                curr_weight=curr_weight,
                weight_change=weight_change
            )
            
            if weight_change > 0:
                changed.change_type = 'increased'
                increased.append(changed)
            else:
                changed.change_type = 'decreased'
                decreased.append(changed)
        
        # 按权重变化幅度排序
        increased.sort(key=lambda x: x.weight_change, reverse=True)
        decreased.sort(key=lambda x: x.weight_change)
        
        # 筛选显著变化
        significant_increased = [h for h in increased if h.weight_change >= self.threshold]
        significant_decreased = [h for h in decreased if abs(h.weight_change) >= self.threshold]
        
        result = {
            'prev_date': prev_date,
            'curr_date': curr_date,
            'added': added,
            'removed': removed,
            'increased': increased,
            'decreased': decreased,
            'significant_increased': significant_increased,
            'significant_decreased': significant_decreased,
            'unchanged': unchanged_count
        }
        
        logger.info(
            f"对比完成: 新增 {len(added)}, 移除 {len(removed)}, "
            f"增持 {len(increased)}, 减持 {len(decreased)}, "
            f"显著增持 {len(significant_increased)}, 显著减持 {len(significant_decreased)}, "
            f"未变化 {unchanged_count}"
        )
        
        return result
    
    def _ensure_dataframe_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """确保 DataFrame 格式正确"""
        required_cols = ['company', 'ticker', 'shares', 'market_value', 'weight']
        
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame 缺少必需字段，需要: {required_cols}")
        
        # 确保数值类型正确
        df = df.copy()
        df['shares'] = pd.to_numeric(df['shares'], errors='coerce')
        df['market_value'] = pd.to_numeric(df['market_value'], errors='coerce')
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
        
        return df
    
    def get_summary_stats(self, analysis_result: Dict) -> Dict:
        """
        获取变化摘要统计
        
        Args:
            analysis_result: compare_holdings() 返回的结果
        
        Returns:
            统计信息字典
        """
        return {
            'total_added': len(analysis_result['added']),
            'total_removed': len(analysis_result['removed']),
            'total_increased': len(analysis_result['increased']),
            'total_decreased': len(analysis_result['decreased']),
            'significant_increased': len(analysis_result['significant_increased']),
            'significant_decreased': len(analysis_result['significant_decreased']),
            'unchanged': analysis_result['unchanged'],
            'threshold': self.threshold
        }
