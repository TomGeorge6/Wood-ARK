#!/bin/bash
#
# 手动清理过期日志文件
#
# 功能:
# - 删除超过 N 天的日志文件（默认 30 天）
# - 保留最近的日志
#
# 使用方法:
#   chmod +x scripts/cleanup_logs.sh
#   ./scripts/cleanup_logs.sh [天数]
#
# 示例:
#   ./scripts/cleanup_logs.sh      # 清理 30 天前的日志
#   ./scripts/cleanup_logs.sh 7    # 清理 7 天前的日志
#

set -e

# 获取项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"

# 默认保留天数
RETENTION_DAYS=${1:-30}

echo "=================================================="
echo "Wood-ARK 日志清理"
echo "=================================================="
echo "日志目录: $LOG_DIR"
echo "保留天数: $RETENTION_DAYS 天"
echo ""

# 检查日志目录是否存在
if [ ! -d "$LOG_DIR" ]; then
    echo "⚠️  日志目录不存在: $LOG_DIR"
    exit 0
fi

# 查找过期日志
OLD_LOGS=$(find "$LOG_DIR" -name "*.log" -type f -mtime +$RETENTION_DAYS 2>/dev/null || true)

if [ -z "$OLD_LOGS" ]; then
    echo "✅ 未找到过期日志文件"
    exit 0
fi

# 显示将被删除的日志
echo "将删除以下日志文件:"
echo "$OLD_LOGS"
echo ""

LOG_COUNT=$(echo "$OLD_LOGS" | wc -l | tr -d ' ')
echo "共 $LOG_COUNT 个文件"
echo ""

read -p "确认删除? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消清理"
    exit 0
fi

# 删除过期日志
find "$LOG_DIR" -name "*.log" -type f -mtime +$RETENTION_DAYS -delete

echo ""
echo "=================================================="
echo "✅ 日志清理完成!"
echo "=================================================="
echo ""
echo "当前日志文件:"
ls -lh "$LOG_DIR"/*.log 2>/dev/null | tail -5 || echo "  (无)"
echo ""
