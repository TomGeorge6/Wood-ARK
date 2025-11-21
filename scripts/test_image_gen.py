#!/usr/bin/env python3
"""
测试图片生成功能（包括新增股票趋势）
"""

import sys
from pathlib import Path
import pandas as pd

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.image_generator import ImageGenerator
from src.fetcher import DataFetcher
from src.analyzer import Analyzer
from src.utils import load_config

def main():
    # 加载配置
    config = load_config()
    
    # 初始化组件
    fetcher = DataFetcher(config=config)
    image_gen = ImageGenerator(data_dir=config.data.data_dir)
    analyzer = Analyzer(threshold=config.analysis.change_threshold)
    
    # 测试 ETF
    etf = "ARKK"
    date = "2025-11-14"
    prev_date = "2025-11-13"
    
    print(f"测试 {etf} 图片生成...")
    
    # 读取数据
    current_df = fetcher.load_from_csv(etf, date)
    previous_df = fetcher.load_from_csv(etf, prev_date)
    
    if current_df is None or previous_df is None:
        print("❌ 数据加载失败")
        return 1
    
    # 分析变化
    analysis = analyzer.compare_holdings(current_df, previous_df, prev_date, date)
    
    # 提取新增股票
    added_tickers = [h.ticker for h in analysis['added']]
    print(f"新增股票: {added_tickers}")
    
    # 生成图片
    current_holdings = current_df.to_dict('records')
    
    try:
        img_path = image_gen.generate_comprehensive_report_image(
            current_holdings,
            current_df,
            previous_df,
            etf,
            date,
            added_tickers=added_tickers
        )
        print(f"✅ 图片生成成功: {img_path}")
        
        # 检查文件大小
        file_size = Path(img_path).stat().st_size / 1024  # KB
        print(f"文件大小: {file_size:.2f} KB")
        
        return 0
    except Exception as e:
        print(f"❌ 图片生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
