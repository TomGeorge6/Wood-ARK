"""
ARK 全系列基金汇总分析器

功能：
1. 汇总所有基金的持仓数据
2. 发现跨基金重叠股票
3. 分析各基金独家持仓
4. 对比昨日变化
"""

import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ETFInfo:
    """ETF 基本信息"""
    symbol: str
    name_cn: str
    name_en: str
    focus: str
    emoji: str
    is_flagship: bool = False


# ARK ETF 信息映射
ETF_INFO_MAP = {
    'ARKK': ETFInfo(
        symbol='ARKK',
        name_cn='创新 ETF',
        name_en='ARK Innovation ETF',
        focus='破坏性创新技术（AI、电动车、太空探索、区块链）',
        emoji='🚀',
        is_flagship=True
    ),
    'ARKW': ETFInfo(
        symbol='ARKW',
        name_cn='下一代互联网',
        name_en='ARK Next Generation Internet ETF',
        focus='互联网、云计算、区块链、元宇宙',
        emoji='🌐'
    ),
    'ARKG': ETFInfo(
        symbol='ARKG',
        name_cn='基因革命',
        name_en='ARK Genomic Revolution ETF',
        focus='基因编辑、精准医疗、生物科技',
        emoji='🧬'
    ),
    'ARKQ': ETFInfo(
        symbol='ARKQ',
        name_cn='自动化科技',
        name_en='ARK Autonomous Tech & Robotics ETF',
        focus='自动驾驶、机器人、航天、3D打印',
        emoji='🤖'
    ),
    'ARKF': ETFInfo(
        symbol='ARKF',
        name_cn='金融科技',
        name_en='ARK Fintech Innovation ETF',
        focus='数字支付、区块链、金融创新、去中心化金融',
        emoji='💰'
    )
}


class SummaryAnalyzer:
    """ARK 全系列基金汇总分析器"""
    
    def __init__(self):
        self.etf_info = ETF_INFO_MAP
    
    def analyze_all_etfs(
        self,
        current_holdings: Dict[str, List[dict]],  # {etf: [dict, ...]}
        previous_holdings: Dict[str, List[dict]] = None
    ) -> dict:
        """
        汇总分析所有 ETF 的持仓
        
        Args:
            current_holdings: 当前所有 ETF 的持仓数据
            previous_holdings: 前一日所有 ETF 的持仓数据（可选）
        
        Returns:
            汇总分析结果字典
        """
        logger.info("开始汇总分析所有 ARK ETF...")
        
        result = {
            'date': None,
            'etf_count': len(current_holdings),
            'etf_summaries': {},  # 各基金摘要
            'statistics': {},  # 统计信息
            'overlapping_stocks': [],  # 跨基金重叠股票
            'exclusive_stocks': {},  # 各基金独家持仓
            'top_changes': [],  # 重点变化
        }
        
        # 1. 收集所有股票信息
        all_stocks = defaultdict(list)  # {ticker: [{etf, weight, company, ...}]}
        
        for etf, holdings in current_holdings.items():
            if not holdings:
                continue
            
            # 设置日期（取第一个 ETF 的日期）
            if result['date'] is None and len(holdings) > 0:
                result['date'] = holdings[0].get('date', None)
            
            # 各基金摘要
            result['etf_summaries'][etf] = {
                'info': self.etf_info[etf],
                'holdings_count': len(holdings),
                'top_holdings': holdings[:5],  # Top 5（字典格式）
            }
            
            # 收集股票
            for holding in holdings:
                ticker = holding.get('ticker', 'N/A')
                if ticker != 'N/A':  # 排除货币基金
                    all_stocks[ticker].append({
                        'etf': etf,
                        'weight': holding['weight'],
                        'company': holding['company'],
                        'market_value': holding.get('market_value', 0),
                        'shares': holding.get('shares', 0)
                    })
        
        # 2. 分析跨基金重叠股票
        result['overlapping_stocks'] = self._analyze_overlapping(all_stocks)
        
        # 3. 分析独家持仓
        result['exclusive_stocks'] = self._analyze_exclusive(all_stocks, current_holdings)
        
        # 4. 统计信息
        result['statistics'] = self._calculate_statistics(all_stocks, current_holdings)
        
        # 5. 对比昨日变化（如果有前一日数据）
        if previous_holdings:
            result['top_changes'] = self._analyze_changes(
                current_holdings, previous_holdings, all_stocks
            )
        
        logger.info(f"✅ 汇总分析完成: {len(all_stocks)} 只股票，"
                   f"{len(result['overlapping_stocks'])} 只跨基金重叠")
        
        return result
    
    def _analyze_overlapping(self, all_stocks: dict) -> List[dict]:
        """分析跨基金重叠股票"""
        overlapping = []
        
        for ticker, holdings in all_stocks.items():
            if len(holdings) >= 2:  # 出现在 2+ 基金中
                total_weight = sum(h['weight'] for h in holdings)
                
                overlapping.append({
                    'ticker': ticker,
                    'company': holdings[0]['company'],
                    'num_funds': len(holdings),
                    'total_weight': total_weight,
                    'holdings': sorted(holdings, key=lambda x: x['weight'], reverse=True)
                })
        
        # 排序：优先按基金数量，其次按总权重
        overlapping.sort(key=lambda x: (x['num_funds'], x['total_weight']), reverse=True)
        
        return overlapping
    
    def _analyze_exclusive(
        self, 
        all_stocks: dict, 
        current_holdings: dict
    ) -> Dict[str, List[dict]]:
        """分析各基金独家持仓（仅在该基金中，且权重 > 3%）"""
        exclusive = defaultdict(list)
        
        for ticker, holdings in all_stocks.items():
            if len(holdings) == 1:  # 仅在一个基金中
                h = holdings[0]
                if h['weight'] >= 3.0:  # 权重 >= 3%
                    exclusive[h['etf']].append({
                        'ticker': ticker,
                        'company': h['company'],
                        'weight': h['weight'],
                        'market_value': h['market_value']
                    })
        
        # 每个基金按权重排序，最多保留 5 只
        for etf in exclusive:
            exclusive[etf] = sorted(
                exclusive[etf], 
                key=lambda x: x['weight'], 
                reverse=True
            )[:5]
        
        return dict(exclusive)
    
    def _calculate_statistics(
        self, 
        all_stocks: dict, 
        current_holdings: dict
    ) -> dict:
        """计算统计信息"""
        total_stocks = len(all_stocks)
        overlapping_count = len([t for t, h in all_stocks.items() if len(h) >= 2])
        exclusive_count = total_stocks - overlapping_count
        
        return {
            'total_stocks': total_stocks,
            'overlapping_count': overlapping_count,
            'exclusive_count': exclusive_count,
            'holdings_by_etf': {
                etf: len(holdings) 
                for etf, holdings in current_holdings.items()
            }
        }
    
    def _analyze_changes(
        self,
        current_holdings: dict,
        previous_holdings: dict,
        all_stocks: dict
    ) -> List[dict]:
        """
        分析重点变化
        
        重点关注：
        1. 被多个基金同时增持/减持的股票
        2. 新增的跨基金股票
        3. 从独家变为跨基金的股票
        """
        changes = []
        
        # 构建前一日的股票分布
        previous_stocks = defaultdict(list)
        for etf, holdings in previous_holdings.items():
            for holding in holdings:
                ticker = holding.get('ticker', 'N/A')
                if ticker != 'N/A':
                    previous_stocks[ticker].append({
                        'etf': etf,
                        'weight': holding['weight']
                    })
        
        # 1. 分析每只股票的变化
        for ticker, current_data in all_stocks.items():
            current_etfs = {h['etf']: h['weight'] for h in current_data}
            previous_data = previous_stocks.get(ticker, [])
            previous_etfs = {h['etf']: h['weight'] for h in previous_data}
            
            # 新增的基金持仓
            new_etfs = set(current_etfs.keys()) - set(previous_etfs.keys())
            
            # 移除的基金持仓
            removed_etfs = set(previous_etfs.keys()) - set(current_etfs.keys())
            
            # 同时增持/减持
            increased_etfs = []
            decreased_etfs = []
            
            for etf in set(current_etfs.keys()) & set(previous_etfs.keys()):
                change = current_etfs[etf] - previous_etfs[etf]
                if change > 0.5:  # 增持超过 0.5%
                    increased_etfs.append((etf, change))
                elif change < -0.5:  # 减持超过 0.5%
                    decreased_etfs.append((etf, change))
            
            # 记录重要变化
            company = current_data[0]['company']
            
            # 被多个基金同时增持
            if len(increased_etfs) >= 2:
                changes.append({
                    'type': 'multi_increase',
                    'ticker': ticker,
                    'company': company,
                    'etfs': increased_etfs,
                    'description': f"{ticker} 被 {len(increased_etfs)} 只基金同时增持"
                })
            
            # 被多个基金同时减持
            if len(decreased_etfs) >= 2:
                changes.append({
                    'type': 'multi_decrease',
                    'ticker': ticker,
                    'company': company,
                    'etfs': decreased_etfs,
                    'description': f"{ticker} 被 {len(decreased_etfs)} 只基金同时减持"
                })
            
            # 新增跨基金股票（前一日只在1个基金，今天在2+基金）
            if len(previous_data) == 1 and len(current_data) >= 2:
                changes.append({
                    'type': 'new_overlap',
                    'ticker': ticker,
                    'company': company,
                    'etfs': list(new_etfs),
                    'description': f"{ticker} 从单基金变为跨基金持仓"
                })
            
            # 完全新增到多个基金
            if len(new_etfs) >= 2:
                changes.append({
                    'type': 'new_multi',
                    'ticker': ticker,
                    'company': company,
                    'etfs': list(new_etfs),
                    'description': f"{ticker} 被 {len(new_etfs)} 只基金同时新增"
                })
            
            # 完全从多个基金移除
            if len(removed_etfs) >= 2:
                changes.append({
                    'type': 'removed_multi',
                    'ticker': ticker,
                    'company': company,
                    'etfs': list(removed_etfs),
                    'description': f"{ticker} 被 {len(removed_etfs)} 只基金同时移除"
                })
        
        # 按重要性排序
        priority = {
            'new_multi': 1,
            'multi_increase': 2,
            'new_overlap': 3,
            'multi_decrease': 4,
            'removed_multi': 5
        }
        changes.sort(key=lambda x: priority.get(x['type'], 99))
        
        return changes[:10]  # 返回最重要的 10 条
