#!/usr/bin/env python3
"""
测试历史数据下载功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import load_config, setup_logging
from src.fetcher import DataFetcher


def test_download_history():
    """测试下载历史数据"""
    
    # 加载配置
    config = load_config("config.yaml")
    setup_logging(config)
    
    # 初始化 Fetcher
    fetcher = DataFetcher(config=config)
    
    print("\n📥 测试下载 ARKK 最近 90 天历史数据...")
    
    # 下载历史数据
    count = fetcher.download_historical_data("ARKK", days=90)
    
    print(f"\n✅ 下载完成: 新增 {count} 个文件")
    
    # 检查文件
    holdings_dir = Path("./data/holdings/ARKK")
    if holdings_dir.exists():
        files = sorted(holdings_dir.glob("*.csv"))
        print(f"\n📊 ARKK 目录下共有 {len(files)} 个文件")
        
        if files:
            print(f"\n最早: {files[0].stem}")
            print(f"最晚: {files[-1].stem}")
    
    print("\n🧹 测试清理过期数据...")
    
    # 测试清理（保留 90 天）
    stats = fetcher.cleanup_old_data(retention_days=90)
    
    if stats:
        for etf, info in stats.items():
            print(f"\n{etf}: 删除 {info['deleted_count']} 个文件")
            if info['deleted_files']:
                print(f"  最早: {info['deleted_files'][0]}")
                print(f"  最晚: {info['deleted_files'][-1]}")
    else:
        print("\n✅ 没有过期文件需要删除")


if __name__ == "__main__":
    test_download_history()
