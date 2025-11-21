"""
任务调度和状态管理模块

负责判断是否执行任务、管理推送状态、检测缺失日期等。
"""

import logging
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from src.utils import (
    get_current_date,
    get_previous_date,
    get_recent_dates,
    is_weekday,
    ensure_dir
)

logger = logging.getLogger(__name__)


class PushStatus:
    """推送状态记录"""
    
    def __init__(self, etf_symbol: str, date: str, status: str, timestamp: str):
        self.etf_symbol = etf_symbol
        self.date = date
        self.status = status  # 'success', 'failed', 'skipped'
        self.timestamp = timestamp
    
    def to_dict(self) -> dict:
        return {
            'etf_symbol': self.etf_symbol,
            'date': self.date,
            'status': self.status,
            'timestamp': self.timestamp
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'PushStatus':
        return PushStatus(
            etf_symbol=data['etf_symbol'],
            date=data['date'],
            status=data['status'],
            timestamp=data['timestamp']
        )


class Scheduler:
    """任务调度器"""
    
    def __init__(
        self,
        data_dir: str = "./data",
        enable_schedule: bool = True
    ):
        """
        初始化调度器
        
        Args:
            data_dir: 数据存储根目录
            enable_schedule: 是否启用工作日检查（False 则总是执行）
        """
        self.data_dir = Path(data_dir)
        self.cache_dir = self.data_dir / "cache"
        ensure_dir(str(self.cache_dir))
        
        self.status_file = self.cache_dir / "push_status.json"
        self.enable_schedule = enable_schedule
        
        logger.info(f"初始化 Scheduler，状态文件: {self.status_file}")
    
    def should_run_today(self, force: bool = False) -> bool:
        """
        判断今天是否应该运行任务
        
        Args:
            force: 是否强制执行（忽略工作日检查和重复检查）
        
        Returns:
            是否应该运行
        """
        if force:
            logger.info("强制执行模式，跳过检查")
            return True
        
        # 检查是否启用调度
        if not self.enable_schedule:
            logger.info("调度已禁用，直接执行")
            return True
        
        # 检查是否为工作日
        if not is_weekday():
            logger.info("今天是周末，跳过执行")
            return False
        
        # 检查今天是否已经执行过
        today = get_current_date()
        if self.is_pushed(today):
            logger.info(f"今天 ({today}) 已执行过，跳过重复执行")
            return False
        
        logger.info(f"今天 ({today}) 是工作日且未执行过，允许执行")
        return True
    
    def get_target_date(self, manual_date: Optional[str] = None) -> str:
        """
        获取目标日期
        
        Args:
            manual_date: 手动指定的日期（YYYY-MM-DD），优先级最高
        
        Returns:
            目标日期
        """
        if manual_date:
            logger.info(f"使用手动指定日期: {manual_date}")
            return manual_date
        
        # 默认使用当前日期
        today = get_current_date()
        logger.info(f"使用当前日期: {today}")
        return today
    
    def get_comparison_date(self, target_date: str) -> str:
        """
        获取对比日期（目标日期的前一个交易日）
        
        Args:
            target_date: 目标日期
        
        Returns:
            对比日期
        """
        # 简单实现：前一天
        # TODO: 考虑美国市场休市日历
        prev_date = get_previous_date(target_date)
        logger.info(f"对比日期: {prev_date}")
        return prev_date
    
    def mark_pushed(
        self,
        etf_symbol: str,
        date: str,
        success: bool = True
    ) -> None:
        """
        标记推送状态
        
        Args:
            etf_symbol: ETF 代码
            date: 日期
            success: 是否成功
        """
        status = 'success' if success else 'failed'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        push_status = PushStatus(
            etf_symbol=etf_symbol,
            date=date,
            status=status,
            timestamp=timestamp
        )
        
        # 加载现有状态
        all_status = self._load_status()
        
        # 添加新状态
        key = f"{etf_symbol}_{date}"
        all_status[key] = push_status.to_dict()
        
        # 保存
        self._save_status(all_status)
        
        logger.info(f"标记推送状态: {etf_symbol} - {date} - {status}")
    
    def is_pushed(self, date: str, etf_symbol: Optional[str] = None) -> bool:
        """
        检查指定日期是否已推送
        
        Args:
            date: 日期
            etf_symbol: ETF 代码（可选，不指定则检查是否有任何 ETF 推送成功）
        
        Returns:
            是否已推送
        """
        all_status = self._load_status()
        
        if etf_symbol:
            key = f"{etf_symbol}_{date}"
            return key in all_status and all_status[key]['status'] == 'success'
        else:
            # 检查是否有任何 ETF 在该日期推送成功
            for key, status in all_status.items():
                if status['date'] == date and status['status'] == 'success':
                    return True
            return False
    
    def check_missed_dates(
        self,
        etf_symbols: List[str],
        days: int = 7
    ) -> Dict[str, List[str]]:
        """
        检查最近缺失的日期
        
        Args:
            etf_symbols: ETF 代码列表
            days: 检查最近多少天
        
        Returns:
            字典，key 为 ETF 代码，value 为缺失日期列表
        """
        logger.info(f"检查最近 {days} 天的缺失日期")
        
        recent_dates = get_recent_dates(days)
        all_status = self._load_status()
        
        missed = {}
        
        for etf in etf_symbols:
            missed_dates = []
            
            for date in recent_dates:
                # 只检查工作日
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                if date_obj.weekday() >= 5:  # 周末
                    continue
                
                key = f"{etf}_{date}"
                if key not in all_status or all_status[key]['status'] != 'success':
                    missed_dates.append(date)
            
            if missed_dates:
                missed[etf] = missed_dates
        
        if missed:
            logger.warning(f"发现缺失日期: {missed}")
        else:
            logger.info("未发现缺失日期")
        
        return missed
    
    def _load_status(self) -> dict:
        """加载推送状态"""
        if not self.status_file.exists():
            return {}
        
        try:
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载状态文件失败: {e}")
            return {}
    
    def _save_status(self, status_dict: dict) -> None:
        """保存推送状态"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def cleanup_old_status(self, keep_days: int = 90) -> None:
        """
        清理旧的状态记录
        
        Args:
            keep_days: 保留最近多少天的记录
        """
        logger.info(f"清理 {keep_days} 天前的状态记录")
        
        all_status = self._load_status()
        cutoff_date = (datetime.now() - timedelta(days=keep_days)).strftime('%Y-%m-%d')
        
        cleaned_status = {
            key: value
            for key, value in all_status.items()
            if value['date'] >= cutoff_date
        }
        
        removed_count = len(all_status) - len(cleaned_status)
        
        if removed_count > 0:
            self._save_status(cleaned_status)
            logger.info(f"已清理 {removed_count} 条旧记录")
        else:
            logger.info("无需清理")
