#!/usr/bin/env python3
"""
测试综合报告长图生成
"""

import sys
from pathlib import Path
import pandas as pd

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.image_generator import ImageGenerator


def test_comprehensive_image():
    """测试生成综合报告长图"""
    
    etf_symbol = "ARKK"
    date = "2025-11-14"
    
    # 初始化图片生成器
    image_gen = ImageGenerator(data_dir="./data")
    
    # 读取当前和前一日数据
    current_file = Path(f"./data/holdings/{etf_symbol}/{date}.csv")
    previous_file = Path(f"./data/holdings/{etf_symbol}/2025-11-13.csv")
    
    if not current_file.exists() or not previous_file.exists():
        print(f"❌ 数据文件不存在")
        return
    
    current_df = pd.read_csv(current_file)
    previous_df = pd.read_csv(previous_file)
    
    # 转换为字典列表
    current_holdings = current_df.to_dict('records')
    
    print(f"📊 开始生成综合报告长图...")
    print(f"  - ETF: {etf_symbol}")
    print(f"  - 日期: {date}")
    print(f"  - 当前持仓数: {len(current_holdings)}")
    print(f"  - 历史数据天数: {len(list(Path(f'./data/holdings/{etf_symbol}').glob('*.csv')))}")
    
    try:
        image_path = image_gen.generate_comprehensive_report_image(
            current_holdings,
            current_df,
            previous_df,
            etf_symbol,
            date
        )
        
        print(f"\n✅ 综合报告长图已生成:")
        print(f"   {image_path}")
        
        # 显示图片信息
        from PIL import Image
        img = Image.open(image_path)
        print(f"\n📐 图片尺寸: {img.size[0]} x {img.size[1]} 像素")
        print(f"📦 图片大小: {Path(image_path).stat().st_size / 1024:.1f} KB")
        
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_comprehensive_image()
