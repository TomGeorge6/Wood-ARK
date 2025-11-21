#!/bin/bash
#
# 卸载 Wood-ARK cron 定时任务
#
# 功能:
# - 从 crontab 中删除 Wood-ARK 相关任务
#
# 使用方法:
#   chmod +x scripts/uninstall_cron.sh
#   ./scripts/uninstall_cron.sh
#

set -e

# 获取项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=================================================="
echo "Wood-ARK Cron 任务卸载"
echo "=================================================="
echo "项目目录: $PROJECT_DIR"
echo ""

# 检查是否存在 cron 任务
if ! crontab -l 2>/dev/null | grep -q "$PROJECT_DIR/main.py"; then
    echo "⚠️  未找到 Wood-ARK cron 任务"
    echo ""
    echo "当前 crontab 配置:"
    crontab -l 2>/dev/null || echo "  (无)"
    exit 0
fi

# 显示将被删除的任务
echo "将删除以下 cron 任务:"
crontab -l 2>/dev/null | grep "$PROJECT_DIR/main.py"
echo ""

read -p "确认删除? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消卸载"
    exit 0
fi

# 删除任务
crontab -l 2>/dev/null | grep -v "$PROJECT_DIR/main.py" | crontab -

echo ""
echo "=================================================="
echo "✅ Cron 任务卸载成功!"
echo "=================================================="
echo ""
echo "验证卸载:"
echo "  crontab -l"
echo ""
