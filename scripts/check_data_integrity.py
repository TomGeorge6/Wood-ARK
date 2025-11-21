#!/usr/bin/env python3
"""
数据完整性检查脚本

检查历史数据是否完整，识别缺失的日期
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config


def check_data_integrity(etf_symbol: str, days: int = 30):
    """
    检查指定 ETF 的数据完整性
    
    Args:
        etf_symbol: ETF 代码
        days: 检查最近多少天
    """
    config = load_config()
    data_dir = Path(config.data.data_dir) / 'holdings' / etf_symbol
    
    if not data_dir.exists():
        print(f"❌ {etf_symbol} 数据目录不存在: {data_dir}")
        return
    
    # 获取现有文件
    csv_files = sorted([f.stem for f in data_dir.glob('*.csv')])
    
    print(f"\n{'='*60}")
    print(f"📊 {etf_symbol} 数据完整性检查")
    print(f"{'='*60}")
    print(f"数据目录: {data_dir}")
    print(f"文件总数: {len(csv_files)} 个")
    
    if csv_files:
        print(f"最早日期: {csv_files[0]}")
        print(f"最新日期: {csv_files[-1]}")
    else:
        print("❌ 没有任何数据文件！")
        return
    
    # 检查最近 N 天的缺失日期
    et_tz = ZoneInfo("America/New_York")
    today = datetime.now(et_tz).date()
    
    expected_dates = []
    for i in range(days):
        check_date = today - timedelta(days=i)
        # 只检查工作日（周一到周五）
        if check_date.weekday() < 5:
            expected_dates.append(check_date.strftime('%Y-%m-%d'))
    
    expected_dates.reverse()
    
    # 找出缺失的日期
    missing_dates = [d for d in expected_dates if d not in csv_files]
    
    print(f"\n检查范围: 最近 {days} 天（仅工作日）")
    print(f"应有数据: {len(expected_dates)} 个交易日")
    print(f"实际拥有: {len([d for d in expected_dates if d in csv_files])} 个")
    
    if missing_dates:
        print(f"\n⚠️  缺失日期 ({len(missing_dates)} 个):")
        for date in missing_dates:
            # 检查是否是节假日（简单判断）
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            weekday = date_obj.strftime('%A')
            print(f"  - {date} ({weekday})")
        
        print(f"\n💡 补充缺失数据:")
        print(f"python3 main.py --date YYYY-MM-DD --manual")
    else:
        print(f"\n✅ 数据完整！")
    
    # 检查文件大小异常
    print(f"\n{'='*60}")
    print("📁 文件大小检查")
    print(f"{'='*60}")
    
    file_sizes = []
    for csv_file in sorted(data_dir.glob('*.csv'))[-10:]:  # 检查最近10个文件
        size = csv_file.stat().st_size
        file_sizes.append((csv_file.name, size))
    
    if file_sizes:
        avg_size = sum(s for _, s in file_sizes) / len(file_sizes)
        
        for filename, size in file_sizes:
            status = "✅"
            if size < avg_size * 0.5:  # 小于平均值的50%
                status = "⚠️  (偏小)"
            elif size > avg_size * 2:  # 大于平均值的200%
                status = "⚠️  (偏大)"
            
            print(f"{status} {filename}: {size:,} bytes")
        
        print(f"\n平均文件大小: {avg_size:,.0f} bytes")


def check_all_etfs(days: int = 30):
    """检查所有 ETF 的数据完整性"""
    etfs = ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']
    
    for etf in etfs:
        check_data_integrity(etf, days)
    
    print(f"\n{'='*60}")
    print("✅ 检查完成")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='检查 ARK ETF 数据完整性')
    parser.add_argument('--etf', type=str, help='指定 ETF 代码（不指定则检查全部）')
    parser.add_argument('--days', type=int, default=30, help='检查最近多少天（默认30天）')
    
    args = parser.parse_args()
    
    if args.etf:
        check_data_integrity(args.etf.upper(), args.days)
    else:
        check_all_etfs(args.days)
