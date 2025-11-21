#!/usr/bin/env python3
"""
Wood-ARK: ARK ETF 持仓监控工具

主程序入口，负责命令行参数解析和流程编排。
"""

import argparse
import sys
import logging
from pathlib import Path

from src.utils import load_config, setup_logging, cleanup_old_logs
from src.fetcher import DataFetcher
from src.analyzer import Analyzer
from src.reporter import ReportGenerator
from src.image_generator import ImageGenerator
from src.notifier import WeChatNotifier
from src.scheduler import Scheduler
from src.summary_analyzer import SummaryAnalyzer
from src.summary_notifier import SummaryNotifier

logger = logging.getLogger(__name__)


def test_webhook_mode(config) -> int:
    """
    测试 Webhook 连接模式
    
    Returns:
        退出码（0 成功，1 失败）
    """
    logger.info("=== 测试 Webhook 连接 ===")
    
    notifier = WeChatNotifier(
        webhook_url=config.notification.webhook_url,
        max_retries=config.retry.max_retries,
        retry_delays=config.retry.retry_delays
    )
    
    if notifier.test_connection():
        print("✅ Webhook 测试成功")
        return 0
    else:
        print("❌ Webhook 测试失败，请检查配置")
        return 1


def check_missed_mode(config) -> int:
    """
    检查缺失数据模式（仅查看，不补齐）
    
    ⚠️ 由于 API 限制，无法补齐历史数据，此功能仅用于查看缺失情况
    
    Returns:
        退出码（0 成功，1 失败）
    """
    logger.info("=== 检查缺失数据 ===")
    
    scheduler = Scheduler(
        data_dir=config.data.data_dir,
        enable_schedule=False
    )
    
    etf_symbols = config.data.etfs
    missed = scheduler.check_missed_dates(etf_symbols, days=7)
    
    if not missed:
        print("✅ 未发现缺失数据")
        return 0
    
    print(f"⚠️  发现缺失数据:")
    for etf, dates in missed.items():
        print(f"  {etf}: {', '.join(dates)}")
    
    print("\n💡 提示：")
    print("   由于 ARKFunds.io API 只能获取当日数据，无法补齐历史缺失数据。")
    print("   建议每天定时运行，自然累积数据。")
    
    return 0


def run_daily_task(
    config,
    target_date: str = None,
    etf_filter: str = None,
    force: bool = False
) -> int:
    """
    执行每日任务
    
    Args:
        config: 配置对象
        target_date: 目标日期（可选）
        etf_filter: 只处理指定 ETF（可选）
        force: 是否强制执行
    
    Returns:
        退出码（0 成功，1 失败）
    """
    logger.info("=== 开始每日任务 ===")
    
    # 初始化各模块
    scheduler = Scheduler(
        data_dir=config.data.data_dir,
        enable_schedule=config.schedule.enabled
    )
    
    # 检查是否应该运行
    if not scheduler.should_run_today(force=force):
        logger.info("今天不需要执行任务")
        return 0
    
    # ⚠️ 不执行任何补齐逻辑
    # 只获取今天的数据，确保数据准确性
    
    # 获取目标日期和对比日期
    target_date = scheduler.get_target_date(target_date)
    comparison_date = scheduler.get_comparison_date(target_date)
    
    logger.info(f"目标日期: {target_date}, 对比日期: {comparison_date}")
    
    # 初始化组件
    fetcher = DataFetcher(config=config)
    
    # 0. 自动下载历史数据（首次运行或数据不足时）
    if config.data.auto_download_history:
        logger.info("[0/6] 检查并下载历史数据...")
        for etf in config.data.etfs:
            # 检查是否有足够的历史数据（至少 5 天）
            holdings_dir = Path(config.data.data_dir) / "holdings" / etf
            if holdings_dir.exists():
                existing_files = list(holdings_dir.glob("*.csv"))
                if len(existing_files) >= 5:
                    logger.debug(f"{etf} 已有 {len(existing_files)} 天数据，跳过下载")
                    continue
            
            logger.info(f"下载 {etf} 历史数据...")
            fetcher.download_historical_data(etf, days=config.data.history_days)
    
    # 0.5 清理过期数据
    logger.info("[0.5/6] 清理过期数据...")
    cleanup_stats = fetcher.cleanup_old_data(retention_days=config.data.retention_days)
    if cleanup_stats:
        total_deleted = sum(s['deleted_count'] for s in cleanup_stats.values())
        logger.info(f"清理完成: 删除 {total_deleted} 个过期文件")
    
    analyzer = Analyzer(threshold=config.analysis.change_threshold)
    
    reporter = ReportGenerator(data_dir=config.data.data_dir)
    
    image_gen = ImageGenerator(data_dir=config.data.data_dir)
    
    notifier = WeChatNotifier(
        webhook_url=config.notification.webhook_url,
        max_retries=config.retry.max_retries,
        retry_delays=config.retry.retry_delays
    )
    
    # 处理每个 ETF
    etf_symbols = config.data.etfs
    if etf_filter:
        etf_symbols = [etf_filter]
    
    total_success = 0
    total_failed = 0
    
    # 存储所有ETF的持仓数据（用于汇总报告）
    all_current_holdings = {}  # {etf: [dict, ...]}
    all_previous_holdings = {}  # {etf: [dict, ...]}
    all_current_dfs = {}  # {etf: DataFrame}
    all_previous_dfs = {}  # {etf: DataFrame}
    all_analysis_results = {}  # {etf: analysis_result}
    all_etf_images = {}  # {etf: [image_paths]}
    
    for etf in etf_symbols:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"处理 {etf}")
            logger.info(f"{'='*50}")
            
            # 1. 获取数据
            logger.info(f"[1/5] 获取 {etf} 持仓数据...")
            current_df = fetcher.fetch_holdings(etf, target_date)
            previous_df = fetcher.fetch_holdings(etf, comparison_date)
            
            if current_df is None or previous_df is None:
                logger.error(f"❌ {etf} 数据获取失败，跳过")
                total_failed += 1
                continue
            
            # 保存到本地
            fetcher.save_to_csv(current_df, etf, target_date)
            
            # 2. 分析变化
            logger.info(f"[2/5] 分析持仓变化...")
            analysis_result = analyzer.compare_holdings(
                current_df, previous_df, comparison_date, target_date
            )
            
            # 3. 生成报告
            logger.info(f"[3/5] 生成 Markdown 报告...")
            current_holdings = current_df.to_dict('records')
            markdown = reporter.generate_markdown(
                analysis_result, etf, current_holdings
            )
            
            # 保存报告
            report_path = reporter.save_report(markdown, etf, target_date)
            logger.info(f"报告已保存: {report_path}")
            
            # 4. 生成可视化长图
            logger.info(f"[4/5] 生成综合报告长图...")
            image_paths = []
            
            try:
                # 提取新增股票代码列表
                added_tickers = [h.ticker for h in analysis_result['added']]
                
                # 生成单张长图（包含持仓表格、基金趋势、Top 10 趋势、新增股票趋势）
                comprehensive_img = image_gen.generate_comprehensive_report_image(
                    current_holdings, 
                    current_df, 
                    previous_df, 
                    etf, 
                    target_date,
                    added_tickers=added_tickers
                )
                image_paths.append(comprehensive_img)
                logger.info(f"综合报告长图已生成: {comprehensive_img}")
            except Exception as e:
                logger.warning(f"图片生成失败: {e}", exc_info=True)
            
            # 保存数据用于后续合并推送
            all_current_holdings[etf] = current_holdings
            all_previous_holdings[etf] = previous_df.to_dict('records')
            all_current_dfs[etf] = current_df
            all_previous_dfs[etf] = previous_df
            all_analysis_results[etf] = analysis_result
            all_etf_images[etf] = image_paths
            
            logger.info(f"✅ {etf} 处理完成")
            total_success += 1
        
        except Exception as e:
            logger.error(f"❌ 处理 {etf} 时发生错误: {e}", exc_info=True)
            total_failed += 1
            
            # 发送错误告警
            if config.notification.enable_error_alert:
                notifier.send_error_alert(str(e), etf)
    
    # 汇总结果
    logger.info(f"\n{'='*50}")
    logger.info(f"数据处理完成: 成功 {total_success}, 失败 {total_failed}")
    logger.info(f"{'='*50}")
    
    # ========== 分批推送（方案A：稳定性最高）==========
    if total_success >= 2:  # 至少成功2个基金才推送
        try:
            logger.info(f"\n{'='*50}")
            logger.info("开始分批推送（7条消息：1文字 + 6图片）")
            logger.info(f"{'='*50}")
            
            # === 步骤1：汇总分析 ===
            logger.info("[步骤 1/7] 生成汇总分析...")
            summary_analyzer = SummaryAnalyzer()
            summary_result = summary_analyzer.analyze_all_etfs(
                current_holdings=all_current_holdings,
                previous_holdings=all_previous_holdings
            )
            
            logger.info(f"✅ 汇总分析完成: {summary_result['statistics']['total_stocks']} 只股票, "
                       f"{summary_result['statistics']['overlapping_count']} 只跨基金重叠")
            
            # === 步骤2：生成并发送超长文字 ===
            logger.info("[步骤 2/7] 生成并发送超长文字消息...")
            
            # 2.1 生成汇总文字
            summary_notifier_gen = SummaryNotifier()
            summary_markdown = summary_notifier_gen.generate_wechat_markdown(summary_result)
            
            # 2.2 追加各基金摘要
            combined_text_lines = [summary_markdown, "\n\n━━━━━━━━━━━━━━━━━━━━━\n"]
            
            for etf in ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']:
                if etf not in all_analysis_results:
                    continue
                
                analysis_result = all_analysis_results[etf]
                etf_text = notifier.generate_etf_wechat_markdown(
                    etf_symbol=etf,
                    date=target_date,
                    prev_date=analysis_result['prev_date'],
                    curr_date=analysis_result['curr_date'],
                    analysis_result=analysis_result
                )
                combined_text_lines.append(etf_text)
                combined_text_lines.append("\n━━━━━━━━━━━━━━━━━━━━━\n")
            
            combined_text = '\n'.join(combined_text_lines)
            
            # 发送文字消息
            if notifier.send_markdown(combined_text):
                logger.info("✅ [2/7] 文字消息发送成功")
            else:
                logger.error("❌ [2/7] 文字消息发送失败")
            
            import time
            time.sleep(0.5)  # 避免发送过快
            
            # === 步骤3：生成并发送汇总长图 ===
            logger.info("[步骤 3/7] 生成并发送汇总长图...")
            summary_image = image_gen.generate_summary_report_image(
                summary_result, target_date
            )
            
            if notifier.send_image(summary_image):
                logger.info("✅ [3/7] 汇总长图发送成功")
            else:
                logger.error("❌ [3/7] 汇总长图发送失败")
            
            time.sleep(0.5)
            
            # === 步骤4-8：依次发送各基金长图 ===
            image_success_count = 1 if notifier.send_image(summary_image) else 0
            
            for idx, etf in enumerate(['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF'], start=4):
                if etf not in all_etf_images or not all_etf_images[etf]:
                    logger.warning(f"[{idx}/7] {etf} 没有图片，跳过")
                    continue
                
                logger.info(f"[步骤 {idx}/7] 发送 {etf} 长图...")
                etf_image_path = all_etf_images[etf][0]
                
                if notifier.send_image(etf_image_path):
                    logger.info(f"✅ [{idx}/7] {etf} 长图发送成功")
                    image_success_count += 1
                else:
                    logger.error(f"❌ [{idx}/7] {etf} 长图发送失败")
                
                time.sleep(0.5)  # 避免发送过快
            
            # === 汇总推送结果 ===
            logger.info(f"\n{'='*50}")
            logger.info(f"分批推送完成: 图片 {image_success_count}/6 成功")
            logger.info(f"{'='*50}")
            
            # 标记推送状态（只要有一张图发送成功就算成功）
            push_success = image_success_count > 0
            
            for etf in all_analysis_results.keys():
                scheduler.mark_pushed(etf, target_date, success=push_success)
            
        except Exception as e:
            logger.error(f"❌ 分批推送时发生错误: {e}", exc_info=True)
            if config.notification.enable_error_alert:
                notifier.send_error_alert(f"分批推送失败: {e}", "ALL")
    else:
        logger.info("跳过推送（成功的基金数量不足）")
    
    return 0 if total_failed == 0 else 1


def backfill_mode(config, days: int = 90) -> int:
    """
    ⚠️ 此功能已废弃
    
    原因：ARKFunds.io API 只能获取当日数据，无法补齐历史数据
    """
    logger.warning("⚠️ backfill 功能已废弃（API 限制：只能获取当日数据）")
    print("❌ 此功能已废弃")
    print("💡 原因：ARKFunds.io API 只能获取当日数据，无法补齐历史数据")
    print("💡 建议：每天定时运行，自然累积数据")
    return 1

def backfill_mode_deprecated(config, days: int = 90) -> int:
    """
    补充历史数据模式
    
    Args:
        config: 配置对象
        days: 补充天数
    
    Returns:
        退出码（0 成功，1 失败）
    """
    logger.info(f"=== 补充历史数据（近 {days} 天）===")
    
    fetcher = DataFetcher(config=config)
    etf_symbols = config.data.etfs
    
    total_success = 0
    
    for etf in etf_symbols:
        logger.info(f"下载 {etf} 历史数据...")
        count = fetcher.download_historical_data(etf, days=days)
        total_success += count
        logger.info(f"✅ {etf}: 新增 {count} 个文件")
    
    logger.info(f"✅ 历史数据补充完成: 总计新增 {total_success} 个文件")
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Wood-ARK: ARK ETF 持仓变化监控工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                    # 自动模式（工作日执行）
  python main.py --manual           # 手动模式（强制执行）
  python main.py --date 2025-01-15  # 指定日期
  python main.py --check-missed     # 检查缺失数据（仅查看，不补齐）
  python main.py --test-webhook     # 测试 Webhook
        """
    )
    
    parser.add_argument(
        '--manual',
        action='store_true',
        help='手动模式：强制执行（忽略工作日检查）'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='指定日期（YYYY-MM-DD），默认使用当前日期'
    )
    
    parser.add_argument(
        '--check-missed',
        action='store_true',
        help='检查并补充最近 7 天缺失的数据'
    )
    
    parser.add_argument(
        '--test-webhook',
        action='store_true',
        help='测试企业微信 Webhook 连接'
    )
    
    parser.add_argument(
        '--etf',
        type=str,
        help='只处理指定 ETF（如 ARKK）'
    )
    
    parser.add_argument(
        '--backfill',
        action='store_true',
        help='[已废弃] 补充历史数据（API 限制，无法使用）'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='[已废弃] 补充历史数据的天数'
    )
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        config = load_config()
        
        # 设置日志
        setup_logging(
            log_dir=config.data.log_dir,  # log_dir 在 data 配置中
            log_level=config.log.level
        )
        
        # 清理旧日志
        cleanup_old_logs(
            log_dir=config.data.log_dir,  # log_dir 在 data 配置中
            retention_days=config.log.retention_days
        )
        
        logger.info("Wood-ARK 启动")
        logger.info(f"参数: {vars(args)}")
        
        # 根据参数选择执行模式
        if args.test_webhook:
            exit_code = test_webhook_mode(config)
        
        elif args.check_missed:
            exit_code = check_missed_mode(config)
        
        elif args.backfill:
            exit_code = backfill_mode(config, days=args.days)
        
        else:
            # 正常执行模式
            exit_code = run_daily_task(
                config=config,
                target_date=args.date,
                etf_filter=args.etf,
                force=args.manual
            )
        
        logger.info(f"Wood-ARK 退出，退出码: {exit_code}")
        sys.exit(exit_code)
    
    except KeyboardInterrupt:
        logger.info("用户中断执行")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"程序发生未处理异常: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
