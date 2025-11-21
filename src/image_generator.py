"""
图片生成模块

生成持仓变化的可视化图表（表格、饼图等）
"""

import logging
from typing import List, Dict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib
from src.utils import ensure_dir

logger = logging.getLogger(__name__)

# 使用非交互式后端
matplotlib.use('Agg')

# 配置中文字体（macOS 系统）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class ImageGenerator:
    """图片生成器"""
    
    def __init__(self, data_dir: str = "./data"):
        """
        初始化图片生成器
        
        Args:
            data_dir: 数据存储根目录
        """
        self.data_dir = Path(data_dir)
        self.image_dir = self.data_dir / "images"
        ensure_dir(str(self.image_dir))
        logger.info(f"初始化 ImageGenerator，图片目录: {self.image_dir}")
    
    def generate_holdings_table(
        self,
        holdings: List[Dict],
        etf_symbol: str,
        date: str,
        top_n: int = 15
    ) -> str:
        """
        生成持仓表格图片
        
        Args:
            holdings: 持仓列表
            etf_symbol: ETF 代码
            date: 日期
            top_n: 显示前N个持仓
        
        Returns:
            生成的图片路径
        """
        logger.info(f"生成 {etf_symbol} 持仓表格图片 (Top {top_n})")
        
        # 按权重排序（权重相同时按市值降序，确保稳定排序）
        sorted_holdings = sorted(
            holdings, 
            key=lambda x: (x['weight'], x['market_value']), 
            reverse=True
        )[:top_n]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, len(sorted_holdings) * 0.5 + 1.5))
        ax.axis('tight')
        ax.axis('off')
        
        # 准备表格数据
        table_data = []
        headers = ['排名', '股票代码', '公司名称', '持股数', '市值', '权重']
        
        for i, holding in enumerate(sorted_holdings, 1):
            shares = self._format_number(holding['shares'])
            market_value = self._format_currency(holding['market_value'])
            weight = f"{holding['weight']:.2f}%"
            company = holding['company'][:25]  # 限制长度
            
            table_data.append([
                str(i),
                holding['ticker'],
                company,
                shares,
                market_value,
                weight
            ])
        
        # 创建表格
        table = ax.table(
            cellText=table_data,
            colLabels=headers,
            cellLoc='left',
            loc='center',
            colWidths=[0.08, 0.12, 0.35, 0.12, 0.15, 0.12]
        )
        
        # 美化样式
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # 设置标题样式（加粗深色背景）
        for i in range(len(headers)):
            cell = table[(0, i)]
            cell.set_facecolor('#4472C4')
            cell.set_text_props(weight='bold', color='white')
        
        # 设置数据行样式（交替颜色）
        for i in range(1, len(table_data) + 1):
            for j in range(len(headers)):
                cell = table[(i, j)]
                if i % 2 == 0:
                    cell.set_facecolor('#E7E6E6')
                else:
                    cell.set_facecolor('#FFFFFF')
        
        # 添加标题
        fig.suptitle(
            f'{etf_symbol} 持仓排名 ({date})',
            fontsize=14,
            fontweight='bold',
            y=0.98
        )
        
        # 保存图片
        etf_dir = self.image_dir / etf_symbol
        ensure_dir(str(etf_dir))
        
        image_path = etf_dir / f"{date}_table.png"
        plt.savefig(
            image_path,
            bbox_inches='tight',
            dpi=150,
            facecolor='white'
        )
        plt.close()
        
        logger.info(f"表格图片已保存: {image_path}")
        return str(image_path)
    
    def generate_pie_chart(
        self,
        holdings: List[Dict],
        etf_symbol: str,
        date: str,
        top_n: int = 10
    ) -> str:
        """
        生成持仓分布饼图
        
        Args:
            holdings: 持仓列表
            etf_symbol: ETF 代码
            date: 日期
            top_n: 显示前N个持仓
        
        Returns:
            生成的图片路径
        """
        logger.info(f"生成 {etf_symbol} 持仓饼图 (Top {top_n})")
        
        # 按权重排序
        sorted_holdings = sorted(holdings, key=lambda x: x['weight'], reverse=True)
        
        # 取前N个和其他
        top_holdings = sorted_holdings[:top_n]
        other_weight = sum(h['weight'] for h in sorted_holdings[top_n:])
        
        # 准备数据
        labels = []
        sizes = []
        
        for holding in top_holdings:
            ticker = holding['ticker']
            weight = holding['weight']
            labels.append(f"{ticker} ({weight:.2f}%)")
            sizes.append(weight)
        
        if other_weight > 0:
            labels.append(f"其他 ({other_weight:.2f}%)")
            sizes.append(other_weight)
        
        # 创建饼图
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = plt.cm.Set3(range(len(sizes)))
        
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 9}
        )
        
        # 美化标签
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
        
        ax.set_title(
            f'{etf_symbol} 持仓分布 ({date})',
            fontsize=14,
            fontweight='bold',
            pad=20
        )
        
        # 保存图片
        etf_dir = self.image_dir / etf_symbol
        ensure_dir(str(etf_dir))
        
        image_path = etf_dir / f"{date}_pie.png"
        plt.savefig(
            image_path,
            bbox_inches='tight',
            dpi=150,
            facecolor='white'
        )
        plt.close()
        
        logger.info(f"饼图已保存: {image_path}")
        return str(image_path)
    
    def generate_change_chart(
        self,
        increased: List,
        decreased: List,
        etf_symbol: str,
        date: str,
        top_n: int = 10
    ) -> str:
        """
        生成持仓变化柱状图
        
        Args:
            increased: 增持列表
            decreased: 减持列表
            etf_symbol: ETF 代码
            date: 日期
            top_n: 显示前N个变化
        
        Returns:
            生成的图片路径
        """
        logger.info(f"生成 {etf_symbol} 持仓变化柱状图")
        
        # 合并增持和减持，按变化绝对值排序
        all_changes = []
        
        for holding in increased:
            all_changes.append({
                'ticker': holding.ticker,
                'change': holding.weight_change,
                'type': 'increase'
            })
        
        for holding in decreased:
            all_changes.append({
                'ticker': holding.ticker,
                'change': holding.weight_change,
                'type': 'decrease'
            })
        
        # 按绝对值排序
        all_changes.sort(key=lambda x: abs(x['change']), reverse=True)
        top_changes = all_changes[:top_n]
        
        if not top_changes:
            logger.warning("没有显著变化，跳过柱状图生成")
            return None
        
        # 准备数据
        tickers = [c['ticker'] for c in top_changes]
        changes = [c['change'] for c in top_changes]
        colors = ['#00C853' if c > 0 else '#D32F2F' for c in changes]
        
        # 创建柱状图
        fig, ax = plt.subplots(figsize=(10, len(top_changes) * 0.5 + 1))
        
        bars = ax.barh(tickers, changes, color=colors)
        
        # 添加数值标签
        for i, (bar, change) in enumerate(zip(bars, changes)):
            width = bar.get_width()
            label_x = width + (0.1 if width > 0 else -0.1)
            ax.text(
                label_x, bar.get_y() + bar.get_height()/2,
                f'{change:+.2f}%',
                va='center',
                ha='left' if width > 0 else 'right',
                fontsize=9
            )
        
        ax.set_xlabel('权重变化 (%)', fontsize=10)
        ax.set_title(
            f'{etf_symbol} 显著持仓变化 ({date})',
            fontsize=12,
            fontweight='bold',
            pad=15
        )
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        ax.grid(axis='x', alpha=0.3)
        
        # 保存图片
        etf_dir = self.image_dir / etf_symbol
        ensure_dir(str(etf_dir))
        
        image_path = etf_dir / f"{date}_change.png"
        plt.savefig(
            image_path,
            bbox_inches='tight',
            dpi=150,
            facecolor='white'
        )
        plt.close()
        
        logger.info(f"变化柱状图已保存: {image_path}")
        return str(image_path)
    
    def _format_number(self, num: float) -> str:
        """格式化数字（使用 K/M 单位）"""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return f"{num:.0f}"
    
    def _format_currency(self, amount: float) -> str:
        """格式化货币（美元）"""
        if amount >= 1_000_000_000:
            return f"${amount / 1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"${amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount / 1_000:.1f}K"
        else:
            return f"${amount:.0f}"
    
    def generate_fund_trend_chart(
        self,
        etf_symbol: str,
        date: str,
        days: int = 30
    ) -> str:
        """
        生成基金总额变化趋势图
        
        Args:
            etf_symbol: ETF 代码
            date: 当前日期
            days: 显示最近N天
        
        Returns:
            生成的图片路径，如果数据不足则返回 None
        """
        logger.info(f"生成 {etf_symbol} 基金总额趋势图 (最近 {days} 天)")
        
        # 读取历史数据
        etf_dir = self.data_dir / "holdings" / etf_symbol
        
        if not etf_dir.exists():
            logger.warning(f"历史数据目录不存在: {etf_dir}")
            return None
        
        # 获取所有历史文件
        csv_files = sorted(etf_dir.glob("*.csv"))
        
        if len(csv_files) < 2:
            logger.warning(f"历史数据不足（仅 {len(csv_files)} 天），需要至少2天数据")
            return None
        
        # 读取最近N天的数据
        import pandas as pd
        
        dates = []
        total_values = []
        
        for csv_file in csv_files[-days:]:
            try:
                df = pd.read_csv(csv_file)
                file_date = csv_file.stem  # 文件名即日期
                total_value = df['market_value'].sum()
                
                dates.append(file_date)
                total_values.append(total_value)
            except Exception as e:
                logger.warning(f"读取文件失败 {csv_file}: {e}")
        
        if len(dates) < 2:
            logger.warning("有效数据不足")
            return None
        
        # 创建趋势图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 图1: 总市值趋势
        ax1.plot(dates, total_values, marker='o', linewidth=2, markersize=6, color='#2E86AB')
        ax1.fill_between(range(len(dates)), total_values, alpha=0.3, color='#2E86AB')
        ax1.set_title(f'{etf_symbol} 基金总市值趋势', fontsize=14, fontweight='bold', pad=15)
        ax1.set_ylabel('总市值 (美元)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # 格式化Y轴（显示为B或M）
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'${x/1e9:.1f}B' if x >= 1e9 else f'${x/1e6:.0f}M'
        ))
        
        # 添加数值标签
        for i, (d, v) in enumerate(zip(dates, total_values)):
            if i % max(1, len(dates)//10) == 0:  # 避免标签过密
                ax1.text(i, v, f'${v/1e9:.2f}B', ha='center', va='bottom', fontsize=8)
        
        # 旋转X轴日期标签
        ax1.tick_params(axis='x', rotation=45)
        
        # 图2: 日度变化百分比
        daily_changes = []
        for i in range(1, len(total_values)):
            change_pct = (total_values[i] - total_values[i-1]) / total_values[i-1] * 100
            daily_changes.append(change_pct)
        
        colors = ['#00C853' if c >= 0 else '#D32F2F' for c in daily_changes]
        
        ax2.bar(range(len(daily_changes)), daily_changes, color=colors, alpha=0.8)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax2.set_title('日度变化率', fontsize=12, fontweight='bold', pad=10)
        ax2.set_ylabel('变化率 (%)', fontsize=11)
        ax2.set_xlabel('日期', fontsize=11)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # X轴使用日期（跳过第一天）
        ax2.set_xticks(range(len(daily_changes)))
        ax2.set_xticklabels(dates[1:], rotation=45, ha='right')
        
        # 添加百分比标签
        for i, change in enumerate(daily_changes):
            if abs(change) > 0.5:  # 只显示显著变化
                ax2.text(i, change, f'{change:+.1f}%', ha='center', 
                        va='bottom' if change > 0 else 'top', fontsize=8)
        
        plt.tight_layout()
        
        # 保存图片
        image_dir = self.image_dir / etf_symbol
        ensure_dir(str(image_dir))
        
        image_path = image_dir / f"{date}_trend.png"
        plt.savefig(image_path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close()
        
        logger.info(f"趋势图已保存: {image_path}")
        return str(image_path)
    
    def generate_comprehensive_report_image(
        self,
        holdings: List[Dict],
        current_df,
        previous_df,
        etf_symbol: str,
        date: str,
        added_tickers: List[str] = None
    ) -> str:
        """
        生成综合报告长图（包含所有内容）
        
        Args:
            holdings: 持仓列表
            current_df: 当前持仓数据
            previous_df: 前一日持仓数据
            etf_symbol: ETF 代码
            date: 当前日期
            added_tickers: 新增股票代码列表（可选）
        
        Returns:
            生成的图片路径
        """
        logger.info(f"生成 {etf_symbol} 综合报告长图")
        
        import pandas as pd
        from datetime import datetime, timedelta
        
        # 计算图表数量
        etf_dir = self.data_dir / "holdings" / etf_symbol
        csv_files = sorted(etf_dir.glob("*.csv")) if etf_dir.exists() else []
        data_days = len(csv_files)
        
        # 创建长图布局
        # 1. 持仓表格 (高度: 10)
        # 2. 基金总额趋势 (高度: 16，分为 1 个月和 3 个月两组)
        # 3. Top 10 个股趋势 (高度: 12)
        # 4. 新增股票趋势 (高度: 10，仅在有新增股票时显示)
        
        has_new_stocks = added_tickers and len(added_tickers) > 0 and data_days >= 5
        
        if has_new_stocks:
            total_height = 10 + 16 + 12 + 10  # 总高度 48
            height_ratios = [10, 16, 12, 10]
            num_sections = 4
        else:
            total_height = 10 + 16 + 12  # 总高度 38
            height_ratios = [10, 16, 12]
            num_sections = 3
        
        fig = plt.figure(figsize=(14, total_height))
        
        # 使用 GridSpec 进行布局
        from matplotlib.gridspec import GridSpec
        gs = GridSpec(num_sections, 1, figure=fig, height_ratios=height_ratios, hspace=0.3)
        
        # ===== 1. 持仓表格 =====
        ax_table = fig.add_subplot(gs[0])
        self._draw_holdings_table(ax_table, holdings, etf_symbol, date, top_n=15)
        
        # ===== 2. 基金总额趋势 =====
        ax_trend = fig.add_subplot(gs[1])
        if data_days >= 5:
            self._draw_fund_trend(ax_trend, etf_symbol, date, csv_files, data_days)
        else:
            ax_trend.text(0.5, 0.5, f'历史数据不足（仅 {data_days} 天），需要至少 5 天数据',
                         ha='center', va='center', fontsize=12, color='red')
            ax_trend.axis('off')
        
        # ===== 3. Top 10 个股趋势 =====
        ax_stocks = fig.add_subplot(gs[2])
        if data_days >= 5:
            self._draw_top10_trend(ax_stocks, current_df, etf_symbol, date, csv_files, data_days)
        else:
            ax_stocks.text(0.5, 0.5, f'历史数据不足（仅 {data_days} 天），需要至少 5 天数据',
                          ha='center', va='center', fontsize=12, color='red')
            ax_stocks.axis('off')
        
        # ===== 4. 新增股票趋势（仅在有新增股票时显示）=====
        if has_new_stocks:
            ax_new_stocks = fig.add_subplot(gs[3])
            self._draw_new_stocks_trend(
                ax_new_stocks, added_tickers, current_df, etf_symbol, date, csv_files
            )
        
        # 保存图片
        image_dir = self.image_dir / etf_symbol
        ensure_dir(str(image_dir))
        
        image_path = image_dir / f"{date}_comprehensive.png"
        plt.savefig(image_path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close()
        
        logger.info(f"综合报告长图已保存: {image_path}")
        return str(image_path)
    
    def _draw_holdings_table(self, ax, holdings: List[Dict], etf_symbol: str, date: str, top_n: int = 15):
        """在指定 Axes 上绘制持仓表格"""
        ax.axis('tight')
        ax.axis('off')
        
        # 按权重排序
        sorted_holdings = sorted(
            holdings, 
            key=lambda x: (x['weight'], x['market_value']), 
            reverse=True
        )[:top_n]
        
        # 准备表格数据
        table_data = []
        headers = ['排名', '股票代码', '公司名称', '持股数', '市值', '权重']
        
        for i, holding in enumerate(sorted_holdings, 1):
            shares = self._format_number(holding['shares'])
            market_value = self._format_currency(holding['market_value'])
            weight = f"{holding['weight']:.2f}%"
            company = holding['company'][:25]
            
            table_data.append([
                str(i),
                holding['ticker'],
                company,
                shares,
                market_value,
                weight
            ])
        
        # 创建表格
        table = ax.table(
            cellText=table_data,
            colLabels=headers,
            cellLoc='left',
            loc='center',
            colWidths=[0.08, 0.12, 0.35, 0.12, 0.15, 0.12]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # 标题行样式
        for i in range(len(headers)):
            cell = table[(0, i)]
            cell.set_facecolor('#4472C4')
            cell.set_text_props(weight='bold', color='white')
        
        # 数据行样式
        for i in range(1, len(table_data) + 1):
            for j in range(len(headers)):
                cell = table[(i, j)]
                cell.set_facecolor('#E7E6E6' if i % 2 == 0 else '#FFFFFF')
        
        # 添加标题
        ax.set_title(
            f'{etf_symbol} 持仓排名 ({date})',
            fontsize=16,
            fontweight='bold',
            pad=20
        )
    
    def _draw_fund_trend(self, ax, etf_symbol: str, date: str, csv_files, data_days):
        """在指定 Axes 上绘制基金总额趋势（1 个月 + 3 个月）"""
        import pandas as pd
        
        # 隐藏父 Axes
        ax.axis('off')
        
        # 读取所有历史数据
        dates_all = []
        values_all = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                file_date = csv_file.stem
                total_value = df['market_value'].sum()
                dates_all.append(file_date)
                values_all.append(total_value)
            except Exception as e:
                logger.warning(f"读取文件失败 {csv_file}: {e}")
        
        if len(dates_all) < 2:
            ax.text(0.5, 0.5, '有效数据不足', ha='center', va='center', fontsize=12)
            return
        
        # 分割为 1 个月和 3 个月数据
        dates_1m = dates_all[-30:] if len(dates_all) >= 30 else dates_all
        values_1m = values_all[-30:] if len(values_all) >= 30 else values_all
        
        dates_3m = dates_all[-90:] if len(dates_all) >= 90 else dates_all
        values_3m = values_all[-90:] if len(values_all) >= 90 else values_all
        
        # 获取父 Axes 的位置并手动创建子图
        pos = ax.get_position()
        
        # 创建 4 个子图的位置（2行2列）
        # 第一行：基金总市值趋势（1个月、3个月）
        # 第二行：日度变化率（1个月、3个月）
        width = pos.width / 2.1  # 每个子图宽度
        height_top = pos.height * 0.6  # 上半部分高度
        height_bottom = pos.height * 0.35  # 下半部分高度
        gap_h = 0.02
        gap_v = 0.03
        
        # 1 个月趋势（左上）
        ax1 = ax.figure.add_axes([pos.x0, pos.y0 + pos.height - height_top, width, height_top])
        ax1.plot(range(len(dates_1m)), values_1m, marker='o', linewidth=2, markersize=4, color='#2E86AB')
        ax1.fill_between(range(len(dates_1m)), values_1m, alpha=0.3, color='#2E86AB')
        ax1.set_title(f'{etf_symbol} 基金总市值 - 最近 1 个月', fontsize=12, fontweight='bold')
        ax1.set_ylabel('总市值', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'${x/1e9:.1f}B' if x >= 1e9 else f'${x/1e6:.0f}M'
        ))
        
        # X 轴显示日期（稀疏显示）
        step = max(1, len(dates_1m) // 10)
        ax1.set_xticks(range(0, len(dates_1m), step))
        ax1.set_xticklabels([dates_1m[i] for i in range(0, len(dates_1m), step)], rotation=45, fontsize=7, ha='right')
        
        # 3 个月趋势（右上）
        ax2 = ax.figure.add_axes([pos.x0 + width + gap_h, pos.y0 + pos.height - height_top, width, height_top])
        ax2.plot(range(len(dates_3m)), values_3m, marker='o', linewidth=2, markersize=3, color='#A23B72')
        ax2.fill_between(range(len(dates_3m)), values_3m, alpha=0.3, color='#A23B72')
        ax2.set_title(f'{etf_symbol} 基金总市值 - 最近 3 个月', fontsize=12, fontweight='bold')
        ax2.set_ylabel('总市值', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'${x/1e9:.1f}B' if x >= 1e9 else f'${x/1e6:.0f}M'
        ))
        
        step = max(1, len(dates_3m) // 15)
        ax2.set_xticks(range(0, len(dates_3m), step))
        ax2.set_xticklabels([dates_3m[i] for i in range(0, len(dates_3m), step)], rotation=45, fontsize=7, ha='right')
    
    def _draw_new_stocks_trend(
        self, 
        ax, 
        added_tickers: List[str], 
        current_df, 
        etf_symbol: str, 
        date: str, 
        csv_files
    ):
        """
        在指定 Axes 上绘制新增股票的持股数趋势
        
        Args:
            ax: Matplotlib Axes 对象
            added_tickers: 新增股票代码列表
            current_df: 当前持仓数据
            etf_symbol: ETF 代码
            date: 当前日期
            csv_files: 所有历史 CSV 文件列表
        """
        import pandas as pd
        
        # 隐藏父 Axes
        ax.axis('off')
        
        # 获取新增股票的当前信息（用于标题）
        new_stocks_info = []
        for ticker in added_tickers[:10]:  # 最多显示 10 只
            row = current_df[current_df['ticker'] == ticker]
            if len(row) > 0:
                company = row.iloc[0]['company']
                shares = row.iloc[0]['shares']
                new_stocks_info.append({
                    'ticker': ticker,
                    'company': company,
                    'shares': shares
                })
        
        # 按持股数排序（显示持股数最大的新增股票）
        new_stocks_info = sorted(new_stocks_info, key=lambda x: x['shares'], reverse=True)
        
        # 读取历史数据，追踪这些新增股票的持股数变化
        stock_shares = {stock['ticker']: [] for stock in new_stocks_info}
        dates = []
        
        # 读取所有历史数据
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                file_date = csv_file.stem
                dates.append(file_date)
                
                for stock in new_stocks_info:
                    ticker = stock['ticker']
                    row = df[df['ticker'] == ticker]
                    # 如果该股票在该日期存在，记录持股数；否则记录为 0
                    shares = row.iloc[0]['shares'] if len(row) > 0 else 0
                    stock_shares[ticker].append(shares)
            except Exception as e:
                logger.warning(f"读取文件失败 {csv_file}: {e}")
        
        # 获取父 Axes 位置
        pos = ax.get_position()
        
        # 创建单个图表（横跨整个宽度）
        ax1 = ax.figure.add_axes([pos.x0, pos.y0, pos.width, pos.height])
        
        # 为每只新增股票绘制趋势线
        colors = plt.cm.tab10(range(len(new_stocks_info)))
        
        for i, stock in enumerate(new_stocks_info):
            ticker = stock['ticker']
            company = stock['company'][:20]  # 限制长度
            shares_list = stock_shares[ticker]
            
            if len(shares_list) > 0:
                # 使用不同的线型来区分股票
                linestyle = '-' if i < 5 else '--'
                ax1.plot(
                    range(len(dates)), 
                    shares_list, 
                    marker='o', 
                    linewidth=2, 
                    markersize=4, 
                    label=f'{ticker} ({company})',
                    alpha=0.8,
                    color=colors[i],
                    linestyle=linestyle
                )
        
        # 设置标题和标签
        ax1.set_title(
            f'{etf_symbol} 新增持仓股票持股数趋势（按当前持股数排序，最多显示 10 只）', 
            fontsize=12, 
            fontweight='bold',
            pad=10
        )
        ax1.set_ylabel('持股数', fontsize=10)
        ax1.set_xlabel('日期', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # 图例（分两列显示）
        ax1.legend(loc='best', fontsize=8, ncol=2, framealpha=0.9)
        
        # 格式化Y轴（显示为M或K）
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'
        ))
        
        # X 轴日期标签（稀疏显示）
        step = max(1, len(dates) // 20)
        ax1.set_xticks(range(0, len(dates), step))
        ax1.set_xticklabels(
            [dates[i] for i in range(0, len(dates), step)], 
            rotation=45, 
            fontsize=7, 
            ha='right'
        )
        
        # 添加说明文字
        info_text = f"图中显示了最近新增的 {len(new_stocks_info)} 只股票的持股数变化\n"
        info_text += "横轴为 0 表示该股票在该日期不存在于持仓中"
        ax1.text(
            0.02, 0.98, 
            info_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
    
    def generate_summary_report_image(
        self,
        summary_result: dict,
        date: str
    ) -> str:
        """
        生成ARK全系列基金汇总报告长图
        
        Args:
            summary_result: 汇总分析结果（来自 SummaryAnalyzer）
            date: 当前日期
        
        Returns:
            生成的图片路径
        """
        logger.info("生成 ARK 全系列基金汇总报告长图")
        
        import pandas as pd
        from matplotlib.gridspec import GridSpec
        
        # 创建长图布局
        # 1. 统计摘要（高度: 10）
        # 2. 跨基金重叠 Top 10 + 趋势（高度: 18）
        # 3. 各基金 Top 5 持仓（高度: 14）
        # 4. 独家持仓亮点（高度: 10）
        # 5. 重点变化提示（高度: 8）
        
        total_height = 10 + 18 + 14 + 10 + 8  # 总高度 60
        fig = plt.figure(figsize=(14, total_height))
        
        gs = GridSpec(5, 1, figure=fig, height_ratios=[10, 18, 14, 10, 8], hspace=0.3)
        
        # ===== 1. 统计摘要 =====
        ax_stats = fig.add_subplot(gs[0])
        self._draw_summary_statistics(ax_stats, summary_result, date)
        
        # ===== 2. 跨基金重叠 Top 10 + 趋势 =====
        ax_overlap = fig.add_subplot(gs[1])
        self._draw_overlapping_stocks(ax_overlap, summary_result, date)
        
        # ===== 3. 各基金 Top 5 持仓 =====
        ax_etfs = fig.add_subplot(gs[2])
        self._draw_etf_top_holdings(ax_etfs, summary_result)
        
        # ===== 4. 独家持仓亮点 =====
        ax_exclusive = fig.add_subplot(gs[3])
        self._draw_exclusive_holdings(ax_exclusive, summary_result)
        
        # ===== 5. 重点变化提示 =====
        ax_changes = fig.add_subplot(gs[4])
        self._draw_top_changes(ax_changes, summary_result)
        
        # 保存图片
        image_dir = self.image_dir / "SUMMARY"
        ensure_dir(str(image_dir))
        
        image_path = image_dir / f"{date}_summary.png"
        plt.savefig(image_path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close()
        
        logger.info(f"汇总报告长图已保存: {image_path}")
        return str(image_path)
    
    def _draw_summary_statistics(self, ax, summary_result: dict, date: str):
        """绘制统计摘要部分"""
        ax.axis('off')
        
        stats = summary_result['statistics']
        summaries = summary_result['etf_summaries']
        
        # 标题
        title_text = f"ARK 全系列基金持仓监控报告\n{date}"
        ax.text(0.5, 0.95, title_text, ha='center', va='top', 
                fontsize=16, fontweight='bold', transform=ax.transAxes)
        
        # 5只基金对比表格
        table_data = []
        headers = ['基金', '中文名称', '投资方向', '持仓数', 'Top 1 持仓']
        
        for etf_symbol in ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']:
            if etf_symbol not in summaries:
                continue
            
            summary = summaries[etf_symbol]
            info = summary['info']
            top1 = summary['top_holdings'][0] if summary['top_holdings'] else None
            
            flag = ' ⭐' if info.is_flagship else ''
            top1_str = f"{top1.get('ticker', 'N/A')} {top1.get('weight', 0):.1f}%" if top1 else 'N/A'
            
            table_data.append([
                f"{info.emoji} {etf_symbol}{flag}",
                info.name_cn,
                info.focus[:25] + '...' if len(info.focus) > 25 else info.focus,
                str(summary['holdings_count']),
                top1_str
            ])
        
        # 创建表格
        table = ax.table(
            cellText=table_data,
            colLabels=headers,
            cellLoc='left',
            loc='center',
            bbox=[0.05, 0.40, 0.90, 0.45]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2.5)
        
        # 表头样式
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 行样式
        for i in range(1, len(table_data) + 1):
            for j in range(len(headers)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#F5F5F5')
        
        # 统计数字
        stats_text = (
            f"📊 总持仓股票: {stats['total_stocks']} 只  |  "
            f"🔥 跨基金重叠: {stats['overlapping_count']} 只  |  "
            f"💎 单基金独有: {stats['exclusive_count']} 只"
        )
        ax.text(0.5, 0.28, stats_text, ha='center', va='top',
                fontsize=11, fontweight='bold', transform=ax.transAxes,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 说明
        note = "💡 ARKK 是 Wood 姐的旗舰基金，涵盖最全面的创新技术投资"
        ax.text(0.5, 0.05, note, ha='center', va='bottom',
                fontsize=10, style='italic', transform=ax.transAxes)
    
    def _draw_overlapping_stocks(self, ax, summary_result: dict, date: str):
        """绘制跨基金重叠股票 Top 10 + 趋势"""
        ax.axis('off')
        
        overlapping = summary_result['overlapping_stocks'][:10]
        
        if not overlapping:
            ax.text(0.5, 0.5, '暂无跨基金重叠股票', 
                   ha='center', va='center', fontsize=12, transform=ax.transAxes)
            return
        
        # 标题
        ax.text(0.5, 0.98, '🔥 核心重叠持仓 Top 10（Wood 姐最看好的股票）',
                ha='center', va='top', fontsize=14, fontweight='bold',
                transform=ax.transAxes)
        
        # 表格数据
        table_data = []
        for i, stock in enumerate(overlapping, 1):
            ticker = stock['ticker']
            company = stock['company'][:20]
            num_funds = stock['num_funds']
            total_weight = stock['total_weight']
            
            # 构建基金分布字符串
            etf_dist = ' | '.join([
                f"{h['etf']} {h['weight']:.1f}%" 
                for h in stock['holdings'][:3]  # 最多显示3个
            ])
            
            table_data.append([
                str(i),
                ticker,
                company,
                f"{num_funds} 只",
                f"{total_weight:.1f}%",
                etf_dist
            ])
        
        # 创建表格
        headers = ['#', '代码', '公司名称', '基金数', '总权重', '分布']
        table = ax.table(
            cellText=table_data,
            colLabels=headers,
            cellLoc='left',
            loc='upper center',
            bbox=[0.05, 0.50, 0.90, 0.45]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2.0)
        
        # 样式
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#FF5722')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(1, len(table_data) + 1):
            for j in range(len(headers)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#FFF3E0')
        
        # 简化的趋势说明（由于没有历史数据，只显示当前状态）
        note = f"💡 以上股票同时出现在 2-{overlapping[0]['num_funds']} 只基金中，是 Wood 姐最核心的持仓"
        ax.text(0.5, 0.42, note, ha='center', va='top',
                fontsize=9, style='italic', transform=ax.transAxes,
                bbox=dict(boxstyle='round', facecolor='#FFEB3B', alpha=0.3))
    
    def _draw_etf_top_holdings(self, ax, summary_result: dict):
        """绘制各基金 Top 5 持仓"""
        ax.axis('off')
        
        ax.text(0.5, 0.98, '📈 各基金 Top 5 持仓详情',
                ha='center', va='top', fontsize=14, fontweight='bold',
                transform=ax.transAxes)
        
        summaries = summary_result['etf_summaries']
        etf_list = ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']
        
        # 计算每个基金的位置（5行1列）
        y_positions = [0.85, 0.68, 0.51, 0.34, 0.17]
        
        for idx, etf_symbol in enumerate(etf_list):
            if etf_symbol not in summaries:
                continue
            
            summary = summaries[etf_symbol]
            info = summary['info']
            top_holdings = summary['top_holdings'][:5]
            
            y_start = y_positions[idx]
            
            # 基金名称
            flag = ' ⭐' if info.is_flagship else ''
            title = f"{info.emoji} {etf_symbol}{flag} - {info.name_cn} ({summary['holdings_count']} 只)"
            ax.text(0.05, y_start, title, fontsize=10, fontweight='bold',
                   transform=ax.transAxes)
            
            # Top 5 列表
            for i, holding in enumerate(top_holdings):
                y_pos = y_start - 0.025 * (i + 1)
                ticker = holding.get('ticker', 'N/A')
                company = holding.get('company', 'Unknown')[:25]
                weight = holding.get('weight', 0)
                text = f"  {i+1}. {ticker:6s}  {company:25s}  {weight:5.2f}%"
                ax.text(0.08, y_pos, text, fontsize=8, family='monospace',
                       transform=ax.transAxes)
    
    def _draw_exclusive_holdings(self, ax, summary_result: dict):
        """绘制独家持仓亮点（权重 >= 3%）"""
        ax.axis('off')
        
        ax.text(0.5, 0.95, '💎 独家持仓亮点（仅在单一基金中，权重 ≥ 3%）',
                ha='center', va='top', fontsize=14, fontweight='bold',
                transform=ax.transAxes)
        
        exclusive = summary_result['exclusive_stocks']
        
        if not exclusive:
            ax.text(0.5, 0.5, '暂无符合条件的独家持仓',
                   ha='center', va='center', fontsize=11, transform=ax.transAxes)
            return
        
        # 显示各基金的独家持仓
        y_start = 0.85
        for etf, stocks in exclusive.items():
            info = summary_result['etf_summaries'][etf]['info']
            
            ax.text(0.05, y_start, f"{info.emoji} {etf} - {info.name_cn}:",
                   fontsize=10, fontweight='bold', transform=ax.transAxes)
            
            for i, stock in enumerate(stocks[:3]):  # 最多显示3只
                y_pos = y_start - 0.04 * (i + 1)
                text = f"  • {stock['ticker']:6s}  {stock['company'][:30]:30s}  {stock['weight']:.1f}%"
                ax.text(0.08, y_pos, text, fontsize=9, transform=ax.transAxes)
            
            y_start -= 0.15
    
    def _draw_top_changes(self, ax, summary_result: dict):
        """绘制重点变化提示"""
        ax.axis('off')
        
        ax.text(0.5, 0.95, '🎯 今日重点变化',
                ha='center', va='top', fontsize=14, fontweight='bold',
                transform=ax.transAxes)
        
        changes = summary_result.get('top_changes', [])
        
        if not changes:
            ax.text(0.5, 0.5, '暂无重大变化',
                   ha='center', va='center', fontsize=11,
                   color='gray', transform=ax.transAxes)
            return
        
        # 显示前5条变化
        y_start = 0.80
        for i, change in enumerate(changes[:5]):
            # 类型图标
            type_icons = {
                'multi_increase': '📈',
                'multi_decrease': '📉',
                'new_overlap': '🆕',
                'new_multi': '⭐',
                'removed_multi': '❌'
            }
            icon = type_icons.get(change['type'], '•')
            
            # 描述
            desc = f"{icon} {change['description']}"
            ax.text(0.05, y_start - i * 0.15, desc,
                   fontsize=10, transform=ax.transAxes)
            
            # 详细信息
            ticker = change['ticker']
            company = change['company'][:25]
            detail = f"     {ticker} - {company}"
            ax.text(0.08, y_start - i * 0.15 - 0.05, detail,
                   fontsize=9, color='gray', transform=ax.transAxes)
    
    def combine_images_vertical(
        self,
        image_paths: List[str],
        output_path: str,
        spacing: int = 20,
        background_color: tuple = (255, 255, 255)
    ) -> str:
        """
        垂直拼接多张图片为一张长图
        
        Args:
            image_paths: 图片路径列表（从上到下的顺序）
            output_path: 输出路径
            spacing: 图片之间的间距（像素）
            background_color: 背景颜色 RGB
        
        Returns:
            输出图片路径
        """
        logger.info(f"开始拼接 {len(image_paths)} 张图片...")
        
        # 打开所有图片
        images = []
        for path in image_paths:
            try:
                img = Image.open(path)
                images.append(img)
                logger.debug(f"加载图片: {path} (尺寸: {img.size})")
            except Exception as e:
                logger.warning(f"无法加载图片 {path}: {e}")
        
        if not images:
            raise ValueError("没有有效的图片可拼接")
        
        # 计算总宽度和高度
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images) + spacing * (len(images) - 1)
        
        logger.info(f"拼接后尺寸: {max_width} x {total_height} 像素")
        
        # 创建空白画布
        combined_img = Image.new('RGB', (max_width, total_height), background_color)
        
        # 逐个粘贴图片
        y_offset = 0
        for i, img in enumerate(images):
            # 居中粘贴（如果图片宽度小于最大宽度）
            x_offset = (max_width - img.width) // 2
            combined_img.paste(img, (x_offset, y_offset))
            y_offset += img.height + spacing
            logger.debug(f"粘贴第 {i+1} 张图片，偏移: ({x_offset}, {y_offset - img.height - spacing})")
        
        # 保存拼接后的图片
        combined_img.save(output_path, format='PNG', optimize=True)
        logger.info(f"✅ 拼接完成: {output_path}")
        
        # 关闭图片
        for img in images:
            img.close()
        
        return output_path
        
        # 日度变化率（3 个月）（右下）
        daily_changes_3m = []
        for i in range(1, len(values_3m)):
            change_pct = (values_3m[i] - values_3m[i-1]) / values_3m[i-1] * 100
            daily_changes_3m.append(change_pct)
        
        ax4 = ax.figure.add_axes([pos.x0 + width + gap_h, pos.y0, width, height_bottom])
        colors = ['#00C853' if c >= 0 else '#D32F2F' for c in daily_changes_3m]
        ax4.bar(range(len(daily_changes_3m)), daily_changes_3m, color=colors, alpha=0.7)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax4.set_title('日度变化率 (3 个月)', fontsize=10, fontweight='bold')
        ax4.set_ylabel('变化率 (%)', fontsize=9)
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.tick_params(axis='x', labelsize=6, rotation=45)
    
    def _draw_top10_trend(self, ax, current_df, etf_symbol: str, date: str, csv_files, data_days):
        """在指定 Axes 上绘制 Top 10 个股趋势（1 个月 + 3 个月）"""
        import pandas as pd
        
        # 隐藏父 Axes
        ax.axis('off')
        
        # 获取当前 Top 10 股票
        current_top10 = current_df.nlargest(10, 'weight')['ticker'].tolist()
        
        # 读取历史数据并追踪这些股票的持股数变化
        stock_shares_1m = {ticker: [] for ticker in current_top10}
        stock_shares_3m = {ticker: [] for ticker in current_top10}
        dates_1m = []
        dates_3m = []
        
        # 1 个月数据
        for csv_file in csv_files[-30:]:
            try:
                df = pd.read_csv(csv_file)
                file_date = csv_file.stem
                dates_1m.append(file_date)
                
                for ticker in current_top10:
                    row = df[df['ticker'] == ticker]
                    shares = row.iloc[0]['shares'] if len(row) > 0 else 0
                    stock_shares_1m[ticker].append(shares)
            except Exception as e:
                logger.warning(f"读取文件失败 {csv_file}: {e}")
        
        # 3 个月数据
        for csv_file in csv_files[-90:]:
            try:
                df = pd.read_csv(csv_file)
                file_date = csv_file.stem
                if file_date not in dates_3m:
                    dates_3m.append(file_date)
                
                for ticker in current_top10:
                    row = df[df['ticker'] == ticker]
                    shares = row.iloc[0]['shares'] if len(row) > 0 else 0
                    stock_shares_3m[ticker].append(shares)
            except Exception as e:
                pass
        
        # 获取父 Axes 位置
        pos = ax.get_position()
        
        # 创建两个子图（并排）
        width = pos.width / 2.1
        gap = 0.02
        
        # 1 个月趋势（左）
        ax1 = ax.figure.add_axes([pos.x0, pos.y0, width, pos.height])
        
        for ticker in current_top10:
            if len(stock_shares_1m[ticker]) > 0:
                ax1.plot(range(len(dates_1m)), stock_shares_1m[ticker], 
                        marker='o', linewidth=1.5, markersize=3, label=ticker, alpha=0.8)
        
        ax1.set_title(f'{etf_symbol} Top 10 个股持股数趋势 - 最近 1 个月', fontsize=12, fontweight='bold')
        ax1.set_ylabel('持股数', fontsize=10)
        ax1.set_xlabel('日期', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best', fontsize=8, ncol=2)
        # 格式化Y轴（显示为M或K）
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'
        ))
        
        step = max(1, len(dates_1m) // 10)
        ax1.set_xticks(range(0, len(dates_1m), step))
        ax1.set_xticklabels([dates_1m[i] for i in range(0, len(dates_1m), step)], rotation=45, fontsize=7, ha='right')
        
        # 3 个月趋势（右）
        ax2 = ax.figure.add_axes([pos.x0 + width + gap, pos.y0, width, pos.height])
        
        for ticker in current_top10:
            if len(stock_shares_3m[ticker]) > 0:
                ax2.plot(range(len(dates_3m)), stock_shares_3m[ticker], 
                        marker='o', linewidth=1.5, markersize=2, label=ticker, alpha=0.8)
        
        ax2.set_title(f'{etf_symbol} Top 10 个股持股数趋势 - 最近 3 个月', fontsize=12, fontweight='bold')
        ax2.set_ylabel('持股数', fontsize=10)
        ax2.set_xlabel('日期', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='best', fontsize=8, ncol=2)
        # 格式化Y轴（显示为M或K）
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'
        ))
        
        step = max(1, len(dates_3m) // 15)
        ax2.set_xticks(range(0, len(dates_3m), step))
        ax2.set_xticklabels([dates_3m[i] for i in range(0, len(dates_3m), step)], rotation=45, fontsize=7, ha='right')
    
    def _draw_new_stocks_trend(
        self, 
        ax, 
        added_tickers: List[str], 
        current_df, 
        etf_symbol: str, 
        date: str, 
        csv_files
    ):
        """
        在指定 Axes 上绘制新增股票的持股数趋势
        
        Args:
            ax: Matplotlib Axes 对象
            added_tickers: 新增股票代码列表
            current_df: 当前持仓数据
            etf_symbol: ETF 代码
            date: 当前日期
            csv_files: 所有历史 CSV 文件列表
        """
        import pandas as pd
        
        # 隐藏父 Axes
        ax.axis('off')
        
        # 获取新增股票的当前信息（用于标题）
        new_stocks_info = []
        for ticker in added_tickers[:10]:  # 最多显示 10 只
            row = current_df[current_df['ticker'] == ticker]
            if len(row) > 0:
                company = row.iloc[0]['company']
                shares = row.iloc[0]['shares']
                new_stocks_info.append({
                    'ticker': ticker,
                    'company': company,
                    'shares': shares
                })
        
        # 按持股数排序（显示持股数最大的新增股票）
        new_stocks_info = sorted(new_stocks_info, key=lambda x: x['shares'], reverse=True)
        
        # 读取历史数据，追踪这些新增股票的持股数变化
        stock_shares = {stock['ticker']: [] for stock in new_stocks_info}
        dates = []
        
        # 读取所有历史数据
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                file_date = csv_file.stem
                dates.append(file_date)
                
                for stock in new_stocks_info:
                    ticker = stock['ticker']
                    row = df[df['ticker'] == ticker]
                    # 如果该股票在该日期存在，记录持股数；否则记录为 0
                    shares = row.iloc[0]['shares'] if len(row) > 0 else 0
                    stock_shares[ticker].append(shares)
            except Exception as e:
                logger.warning(f"读取文件失败 {csv_file}: {e}")
        
        # 获取父 Axes 位置
        pos = ax.get_position()
        
        # 创建单个图表（横跨整个宽度）
        ax1 = ax.figure.add_axes([pos.x0, pos.y0, pos.width, pos.height])
        
        # 为每只新增股票绘制趋势线
        colors = plt.cm.tab10(range(len(new_stocks_info)))
        
        for i, stock in enumerate(new_stocks_info):
            ticker = stock['ticker']
            company = stock['company'][:20]  # 限制长度
            shares_list = stock_shares[ticker]
            
            if len(shares_list) > 0:
                # 使用不同的线型来区分股票
                linestyle = '-' if i < 5 else '--'
                ax1.plot(
                    range(len(dates)), 
                    shares_list, 
                    marker='o', 
                    linewidth=2, 
                    markersize=4, 
                    label=f'{ticker} ({company})',
                    alpha=0.8,
                    color=colors[i],
                    linestyle=linestyle
                )
        
        # 设置标题和标签
        ax1.set_title(
            f'{etf_symbol} 新增持仓股票持股数趋势（按当前持股数排序，最多显示 10 只）', 
            fontsize=12, 
            fontweight='bold',
            pad=10
        )
        ax1.set_ylabel('持股数', fontsize=10)
        ax1.set_xlabel('日期', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # 图例（分两列显示）
        ax1.legend(loc='best', fontsize=8, ncol=2, framealpha=0.9)
        
        # 格式化Y轴（显示为M或K）
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'
        ))
        
        # X 轴日期标签（稀疏显示）
        step = max(1, len(dates) // 20)
        ax1.set_xticks(range(0, len(dates), step))
        ax1.set_xticklabels(
            [dates[i] for i in range(0, len(dates), step)], 
            rotation=45, 
            fontsize=7, 
            ha='right'
        )
        
        # 添加说明文字
        info_text = f"图中显示了最近新增的 {len(new_stocks_info)} 只股票的持股数变化\n"
        info_text += "横轴为 0 表示该股票在该日期不存在于持仓中"
        ax1.text(
            0.02, 0.98, 
            info_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
    
    def generate_summary_report_image(
        self,
        summary_result: dict,
        date: str
    ) -> str:
        """
        生成ARK全系列基金汇总报告长图
        
        Args:
            summary_result: 汇总分析结果（来自 SummaryAnalyzer）
            date: 当前日期
        
        Returns:
            生成的图片路径
        """
        logger.info("生成 ARK 全系列基金汇总报告长图")
        
        import pandas as pd
        from matplotlib.gridspec import GridSpec
        
        # 创建长图布局
        # 1. 统计摘要（高度: 10）
        # 2. 跨基金重叠 Top 10 + 趋势（高度: 18）
        # 3. 各基金 Top 5 持仓（高度: 14）
        # 4. 独家持仓亮点（高度: 10）
        # 5. 重点变化提示（高度: 8）
        
        total_height = 10 + 18 + 14 + 10 + 8  # 总高度 60
        fig = plt.figure(figsize=(14, total_height))
        
        gs = GridSpec(5, 1, figure=fig, height_ratios=[10, 18, 14, 10, 8], hspace=0.3)
        
        # ===== 1. 统计摘要 =====
        ax_stats = fig.add_subplot(gs[0])
        self._draw_summary_statistics(ax_stats, summary_result, date)
        
        # ===== 2. 跨基金重叠 Top 10 + 趋势 =====
        ax_overlap = fig.add_subplot(gs[1])
        self._draw_overlapping_stocks(ax_overlap, summary_result, date)
        
        # ===== 3. 各基金 Top 5 持仓 =====
        ax_etfs = fig.add_subplot(gs[2])
        self._draw_etf_top_holdings(ax_etfs, summary_result)
        
        # ===== 4. 独家持仓亮点 =====
        ax_exclusive = fig.add_subplot(gs[3])
        self._draw_exclusive_holdings(ax_exclusive, summary_result)
        
        # ===== 5. 重点变化提示 =====
        ax_changes = fig.add_subplot(gs[4])
        self._draw_top_changes(ax_changes, summary_result)
        
        # 保存图片
        image_dir = self.image_dir / "SUMMARY"
        ensure_dir(str(image_dir))
        
        image_path = image_dir / f"{date}_summary.png"
        plt.savefig(image_path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close()
        
        logger.info(f"汇总报告长图已保存: {image_path}")
        return str(image_path)
    
    def _draw_summary_statistics(self, ax, summary_result: dict, date: str):
        """绘制统计摘要部分"""
        ax.axis('off')
        
        stats = summary_result['statistics']
        summaries = summary_result['etf_summaries']
        
        # 标题
        title_text = f"ARK 全系列基金持仓监控报告\n{date}"
        ax.text(0.5, 0.95, title_text, ha='center', va='top', 
                fontsize=16, fontweight='bold', transform=ax.transAxes)
        
        # 5只基金对比表格
        table_data = []
        headers = ['基金', '中文名称', '投资方向', '持仓数', 'Top 1 持仓']
        
        for etf_symbol in ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']:
            if etf_symbol not in summaries:
                continue
            
            summary = summaries[etf_symbol]
            info = summary['info']
            top1 = summary['top_holdings'][0] if summary['top_holdings'] else None
            
            flag = ' ⭐' if info.is_flagship else ''
            top1_str = f"{top1.get('ticker', 'N/A')} {top1.get('weight', 0):.1f}%" if top1 else 'N/A'
            
            table_data.append([
                f"{info.emoji} {etf_symbol}{flag}",
                info.name_cn,
                info.focus[:25] + '...' if len(info.focus) > 25 else info.focus,
                str(summary['holdings_count']),
                top1_str
            ])
        
        # 创建表格
        table = ax.table(
            cellText=table_data,
            colLabels=headers,
            cellLoc='left',
            loc='center',
            bbox=[0.05, 0.40, 0.90, 0.45]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2.5)
        
        # 表头样式
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 行样式
        for i in range(1, len(table_data) + 1):
            for j in range(len(headers)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#F5F5F5')
        
        # 统计数字
        stats_text = (
            f"📊 总持仓股票: {stats['total_stocks']} 只  |  "
            f"🔥 跨基金重叠: {stats['overlapping_count']} 只  |  "
            f"💎 单基金独有: {stats['exclusive_count']} 只"
        )
        ax.text(0.5, 0.28, stats_text, ha='center', va='top',
                fontsize=11, fontweight='bold', transform=ax.transAxes,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 说明
        note = "💡 ARKK 是 Wood 姐的旗舰基金，涵盖最全面的创新技术投资"
        ax.text(0.5, 0.05, note, ha='center', va='bottom',
                fontsize=10, style='italic', transform=ax.transAxes)
    
    def _draw_overlapping_stocks(self, ax, summary_result: dict, date: str):
        """绘制跨基金重叠股票 Top 10 + 趋势"""
        ax.axis('off')
        
        overlapping = summary_result['overlapping_stocks'][:10]
        
        if not overlapping:
            ax.text(0.5, 0.5, '暂无跨基金重叠股票', 
                   ha='center', va='center', fontsize=12, transform=ax.transAxes)
            return
        
        # 标题
        ax.text(0.5, 0.98, '🔥 核心重叠持仓 Top 10（Wood 姐最看好的股票）',
                ha='center', va='top', fontsize=14, fontweight='bold',
                transform=ax.transAxes)
        
        # 表格数据
        table_data = []
        for i, stock in enumerate(overlapping, 1):
            ticker = stock['ticker']
            company = stock['company'][:20]
            num_funds = stock['num_funds']
            total_weight = stock['total_weight']
            
            # 构建基金分布字符串
            etf_dist = ' | '.join([
                f"{h['etf']} {h['weight']:.1f}%" 
                for h in stock['holdings'][:3]  # 最多显示3个
            ])
            
            table_data.append([
                str(i),
                ticker,
                company,
                f"{num_funds} 只",
                f"{total_weight:.1f}%",
                etf_dist
            ])
        
        # 创建表格
        headers = ['#', '代码', '公司名称', '基金数', '总权重', '分布']
        table = ax.table(
            cellText=table_data,
            colLabels=headers,
            cellLoc='left',
            loc='upper center',
            bbox=[0.05, 0.50, 0.90, 0.45]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2.0)
        
        # 样式
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#FF5722')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(1, len(table_data) + 1):
            for j in range(len(headers)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#FFF3E0')
        
        # 简化的趋势说明（由于没有历史数据，只显示当前状态）
        note = f"💡 以上股票同时出现在 2-{overlapping[0]['num_funds']} 只基金中，是 Wood 姐最核心的持仓"
        ax.text(0.5, 0.42, note, ha='center', va='top',
                fontsize=9, style='italic', transform=ax.transAxes,
                bbox=dict(boxstyle='round', facecolor='#FFEB3B', alpha=0.3))
    
    def _draw_etf_top_holdings(self, ax, summary_result: dict):
        """绘制各基金 Top 5 持仓"""
        ax.axis('off')
        
        ax.text(0.5, 0.98, '📈 各基金 Top 5 持仓详情',
                ha='center', va='top', fontsize=14, fontweight='bold',
                transform=ax.transAxes)
        
        summaries = summary_result['etf_summaries']
        etf_list = ['ARKK', 'ARKW', 'ARKG', 'ARKQ', 'ARKF']
        
        # 计算每个基金的位置（5行1列）
        y_positions = [0.85, 0.68, 0.51, 0.34, 0.17]
        
        for idx, etf_symbol in enumerate(etf_list):
            if etf_symbol not in summaries:
                continue
            
            summary = summaries[etf_symbol]
            info = summary['info']
            top_holdings = summary['top_holdings'][:5]
            
            y_start = y_positions[idx]
            
            # 基金名称
            flag = ' ⭐' if info.is_flagship else ''
            title = f"{info.emoji} {etf_symbol}{flag} - {info.name_cn} ({summary['holdings_count']} 只)"
            ax.text(0.05, y_start, title, fontsize=10, fontweight='bold',
                   transform=ax.transAxes)
            
            # Top 5 列表
            for i, holding in enumerate(top_holdings):
                y_pos = y_start - 0.025 * (i + 1)
                ticker = holding.get('ticker', 'N/A')
                company = holding.get('company', 'Unknown')[:25]
                weight = holding.get('weight', 0)
                text = f"  {i+1}. {ticker:6s}  {company:25s}  {weight:5.2f}%"
                ax.text(0.08, y_pos, text, fontsize=8, family='monospace',
                       transform=ax.transAxes)
    
    def _draw_exclusive_holdings(self, ax, summary_result: dict):
        """绘制独家持仓亮点（权重 >= 3%）"""
        ax.axis('off')
        
        ax.text(0.5, 0.95, '💎 独家持仓亮点（仅在单一基金中，权重 ≥ 3%）',
                ha='center', va='top', fontsize=14, fontweight='bold',
                transform=ax.transAxes)
        
        exclusive = summary_result['exclusive_stocks']
        
        if not exclusive:
            ax.text(0.5, 0.5, '暂无符合条件的独家持仓',
                   ha='center', va='center', fontsize=11, transform=ax.transAxes)
            return
        
        # 显示各基金的独家持仓
        y_start = 0.85
        for etf, stocks in exclusive.items():
            info = summary_result['etf_summaries'][etf]['info']
            
            ax.text(0.05, y_start, f"{info.emoji} {etf} - {info.name_cn}:",
                   fontsize=10, fontweight='bold', transform=ax.transAxes)
            
            for i, stock in enumerate(stocks[:3]):  # 最多显示3只
                y_pos = y_start - 0.04 * (i + 1)
                text = f"  • {stock['ticker']:6s}  {stock['company'][:30]:30s}  {stock['weight']:.1f}%"
                ax.text(0.08, y_pos, text, fontsize=9, transform=ax.transAxes)
            
            y_start -= 0.15
    
    def _draw_top_changes(self, ax, summary_result: dict):
        """绘制重点变化提示"""
        ax.axis('off')
        
        ax.text(0.5, 0.95, '🎯 今日重点变化',
                ha='center', va='top', fontsize=14, fontweight='bold',
                transform=ax.transAxes)
        
        changes = summary_result.get('top_changes', [])
        
        if not changes:
            ax.text(0.5, 0.5, '暂无重大变化',
                   ha='center', va='center', fontsize=11,
                   color='gray', transform=ax.transAxes)
            return
        
        # 显示前5条变化
        y_start = 0.80
        for i, change in enumerate(changes[:5]):
            # 类型图标
            type_icons = {
                'multi_increase': '📈',
                'multi_decrease': '📉',
                'new_overlap': '🆕',
                'new_multi': '⭐',
                'removed_multi': '❌'
            }
            icon = type_icons.get(change['type'], '•')
            
            # 描述
            desc = f"{icon} {change['description']}"
            ax.text(0.05, y_start - i * 0.15, desc,
                   fontsize=10, transform=ax.transAxes)
            
            # 详细信息
            ticker = change['ticker']
            company = change['company'][:25]
            detail = f"     {ticker} - {company}"
            ax.text(0.08, y_start - i * 0.15 - 0.05, detail,
                   fontsize=9, color='gray', transform=ax.transAxes)
    
    def combine_images_vertical(
        self,
        image_paths: List[str],
        output_path: str,
        spacing: int = 20,
        background_color: tuple = (255, 255, 255)
    ) -> str:
        """
        垂直拼接多张图片为一张长图
        
        Args:
            image_paths: 图片路径列表（从上到下的顺序）
            output_path: 输出路径
            spacing: 图片之间的间距（像素）
            background_color: 背景颜色 RGB
        
        Returns:
            输出图片路径
        """
        logger.info(f"开始拼接 {len(image_paths)} 张图片...")
        
        # 打开所有图片
        images = []
        for path in image_paths:
            try:
                img = Image.open(path)
                images.append(img)
                logger.debug(f"加载图片: {path} (尺寸: {img.size})")
            except Exception as e:
                logger.warning(f"无法加载图片 {path}: {e}")
        
        if not images:
            raise ValueError("没有有效的图片可拼接")
        
        # 计算总宽度和高度
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images) + spacing * (len(images) - 1)
        
        logger.info(f"拼接后尺寸: {max_width} x {total_height} 像素")
        
        # 创建空白画布
        combined_img = Image.new('RGB', (max_width, total_height), background_color)
        
        # 逐个粘贴图片
        y_offset = 0
        for i, img in enumerate(images):
            # 居中粘贴（如果图片宽度小于最大宽度）
            x_offset = (max_width - img.width) // 2
            combined_img.paste(img, (x_offset, y_offset))
            y_offset += img.height + spacing
            logger.debug(f"粘贴第 {i+1} 张图片，偏移: ({x_offset}, {y_offset - img.height - spacing})")
        
        # 保存拼接后的图片
        combined_img.save(output_path, format='PNG', optimize=True)
        logger.info(f"✅ 拼接完成: {output_path}")
        
        # 关闭图片
        for img in images:
            img.close()
        
        return output_path
