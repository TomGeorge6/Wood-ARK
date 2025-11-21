#!/usr/bin/env python3
"""
测试 ARK 全系列基金汇总报告生成

功能：
1. 下载所有基金数据
2. 生成汇总分析
3. 生成汇总长图
4. 生成微信推送内容
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import load_config
from src.fetcher import DataFetcher
from src.summary_analyzer import SummaryAnalyzer
from src.summary_notifier import SummaryNotifier
from src.image_generator import ImageGenerator
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    """主测试函数"""
    logger.info("=" * 80)
    logger.info("测试 ARK 全系列基金汇总报告生成".center(80))
    logger.info("=" * 80)
    
    # 加载配置
    config = load_config()
    fetcher = DataFetcher(config)
    
    etfs = config.data.etfs
    date = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    logger.info(f"\n📅 目标日期: {date}")
    logger.info(f"📊 监控基金: {', '.join(etfs)}\n")
    
    # 1. 下载所有基金数据
    logger.info("步骤 1: 下载所有基金数据")
    logger.info("-" * 80)
    
    all_current_holdings = {}
    all_previous_holdings = {}
    
    for etf in etfs:
        try:
            logger.info(f"  获取 {etf} 数据...")
            
            # 下载当前数据
            current_df = fetcher.fetch_holdings(etf, date)
            
            # 转换为字典列表
            holdings = current_df.to_dict('records')
            all_current_holdings[etf] = holdings
            
            logger.info(f"  ✅ {etf}: {len(holdings)} 只股票")
            
        except Exception as e:
            logger.error(f"  ❌ {etf} 失败: {e}")
    
    if len(all_current_holdings) < 2:
        logger.error("\n❌ 成功的基金数量不足，无法生成汇总报告")
        return 1
    
    # 2. 汇总分析
    logger.info(f"\n步骤 2: 汇总分析所有基金")
    logger.info("-" * 80)
    
    summary_analyzer = SummaryAnalyzer()
    summary_result = summary_analyzer.analyze_all_etfs(
        current_holdings=all_current_holdings,
        previous_holdings=None  # 暂不对比昨日
    )
    
    stats = summary_result['statistics']
    logger.info(f"  ✅ 总持仓股票: {stats['total_stocks']} 只")
    logger.info(f"  ✅ 跨基金重叠: {stats['overlapping_count']} 只")
    logger.info(f"  ✅ 单基金独有: {stats['exclusive_count']} 只")
    
    # 显示跨基金重叠 Top 5
    logger.info(f"\n  🔥 跨基金重叠 Top 5:")
    for i, stock in enumerate(summary_result['overlapping_stocks'][:5], 1):
        logger.info(
            f"     {i}. {stock['ticker']:6s}  "
            f"{stock['company'][:25]:25s}  "
            f"{stock['num_funds']} 基金  "
            f"总权重 {stock['total_weight']:.2f}%"
        )
    
    # 3. 生成汇总长图
    logger.info(f"\n步骤 3: 生成汇总长图")
    logger.info("-" * 80)
    
    try:
        image_gen = ImageGenerator(data_dir=config.data.data_dir)
        summary_image = image_gen.generate_summary_report_image(
            summary_result, date
        )
        
        logger.info(f"  ✅ 长图已生成: {summary_image}")
        
        # 检查文件大小
        from pathlib import Path
        image_size = Path(summary_image).stat().st_size / 1024  # KB
        logger.info(f"  📏 图片大小: {image_size:.2f} KB")
        
    except Exception as e:
        logger.error(f"  ❌ 长图生成失败: {e}", exc_info=True)
        return 1
    
    # 4. 生成微信推送内容
    logger.info(f"\n步骤 4: 生成微信推送内容")
    logger.info("-" * 80)
    
    try:
        summary_notifier = SummaryNotifier()
        markdown = summary_notifier.generate_wechat_markdown(summary_result)
        
        logger.info("  ✅ 推送内容已生成")
        logger.info("\n" + "=" * 80)
        logger.info("推送预览:")
        logger.info("=" * 80)
        print(markdown)
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"  ❌ 推送内容生成失败: {e}", exc_info=True)
        return 1
    
    logger.info(f"\n✅ 所有测试通过！")
    logger.info("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
