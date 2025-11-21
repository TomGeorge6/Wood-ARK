"""
数据获取模块

负责从 ARK 官网下载持仓数据，并保存/加载本地 CSV 文件。
"""

import os
import time
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import Optional

from .utils import Config, ensure_dir, get_holding_file_path


logger = logging.getLogger(__name__)


class DataFetcher:
    """
    数据获取类
    
    负责：
    1. 从数据源下载持仓 CSV 数据
    2. 保存数据到本地文件
    3. 从本地文件加载数据
    """
    
    # ARK 官方 CSV 文件名映射（已废弃，官网有反爬虫保护）
    ETF_FULL_NAMES = {
        'ARKK': 'ARK_INNOVATION_ETF_ARKK_HOLDINGS',
        'ARKQ': 'ARK_AUTONOMOUS_TECHNOLOGY_&_ROBOTICS_ETF_ARKQ_HOLDINGS',
        'ARKW': 'ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS',
        'ARKG': 'ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS',
        'ARKF': 'ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS',
    }
    
    # 主数据源：ARKFunds.io API（推荐，数据最新）
    # 由开源项目维护，数据来源于 ARK Invest 官方
    # GitHub: https://github.com/frefrik/ark-invest-api
    # 返回格式：JSON，包含当日最新持仓数据
    ARKFUNDS_API_TEMPLATE = "https://arkfunds.io/api/v1/etf/holdings?symbol={etf_symbol}"
    
    # 备用数据源1：GitHub 历史数据（仅用于历史回溯）
    # 注意：此数据源已停止更新（最后更新 2021-09-08）
    # 仅用于下载历史数据，不应作为主数据源
    GITHUB_URL_TEMPLATE = "https://raw.githubusercontent.com/thisjustinh/ark-invest-history/master/fund-holdings/{etf_symbol}.csv"
    
    # 备用数据源2：ARK 官网（不可用）
    # ARK 官网存在 Cloudflare 保护，经测试会返回 403/404 错误
    # ARK_URL_TEMPLATE = "https://ark-funds.com/wp-content/fundsiteliterature/csv/{full_name}.csv"
    
    def __init__(self, config: Config):
        """
        初始化 DataFetcher
        
        Args:
            config: 系统配置对象
        """
        self.config = config
        self.timeout = 30  # HTTP 请求超时时间（秒）
    
    def fetch_holdings(self, etf_symbol: str, date: str) -> pd.DataFrame:
        """
        下载指定 ETF 的持仓数据（使用真实API）
        
        Args:
            etf_symbol: ETF 代码（如 'ARKK'）
            date: 日期字符串 YYYY-MM-DD（用于标记数据，API返回最新数据）
            
        Returns:
            包含持仓数据的 DataFrame，列名：
            ['date', 'etf_symbol', 'company', 'ticker', 'cusip', 'shares', 'market_value', 'weight']
            
        Raises:
            requests.RequestException: 网络请求失败
            ValueError: 数据格式不正确或缺少必需列
        """
        # 检查 ETF 是否支持
        if etf_symbol not in self.ETF_FULL_NAMES:
            logger.error(f"不支持的 ETF 代码: {etf_symbol}，支持的代码: {list(self.ETF_FULL_NAMES.keys())}")
            raise ValueError(f"不支持的 ETF 代码: {etf_symbol}")
        
        # 优先使用 ARKFunds.io API（真实数据）
        url = self.ARKFUNDS_API_TEMPLATE.format(etf_symbol=etf_symbol)
        logger.info(f"开始下载 {etf_symbol} 持仓数据: {url}")
        
        try:
            # 使用重试机制下载JSON数据
            json_data = self._download_json_with_retry(url)
            
            # 转换JSON为DataFrame
            df = self._transform_json(json_data, etf_symbol, date)
            
            logger.info(f"✅ {etf_symbol} 数据下载成功，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"ARKFunds.io API 获取失败: {e}")
            logger.warning("注意：当前没有可用的真实数据源")
            raise
    
    def _download_json_with_retry(self, url: str) -> dict:
        """
        使用重试机制下载 JSON 数据
        
        Args:
            url: API URL
            
        Returns:
            JSON 响应数据（字典）
            
        Raises:
            requests.RequestException: 重试耗尽后仍失败
        """
        max_retries = self.config.retry.max_retries
        retry_delays = self.config.retry.retry_delays
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"尝试下载 (第 {attempt + 1}/{max_retries} 次)...")
                
                # 添加 User-Agent
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, timeout=self.timeout, headers=headers)
                response.raise_for_status()  # 抛出 HTTP 错误
                
                # 解析 JSON
                json_data = response.json()
                
                logger.debug(f"下载成功，数据日期: {json_data.get('date', 'unknown')}")
                return json_data
            
            except (requests.RequestException, ValueError) as e:
                last_exception = e
                logger.warning(f"下载失败 (第 {attempt + 1} 次): {e}")
                
                # 如果还有重试机会，等待后重试
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
        
        # 所有重试都失败
        error_msg = f"下载失败，已重试 {max_retries} 次: {last_exception}"
        logger.error(error_msg)
        raise requests.RequestException(error_msg)
    
    def _transform_json(
        self, 
        json_data: dict, 
        etf_symbol: str, 
        date: str
    ) -> pd.DataFrame:
        """
        转换 ARKFunds.io API JSON 格式到标准 DataFrame
        
        Args:
            json_data: API 返回的 JSON 数据
            etf_symbol: ETF 代码
            date: 日期（用于覆盖API返回的日期，如果需要）
            
        Returns:
            转换后的 DataFrame
            
        Raises:
            ValueError: 缺少必需字段或数据格式错误
        """
        logger.info(f"转换 JSON 数据到 DataFrame...")
        
        # 验证 JSON 结构
        if 'holdings' not in json_data:
            raise ValueError("JSON 数据缺少 'holdings' 字段")
        
        holdings = json_data['holdings']
        api_date = json_data.get('date', date)  # 使用API返回的日期
        
        logger.info(f"API 数据日期: {api_date}, 持仓数量: {len(holdings)}")
        
        # 转换为 DataFrame
        df = pd.DataFrame(holdings)
        
        # 添加日期和 ETF 代码列
        df['date'] = api_date
        df['etf_symbol'] = etf_symbol
        
        # 确保必需列存在
        required_columns = ['company', 'ticker', 'shares', 'market_value', 'weight']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(
                f"JSON 数据缺少必需字段: {missing_columns}\n"
                f"实际字段: {df.columns.tolist()}"
            )
        
        # 处理 ticker 为 null 的情况（某些资产没有ticker，如货币基金）
        df['ticker'] = df['ticker'].fillna('N/A')
        
        # 确保 cusip 列存在
        if 'cusip' not in df.columns:
            df['cusip'] = None
        
        # 选择并排序列
        final_columns = [
            'date', 'etf_symbol', 'company', 'ticker', 
            'cusip', 'shares', 'market_value', 'weight'
        ]
        
        df = df[final_columns]
        
        # 数据类型转换
        df['shares'] = pd.to_numeric(df['shares'], errors='coerce')
        df['market_value'] = pd.to_numeric(df['market_value'], errors='coerce')
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
        
        # 删除无效行
        original_count = len(df)
        df = df.dropna(subset=['ticker', 'shares'])
        dropped_count = original_count - len(df)
        
        if dropped_count > 0:
            logger.warning(f"删除 {dropped_count} 条无效记录")
        
        logger.info(f"✅ 数据转换成功，有效记录: {len(df)} 条")
        return df
    
    def _download_with_retry(self, url: str) -> pd.DataFrame:
        """
        使用重试机制下载 CSV
        
        Args:
            url: CSV 文件 URL
            
        Returns:
            原始 DataFrame
            
        Raises:
            requests.RequestException: 重试耗尽后仍失败
        """
        max_retries = self.config.retry.max_retries
        retry_delays = self.config.retry.retry_delays
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"尝试下载 (第 {attempt + 1}/{max_retries} 次)...")
                
                # 添加 User-Agent 避免 403 错误
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, timeout=self.timeout, headers=headers)
                response.raise_for_status()  # 抛出 HTTP 错误
                
                # 使用 pandas 读取 CSV
                # 尝试检测分隔符类型
                text_sample = response.text[:1000]  # 取前1000个字符检测
                
                if '\t' in text_sample:
                    # Tab 分隔
                    sep = '\t'
                elif ',' in text_sample.split('\n')[0]:
                    # 逗号分隔
                    sep = ','
                else:
                    # 多个空格分隔
                    sep = r'\s+'
                
                df = pd.read_csv(
                    pd.io.common.StringIO(response.text),
                    encoding='utf-8',
                    sep=sep,
                    engine='python' if sep == r'\s+' else 'c'
                )
                
                logger.debug(f"下载成功，原始列名: {df.columns.tolist()}")
                return df
            
            except (requests.RequestException, pd.errors.ParserError) as e:
                last_exception = e
                logger.warning(f"下载失败 (第 {attempt + 1} 次): {e}")
                
                # 如果还有重试机会，等待后重试
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
        
        # 所有重试都失败
        error_msg = f"下载失败，已重试 {max_retries} 次: {last_exception}"
        logger.error(error_msg)
        raise requests.RequestException(error_msg)
    
    def _transform_csv(
        self, 
        df: pd.DataFrame, 
        etf_symbol: str, 
        date: str
    ) -> pd.DataFrame:
        """
        转换 ARK CSV 格式到标准格式
        
        Args:
            df: 原始 DataFrame
            etf_symbol: ETF 代码
            date: 日期
            
        Returns:
            转换后的 DataFrame
            
        Raises:
            ValueError: 缺少必需列或数据格式错误
        """
        # 0. 如果是 GitHub 历史数据格式，筛选最新日期
        # GitHub 数据包含所有历史记录（数千行），需自动筛选最新日期
        # 列名第一列是 date（或需要转换为 date）
        if 'date' in df.columns or df.columns[0].lower() == 'date':
            logger.info("检测到历史数据格式，筛选最新日期")
            
            # 确保第一列是 date
            if df.columns[0] != 'date':
                df.columns = ['date'] + list(df.columns[1:])
            
            # 转换日期并筛选最新
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            
            max_date = df['date'].max()
            df = df[df['date'] == max_date].copy()
            
            logger.info(f"筛选出最新日期 {max_date.strftime('%Y-%m-%d')} 的数据，共 {len(df)} 条")
            
            # 转换日期格式为字符串
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # 1. 清理列名（去除空格、转小写、替换特殊字符）
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(r'[^a-z0-9]', '_', regex=True)
            .str.replace(r'_+', '_', regex=True)
            .str.strip('_')
        )
        
        logger.debug(f"清理后列名: {df.columns.tolist()}")
        
        # 2. 列名映射（ARK CSV 列名 → 标准列名）
        # ARK CSV 常见列名：date, fund, company, ticker, cusip, shares, market_value, weight
        column_mapping = {
            'fund': 'etf_symbol',
            'market_value': 'market_value',
            'weight': 'weight'
        }
        
        # 尝试多种可能的列名变体
        for original_col in df.columns:
            # 处理带美元符号的列名（如 market_value_$）
            if 'market' in original_col and 'value' in original_col:
                column_mapping[original_col] = 'market_value'
            # 处理带百分号的列名（如 weight_%）
            elif 'weight' in original_col:
                column_mapping[original_col] = 'weight'
        
        df = df.rename(columns=column_mapping)
        
        # 3. 验证必需列
        required_columns = ['company', 'ticker', 'shares', 'market_value', 'weight']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(
                f"CSV 缺少必需列: {missing_columns}\n"
                f"实际列名: {df.columns.tolist()}"
            )
        
        # 4. 添加日期和 ETF 代码列
        if 'date' not in df.columns:
            df['date'] = date
        else:
            # 转换日期格式（如果存在）
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        if 'etf_symbol' not in df.columns:
            df['etf_symbol'] = etf_symbol
        
        # 5. 数值类型转换
        df['shares'] = pd.to_numeric(df['shares'], errors='coerce')
        df['market_value'] = pd.to_numeric(df['market_value'], errors='coerce')
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
        
        # 6. 删除无效行（ticker 或 shares 为空）
        original_count = len(df)
        df = df.dropna(subset=['ticker', 'shares'])
        dropped_count = original_count - len(df)
        
        if dropped_count > 0:
            logger.warning(f"删除 {dropped_count} 条无效记录")
        
        # 7. 选择并排序列
        final_columns = [
            'date', 'etf_symbol', 'company', 'ticker', 
            'cusip', 'shares', 'market_value', 'weight'
        ]
        
        # 添加缺失的可选列（如 cusip）
        for col in final_columns:
            if col not in df.columns:
                df[col] = None
        
        df = df[final_columns]
        
        return df
    
    def save_to_csv(
        self, 
        df: pd.DataFrame, 
        etf_symbol: str, 
        date: str
    ) -> None:
        """
        保存持仓数据到 CSV 文件
        
        Args:
            df: 持仓数据 DataFrame
            etf_symbol: ETF 代码
            date: 日期字符串 YYYY-MM-DD
            
        Raises:
            IOError: 文件写入失败
            
        Side Effects:
            - 创建目录 data/holdings/{etf_symbol}/（如不存在）
            - 如文件已存在，记录警告日志但不覆盖
        """
        file_path = get_holding_file_path(
            self.config.data.data_dir, 
            etf_symbol, 
            date
        )
        
        # 检查文件是否已存在
        if os.path.exists(file_path):
            logger.warning(
                f"文件已存在，跳过保存: {file_path}\n"
                f"（符合 Constitution 不可变历史原则）"
            )
            return
        
        # 创建目录
        ensure_dir(os.path.dirname(file_path))
        
        # 保存 CSV
        try:
            df.to_csv(file_path, index=False, encoding='utf-8', sep=',')
            logger.info(f"✅ 数据已保存: {file_path}")
        except IOError as e:
            error_msg = f"文件保存失败 {file_path}: {e}"
            logger.error(error_msg)
            raise IOError(error_msg)
    
    def load_from_csv(self, etf_symbol: str, date: str) -> pd.DataFrame:
        """
        从本地 CSV 文件加载持仓数据
        
        Args:
            etf_symbol: ETF 代码
            date: 日期字符串 YYYY-MM-DD
            
        Returns:
            持仓数据 DataFrame
            
        Raises:
            FileNotFoundError: 文件不存在
            pd.errors.ParserError: CSV 解析失败
        """
        file_path = get_holding_file_path(
            self.config.data.data_dir,
            etf_symbol,
            date
        )
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"持仓数据文件不存在: {file_path}\n"
                f"请先运行数据下载任务"
            )
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            logger.debug(f"从本地加载数据: {file_path}，共 {len(df)} 条记录")
            return df
        except pd.errors.ParserError as e:
            error_msg = f"CSV 解析失败 {file_path}: {e}"
            logger.error(error_msg)
            raise pd.errors.ParserError(error_msg)
    
    def file_exists(self, etf_symbol: str, date: str) -> bool:
        """
        检查持仓数据文件是否存在
        
        Args:
            etf_symbol: ETF 代码
            date: 日期
            
        Returns:
            True 表示文件存在
        """
        file_path = get_holding_file_path(
            self.config.data.data_dir,
            etf_symbol,
            date
        )
        return os.path.exists(file_path)
    
    def download_historical_data(
        self, 
        etf_symbol: str, 
        days: int = 90
    ) -> int:
        """
        从 GitHub 下载历史数据并保存
        
        Args:
            etf_symbol: ETF 代码
            days: 下载最近多少天的数据
            
        Returns:
            成功下载的文件数量
        """
        from datetime import datetime, timedelta
        
        logger.info(f"开始下载 {etf_symbol} 最近 {days} 天的历史数据")
        
        # 下载 GitHub 完整历史数据
        url = self.GITHUB_URL_TEMPLATE.format(etf_symbol=etf_symbol)
        logger.info(f"从 GitHub 下载历史数据: {url}")
        
        try:
            # 下载完整历史数据
            df_all = self._download_with_retry(url)
            
            # 确保第一列是 date
            if df_all.columns[0] != 'date':
                df_all.columns = ['date'] + list(df_all.columns[1:])
            
            # 转换日期列
            df_all['date'] = pd.to_datetime(df_all['date'], errors='coerce')
            df_all = df_all.dropna(subset=['date'])
            
            # 计算日期范围
            end_date = df_all['date'].max()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"历史数据时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
            
            # 筛选指定天数的数据
            df_filtered = df_all[df_all['date'] >= start_date].copy()
            
            # 按日期分组保存
            success_count = 0
            dates = sorted(df_filtered['date'].unique())
            
            for date in dates:
                date_str = date.strftime('%Y-%m-%d')
                
                # 检查文件是否已存在
                if self.file_exists(etf_symbol, date_str):
                    logger.debug(f"文件已存在，跳过: {etf_symbol}/{date_str}")
                    continue
                
                # 筛选当天数据
                df_day = df_filtered[df_filtered['date'] == date].copy()
                
                # 转换格式
                df_day = self._transform_csv(df_day, etf_symbol, date_str)
                
                # 保存文件
                self.save_to_csv(df_day, etf_symbol, date_str)
                success_count += 1
            
            logger.info(f"✅ {etf_symbol} 历史数据下载完成: 新增 {success_count} 个文件")
            return success_count
            
        except Exception as e:
            logger.error(f"❌ {etf_symbol} 历史数据下载失败: {e}")
            return 0
    
    def cleanup_old_data(self, retention_days: int = 90) -> dict:
        """
        清理过期的历史数据
        
        Args:
            retention_days: 数据保留天数（默认 90 天）
            
        Returns:
            清理统计 {'etf': {'deleted_count': X, 'deleted_files': [...]}}
        """
        from datetime import datetime, timedelta
        
        logger.info(f"开始清理过期数据（保留 {retention_days} 天）")
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        logger.info(f"删除早于 {cutoff_str} 的数据")
        
        stats = {}
        holdings_dir = Path(self.config.data.data_dir) / "holdings"
        
        if not holdings_dir.exists():
            logger.warning(f"数据目录不存在: {holdings_dir}")
            return stats
        
        # 遍历每个 ETF 目录
        for etf_dir in holdings_dir.iterdir():
            if not etf_dir.is_dir():
                continue
            
            etf_symbol = etf_dir.name
            deleted_files = []
            
            # 遍历该 ETF 的所有 CSV 文件
            for csv_file in etf_dir.glob("*.csv"):
                try:
                    # 从文件名提取日期（格式：YYYY-MM-DD.csv）
                    file_date_str = csv_file.stem
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                    
                    # 如果早于截止日期，删除
                    if file_date < cutoff_date:
                        csv_file.unlink()
                        deleted_files.append(file_date_str)
                        logger.debug(f"删除过期文件: {csv_file}")
                
                except (ValueError, OSError) as e:
                    logger.warning(f"处理文件失败 {csv_file}: {e}")
            
            if deleted_files:
                stats[etf_symbol] = {
                    'deleted_count': len(deleted_files),
                    'deleted_files': sorted(deleted_files)
                }
                logger.info(f"✅ {etf_symbol}: 删除 {len(deleted_files)} 个过期文件")
        
        total_deleted = sum(s['deleted_count'] for s in stats.values())
        logger.info(f"清理完成: 共删除 {total_deleted} 个过期文件")
        
        return stats

