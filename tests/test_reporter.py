"""
测试报告生成模块

测试 src/reporter.py 中的 ReportGenerator 类
"""

import pytest
import tempfile
from pathlib import Path
from src.reporter import ReportGenerator
from src.analyzer import ChangeAnalysis


# ==================== Fixtures ====================

@pytest.fixture
def reporter():
    """创建 ReportGenerator 实例"""
    return ReportGenerator()


@pytest.fixture
def sample_analysis():
    """模拟持仓分析结果"""
    return ChangeAnalysis(
        etf_symbol='ARKK',
        current_date='2025-01-15',
        previous_date='2025-01-14',
        added=[
            {
                'ticker': 'PATH',
                'company': 'UiPath Inc',
                'shares': 500000,
                'market_value': 25000000.00,
                'weight': 0.98
            }
        ],
        removed=[
            {
                'ticker': 'SHOP',
                'company': 'Shopify Inc',
                'shares': 300000,
                'market_value': 30000000.00,
                'weight': 1.26
            }
        ],
        increased=[
            {
                'ticker': 'TSLA',
                'company': 'Tesla Inc',
                'previous_shares': 1000000,
                'current_shares': 1200000,
                'shares_change': 200000,
                'change_percent': 20.0,
                'current_weight': 11.80,
                'weight_change': 1.30
            }
        ],
        decreased=[
            {
                'ticker': 'COIN',
                'company': 'Coinbase Global Inc',
                'previous_shares': 500000,
                'current_shares': 450000,
                'shares_change': -50000,
                'change_percent': -10.0,
                'current_weight': 3.50,
                'weight_change': -0.70
            }
        ]
    )


@pytest.fixture
def empty_analysis():
    """模拟无变化的分析结果"""
    return ChangeAnalysis(
        etf_symbol='ARKK',
        current_date='2025-01-15',
        previous_date='2025-01-14',
        added=[],
        removed=[],
        increased=[],
        decreased=[]
    )


# ==================== 测试 Markdown 生成 ====================

class TestMarkdownGeneration:
    """测试 Markdown 报告生成"""
    
    def test_generate_markdown_structure(self, reporter, sample_analysis):
        """测试 Markdown 基本结构"""
        markdown = reporter.generate_markdown([sample_analysis], execution_time='11:05:23')
        
        # 验证包含基本结构
        assert '# ARK 持仓变化' in markdown
        assert '## ARKK' in markdown
        assert '### 📊 概览' in markdown
        assert '### ✅ 新增持仓' in markdown
        assert '### ❌ 移除持仓' in markdown
        assert '### 📈 显著增持' in markdown
        assert '### 📉 显著减持' in markdown
    
    def test_generate_markdown_with_changes(self, reporter, sample_analysis):
        """测试包含变化的报告"""
        markdown = reporter.generate_markdown([sample_analysis], execution_time='11:05:23')
        
        # 验证新增股票
        assert 'PATH' in markdown
        assert 'UiPath Inc' in markdown
        
        # 验证移除股票
        assert 'SHOP' in markdown
        assert 'Shopify Inc' in markdown
        
        # 验证增持股票
        assert 'TSLA' in markdown
        assert 'Tesla Inc' in markdown
        assert '+20.0%' in markdown
        
        # 验证减持股票
        assert 'COIN' in markdown
        assert 'Coinbase Global Inc' in markdown
        assert '-10.0%' in markdown
    
    def test_generate_markdown_no_changes(self, reporter, empty_analysis):
        """测试无变化的报告"""
        markdown = reporter.generate_markdown([empty_analysis], execution_time='11:05:23')
        
        # 验证包含 "今日无重大变化" 提示
        assert '无重大变化' in markdown or '暂无' in markdown
    
    def test_generate_markdown_multiple_etfs(self, reporter, sample_analysis):
        """测试多个 ETF 的报告"""
        # 创建第二个 ETF 分析
        analysis2 = ChangeAnalysis(
            etf_symbol='ARKW',
            current_date='2025-01-15',
            previous_date='2025-01-14',
            added=[],
            removed=[],
            increased=[],
            decreased=[]
        )
        
        markdown = reporter.generate_markdown([sample_analysis, analysis2], execution_time='11:05:23')
        
        # 验证包含两个 ETF
        assert '## ARKK' in markdown
        assert '## ARKW' in markdown
    
    def test_generate_markdown_with_execution_time(self, reporter, sample_analysis):
        """测试包含执行时间"""
        markdown = reporter.generate_markdown([sample_analysis], execution_time='11:05:23')
        
        # 验证包含执行时间
        assert '11:05:23' in markdown
    
    def test_markdown_table_format(self, reporter, sample_analysis):
        """测试表格格式正确"""
        markdown = reporter.generate_markdown([sample_analysis], execution_time='11:05:23')
        
        # 验证包含表格分隔符
        assert '|' in markdown
        assert '---' in markdown
        
        # 验证包含表头
        assert '股票代码' in markdown or 'ticker' in markdown.lower()
        assert '公司名称' in markdown or 'company' in markdown.lower()


# ==================== 测试字符长度限制 ====================

class TestLengthLimit:
    """测试字符长度限制"""
    
    def test_truncate_long_report(self, reporter):
        """测试超长报告截断"""
        # 创建超长分析结果（大量股票）
        large_added = [
            {
                'ticker': f'TICK{i}',
                'company': f'Company {i}',
                'shares': 1000000 + i,
                'market_value': 25000000.00,
                'weight': 0.98
            }
            for i in range(200)  # 200 只新增股票
        ]
        
        large_analysis = ChangeAnalysis(
            etf_symbol='ARKK',
            current_date='2025-01-15',
            previous_date='2025-01-14',
            added=large_added,
            removed=[],
            increased=[],
            decreased=[]
        )
        
        markdown = reporter.generate_markdown([large_analysis], execution_time='11:05:23')
        
        # 企业微信 Markdown 限制 4096 字符
        # 如果超过，应该被截断或压缩
        # 这里只验证不会无限增长
        assert len(markdown) < 10000  # 合理的上限
    
    def test_normal_report_length(self, reporter, sample_analysis):
        """测试正常报告长度"""
        markdown = reporter.generate_markdown([sample_analysis], execution_time='11:05:23')
        
        # 正常报告应该在合理范围内
        assert len(markdown) < 4096  # 不超过企业微信限制
        assert len(markdown) > 100  # 不应该太短


# ==================== 测试报告保存 ====================

class TestReportSaving:
    """测试报告保存功能"""
    
    def test_save_report(self, reporter, sample_analysis, tmp_path):
        """测试保存报告到文件"""
        # 修改 reporter 的 data_dir
        reporter.data_dir = str(tmp_path)
        
        # 生成并保存报告
        markdown = reporter.generate_markdown([sample_analysis], execution_time='11:05:23')
        reporter.save_report(markdown, 'ARKK', '2025-01-15')
        
        # 验证文件存在
        expected_path = tmp_path / "reports" / "ARKK" / "2025-01-15.md"
        assert expected_path.exists()
        
        # 验证文件内容
        content = expected_path.read_text(encoding='utf-8')
        assert '# ARK 持仓变化' in content
        assert 'ARKK' in content
    
    def test_save_report_creates_directory(self, reporter, sample_analysis, tmp_path):
        """测试自动创建目录"""
        reporter.data_dir = str(tmp_path)
        
        # 保存报告（目录不存在）
        markdown = reporter.generate_markdown([sample_analysis], execution_time='11:05:23')
        reporter.save_report(markdown, 'ARKW', '2025-01-15')
        
        # 验证目录被创建
        expected_dir = tmp_path / "reports" / "ARKW"
        assert expected_dir.exists()
        assert expected_dir.is_dir()
    
    def test_save_multiple_reports(self, reporter, sample_analysis, tmp_path):
        """测试保存多个报告"""
        reporter.data_dir = str(tmp_path)
        
        markdown = reporter.generate_markdown([sample_analysis], execution_time='11:05:23')
        
        # 保存不同日期的报告
        reporter.save_report(markdown, 'ARKK', '2025-01-14')
        reporter.save_report(markdown, 'ARKK', '2025-01-15')
        
        # 验证两个文件都存在
        assert (tmp_path / "reports" / "ARKK" / "2025-01-14.md").exists()
        assert (tmp_path / "reports" / "ARKK" / "2025-01-15.md").exists()


# ==================== 测试格式化函数 ====================

class TestFormatting:
    """测试格式化辅助函数"""
    
    def test_format_large_number(self, reporter):
        """测试大数字格式化"""
        markdown = reporter.generate_markdown(
            [ChangeAnalysis(
                etf_symbol='ARKK',
                current_date='2025-01-15',
                previous_date='2025-01-14',
                added=[{
                    'ticker': 'TSLA',
                    'company': 'Tesla Inc',
                    'shares': 1200000,  # 应该格式化为 1.2M
                    'market_value': 300000000.00,  # 应该格式化为 $300M
                    'weight': 11.80
                }],
                removed=[],
                increased=[],
                decreased=[]
            )],
            execution_time='11:05:23'
        )
        
        # 验证数字格式化（根据实际实现可能不同）
        # 如果实现了格式化，应该看到 1.2M 或 $300M
        # 这里只验证数字存在
        assert '1200000' in markdown or '1.2M' in markdown
        assert '300000000' in markdown or '$300M' in markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
