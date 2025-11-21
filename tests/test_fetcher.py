"""
测试数据获取模块

测试 src/fetcher.py 中的 DataFetcher 类
"""

import os
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.fetcher import DataFetcher
from src.utils import load_config, Config, DataConfig, RetryConfig


# ==================== Fixtures ====================

@pytest.fixture
def mock_config():
    """创建模拟配置"""
    config = MagicMock(spec=Config)
    config.data = MagicMock(spec=DataConfig)
    config.data.data_dir = "./test_data"
    config.retry = MagicMock(spec=RetryConfig)
    config.retry.max_retries = 3
    config.retry.retry_delays = [1, 2, 4]
    return config


@pytest.fixture
def fetcher(mock_config):
    """创建 DataFetcher 实例"""
    return DataFetcher(mock_config)


@pytest.fixture
def sample_csv_content():
    """模拟 ARK CSV 内容（GitHub 镜像格式，包含历史数据）"""
    return """date,fund,company,ticker,cusip,shares,market value($),weight(%)
2025-01-14,ARKK,Tesla Inc,TSLA,88160R101,1000000,250000000.00,10.50
2025-01-14,ARKK,Coinbase Global Inc,COIN,19260Q107,500000,100000000.00,4.20
2025-01-15,ARKK,Tesla Inc,TSLA,88160R101,1200000,300000000.00,11.80
2025-01-15,ARKK,Coinbase Global Inc,COIN,19260Q107,450000,90000000.00,3.50
2025-01-15,ARKK,Block Inc,SQ,852234103,800000,50000000.00,1.95
"""


@pytest.fixture
def sample_df():
    """模拟持仓数据 DataFrame（筛选后的最新日期数据）"""
    data = {
        'date': ['2025-01-15', '2025-01-15', '2025-01-15'],
        'company': ['Tesla Inc', 'Coinbase Global Inc', 'Block Inc'],
        'ticker': ['TSLA', 'COIN', 'SQ'],
        'cusip': ['88160R101', '19260Q107', '852234103'],
        'shares': [1200000, 450000, 800000],
        'market_value': [300000000.00, 90000000.00, 50000000.00],
        'weight': [11.80, 3.50, 1.95]
    }
    return pd.DataFrame(data)


# ==================== 测试数据获取 ====================

class TestDataFetching:
    """测试数据下载功能"""
    
    @patch('src.fetcher.requests.get')
    def test_fetch_holdings_success(self, mock_get, fetcher, sample_csv_content):
        """测试成功下载持仓数据"""
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_csv_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 执行下载
        df = fetcher.fetch_holdings('ARKK', '2025-01-15')
        
        # 验证结果
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'ticker' in df.columns
        assert 'company' in df.columns
        assert 'shares' in df.columns
        assert 'weight' in df.columns
        
        # 验证只保留最新日期数据（2025-01-15）
        if 'date' in df.columns:
            unique_dates = df['date'].unique()
            assert len(unique_dates) == 1  # 只有一个日期
    
    @patch('src.fetcher.requests.get')
    def test_fetch_holdings_retry_on_failure(self, mock_get, fetcher, sample_csv_content):
        """测试网络失败后重试机制"""
        # Mock: 前 2 次失败，第 3 次成功
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("Network error")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.text = sample_csv_content
        mock_response_success.raise_for_status = Mock()
        
        mock_get.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]
        
        # 执行下载（应该重试并成功）
        df = fetcher.fetch_holdings('ARKK', '2025-01-15')
        
        # 验证重试了 3 次
        assert mock_get.call_count == 3
        
        # 验证最终成功
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
    
    @patch('src.fetcher.requests.get')
    def test_fetch_holdings_max_retries_exceeded(self, mock_get, fetcher):
        """测试超过最大重试次数后抛出异常"""
        # Mock: 所有请求都失败
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Network error")
        mock_get.return_value = mock_response
        
        # 执行下载（应该抛出异常）
        with pytest.raises(Exception):
            fetcher.fetch_holdings('ARKK', '2025-01-15')
        
        # 验证重试了 3 次
        assert mock_get.call_count == 3
    
    @patch('src.fetcher.requests.get')
    def test_fetch_holdings_with_user_agent(self, mock_get, fetcher, sample_csv_content):
        """测试请求包含 User-Agent 头"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_csv_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 执行下载
        fetcher.fetch_holdings('ARKK', '2025-01-15')
        
        # 验证请求包含 User-Agent
        call_args = mock_get.call_args
        headers = call_args[1].get('headers', {})
        assert 'User-Agent' in headers
        assert 'Mozilla' in headers['User-Agent']


# ==================== 测试数据保存和加载 ====================

class TestDataPersistence:
    """测试数据持久化功能"""
    
    def test_save_to_csv(self, fetcher, sample_df, tmp_path):
        """测试保存 CSV 文件"""
        # 修改配置的数据目录
        fetcher.config.data.data_dir = str(tmp_path)
        
        # 保存数据
        fetcher.save_to_csv(sample_df, 'ARKK', '2025-01-15')
        
        # 验证文件存在
        expected_path = tmp_path / "holdings" / "ARKK" / "2025-01-15.csv"
        assert expected_path.exists()
        
        # 验证文件内容
        df_loaded = pd.read_csv(expected_path)
        assert len(df_loaded) == len(sample_df)
        assert list(df_loaded.columns) == list(sample_df.columns)
    
    def test_save_to_csv_creates_directory(self, fetcher, sample_df, tmp_path):
        """测试自动创建目录"""
        fetcher.config.data.data_dir = str(tmp_path)
        
        # 保存数据（目录不存在）
        fetcher.save_to_csv(sample_df, 'ARKW', '2025-01-15')
        
        # 验证目录被创建
        expected_dir = tmp_path / "holdings" / "ARKW"
        assert expected_dir.exists()
        assert expected_dir.is_dir()
    
    def test_load_from_csv(self, fetcher, sample_df, tmp_path):
        """测试从 CSV 文件加载数据"""
        fetcher.config.data.data_dir = str(tmp_path)
        
        # 先保存数据
        fetcher.save_to_csv(sample_df, 'ARKK', '2025-01-15')
        
        # 加载数据
        df_loaded = fetcher.load_from_csv('ARKK', '2025-01-15')
        
        # 验证数据正确
        assert isinstance(df_loaded, pd.DataFrame)
        assert len(df_loaded) == len(sample_df)
        
        # 验证关键列存在
        assert 'ticker' in df_loaded.columns
        assert 'company' in df_loaded.columns
    
    def test_load_from_csv_file_not_found(self, fetcher, tmp_path):
        """测试加载不存在的文件抛出异常"""
        fetcher.config.data.data_dir = str(tmp_path)
        
        # 尝试加载不存在的文件
        with pytest.raises(FileNotFoundError):
            fetcher.load_from_csv('ARKK', '2025-01-15')


# ==================== 测试 CSV 转换和清洗 ====================

class TestCSVTransformation:
    """测试 CSV 数据转换和清洗"""
    
    @patch('src.fetcher.requests.get')
    def test_column_name_normalization(self, mock_get, fetcher):
        """测试列名标准化"""
        # Mock CSV 数据（带特殊字符的列名）
        csv_content = """date,fund,company,ticker,cusip,shares,market value($),weight(%)
2025-01-15,ARKK,Tesla Inc,TSLA,88160R101,1000000,250000000.00,10.50
"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = csv_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 执行下载
        df = fetcher.fetch_holdings('ARKK', '2025-01-15')
        
        # 验证列名被标准化
        assert 'market_value' in df.columns  # "market value($)" → "market_value"
        assert 'weight' in df.columns  # "weight(%)" → "weight"
    
    @patch('src.fetcher.requests.get')
    def test_numeric_type_conversion(self, mock_get, fetcher):
        """测试数值类型转换"""
        csv_content = """date,fund,company,ticker,cusip,shares,market value($),weight(%)
2025-01-15,ARKK,Tesla Inc,TSLA,88160R101,1000000,250000000.00,10.50
"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = csv_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 执行下载
        df = fetcher.fetch_holdings('ARKK', '2025-01-15')
        
        # 验证数值列的数据类型
        assert pd.api.types.is_numeric_dtype(df['shares'])
        assert pd.api.types.is_numeric_dtype(df['market_value'])
        assert pd.api.types.is_numeric_dtype(df['weight'])
    
    @patch('src.fetcher.requests.get')
    def test_filter_latest_date_from_history(self, mock_get, fetcher, sample_csv_content):
        """测试从历史数据中筛选最新日期"""
        # Mock 包含多个日期的 CSV（GitHub 镜像格式）
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_csv_content  # 包含 2025-01-14 和 2025-01-15
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 执行下载
        df = fetcher.fetch_holdings('ARKK', '2025-01-15')
        
        # 验证只保留最新日期（2025-01-15）
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            max_date = df['date'].max()
            assert all(df['date'] == max_date)
        
        # 验证数据行数（2025-01-15 有 3 行）
        assert len(df) == 3


# ==================== 集成测试 ====================

class TestDataFetcherIntegration:
    """集成测试（完整流程）"""
    
    @patch('src.fetcher.requests.get')
    def test_full_workflow(self, mock_get, fetcher, sample_csv_content, tmp_path):
        """测试完整工作流：下载 → 保存 → 加载"""
        fetcher.config.data.data_dir = str(tmp_path)
        
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_csv_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 1. 下载数据
        df_fetched = fetcher.fetch_holdings('ARKK', '2025-01-15')
        assert len(df_fetched) > 0
        
        # 2. 保存数据
        fetcher.save_to_csv(df_fetched, 'ARKK', '2025-01-15')
        
        # 3. 加载数据
        df_loaded = fetcher.load_from_csv('ARKK', '2025-01-15')
        
        # 4. 验证数据一致性
        assert len(df_loaded) == len(df_fetched)
        assert set(df_loaded['ticker'].tolist()) == set(df_fetched['ticker'].tolist())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
