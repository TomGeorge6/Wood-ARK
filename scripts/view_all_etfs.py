#!/usr/bin/env python3
"""
查看所有 ARK ETF 的综合信息

功能：
1. 显示所有 ETF 的基本信息和 Top 持仓
2. 发现跨基金重叠的股票
3. 计算 Wood 姐对某只股票的总体配置
"""

import sys
import os
from pathlib import Path
import pandas as pd
from collections import defaultdict

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.fetcher import DataFetcher
from src.config_loader import ConfigLoader
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("ARK 全系列 ETF 持仓概览".center(80))
    logger.info("=" * 80)
    
    # 加载配置
    config = ConfigLoader()
    fetcher = DataFetcher(config)
    
    etfs = config.data.etf_symbols
    date = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    all_holdings = {}  # {etf: df}
    all_stocks = defaultdict(list)  # {ticker: [(etf, weight), ...]}
    
    # 1. 下载所有 ETF 数据
    logger.info("\n📊 正在获取所有 ETF 数据...\n")
    
    for etf in etfs:
        try:
            df = fetcher.fetch_holdings(etf, date)
            all_holdings[etf] = df
            
            # 记录每只股票在哪些基金中
            for _, row in df.iterrows():
                ticker = row['ticker']
                if ticker != 'N/A':  # 排除货币基金
                    all_stocks[ticker].append({
                        'etf': etf,
                        'weight': row['weight'],
                        'company': row['company'],
                        'market_value': row['market_value']
                    })
            
            logger.info(f"✅ {etf}: {len(df)} 只股票")
            
        except Exception as e:
            logger.error(f"❌ {etf}: 下载失败 - {e}")
    
    # 2. 显示每个 ETF 的 Top 5 持仓
    logger.info("\n" + "=" * 80)
    logger.info("各基金 Top 5 持仓".center(80))
    logger.info("=" * 80)
    
    etf_descriptions = {
        'ARKK': 'ARK Innovation ETF (创新 ETF) ⭐ 旗舰基金',
        'ARKW': 'ARK Next Generation Internet ETF (下一代互联网)',
        'ARKG': 'ARK Genomic Revolution ETF (基因革命)',
        'ARKQ': 'ARK Autonomous Tech & Robotics ETF (自动化科技)',
        'ARKF': 'ARK Fintech Innovation ETF (金融科技)'
    }
    
    for etf in etfs:
        if etf not in all_holdings:
            continue
        
        df = all_holdings[etf].copy()
        df = df.sort_values('weight', ascending=False).head(5)
        
        logger.info(f"\n【{etf}】{etf_descriptions.get(etf, '')}")
        logger.info("-" * 80)
        
        for i, row in enumerate(df.itertuples(), 1):
            company = row.company[:35]  # 限制长度
            logger.info(
                f"{i}. {row.ticker:6s}  {company:35s}  {row.weight:6.2f}%  "
                f"${row.market_value/1e6:,.0f}M"
            )
    
    # 3. 显示跨基金重叠的股票（出现在 2 个及以上基金中）
    logger.info("\n" + "=" * 80)
    logger.info("跨基金重叠持仓（Wood 姐的核心持仓）".center(80))
    logger.info("=" * 80)
    
    # 筛选出现在多个基金中的股票
    overlapping_stocks = {
        ticker: holdings 
        for ticker, holdings in all_stocks.items() 
        if len(holdings) >= 2
    }
    
    # 按出现次数和总权重排序
    overlapping_list = []
    for ticker, holdings in overlapping_stocks.items():
        total_weight = sum(h['weight'] for h in holdings)
        num_funds = len(holdings)
        company = holdings[0]['company']
        
        overlapping_list.append({
            'ticker': ticker,
            'company': company,
            'num_funds': num_funds,
            'total_weight': total_weight,
            'holdings': holdings
        })
    
    # 排序：先按基金数量，再按总权重
    overlapping_list.sort(key=lambda x: (x['num_funds'], x['total_weight']), reverse=True)
    
    logger.info(f"\n🔥 共发现 {len(overlapping_list)} 只股票出现在多个基金中\n")
    
    for i, stock in enumerate(overlapping_list[:20], 1):  # 显示 Top 20
        ticker = stock['ticker']
        company = stock['company'][:30]
        num_funds = stock['num_funds']
        total_weight = stock['total_weight']
        
        logger.info(f"\n{i}. {ticker:6s}  {company:30s}")
        logger.info(f"   出现在 {num_funds} 只基金中，总权重: {total_weight:.2f}%")
        
        # 显示详细分布
        for h in stock['holdings']:
            logger.info(
                f"      - {h['etf']}: {h['weight']:6.2f}%  "
                f"(${h['market_value']/1e6:,.0f}M)"
            )
    
    # 4. 统计信息
    logger.info("\n" + "=" * 80)
    logger.info("统计摘要".center(80))
    logger.info("=" * 80)
    
    total_stocks = len(all_stocks)
    unique_stocks = len([t for t, h in all_stocks.items() if len(h) == 1])
    
    logger.info(f"\n📊 总持仓股票数: {total_stocks}")
    logger.info(f"   - 跨基金重叠: {len(overlapping_list)} 只")
    logger.info(f"   - 单一基金独有: {unique_stocks} 只")
    
    # 各基金持仓数量
    logger.info(f"\n📈 各基金持仓数量:")
    for etf in etfs:
        if etf in all_holdings:
            logger.info(f"   - {etf}: {len(all_holdings[etf])} 只")
    
    logger.info("\n" + "=" * 80)
    logger.info("💡 提示：ARKK 是 Wood 姐的旗舰基金，集中了最核心的创新技术投资")
    logger.info("=" * 80 + "\n")


if __name__ == '__main__':
    main()
