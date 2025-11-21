#!/usr/bin/env python3
"""
测试真实数据下载功能

验证 ARKFunds.io API 是否正常工作
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetcher import DataFetcher
from src.utils import load_config
from datetime import datetime

def main():
    print("=" * 60)
    print("测试真实数据下载功能")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    fetcher = DataFetcher(config=config)
    
    # 测试所有 ETF
    etfs = ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF"]
    date = datetime.now().strftime('%Y-%m-%d')
    
    for etf in etfs:
        print(f"\n{'='*60}")
        print(f"测试 {etf}")
        print(f"{'='*60}")
        
        try:
            # 下载数据
            df = fetcher.fetch_holdings(etf, date)
            
            print(f"✅ {etf} 数据下载成功")
            print(f"   持仓数量: {len(df)}")
            print(f"   数据日期: {df['date'].iloc[0]}")
            print(f"   Top 5 股票:")
            
            top5 = df.nlargest(5, 'weight')
            for idx, row in top5.iterrows():
                print(f"      {row['ticker']:6s} {row['company'][:30]:30s} {row['weight']:5.2f}%")
            
            # 保存数据
            fetcher.save_to_csv(df, etf, date)
            print(f"   已保存到: data/holdings/{etf}/{date}.csv")
            
        except Exception as e:
            print(f"❌ {etf} 数据下载失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
