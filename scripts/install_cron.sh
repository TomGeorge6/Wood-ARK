#!/bin/bash
#
# 安装 Wood-ARK cron 定时任务
#
# 功能:
# - 自动检测项目路径和 Python 解释器
# - 添加 cron 任务到 crontab
# - 默认每天上午 11:00 执行（周一到周五）
#
# 使用方法:
#   chmod +x scripts/install_cron.sh
#   ./scripts/install_cron.sh
#

set -e  # 遇到错误立即退出

# ==================== 配置 ====================

# 获取项目根目录（脚本所在目录的上一级）
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 检测 Python 解释器
if command -v python3 &>/dev/null; then
    PYTHON_BIN="$(which python3)"
elif command -v python &>/dev/null; then
    PYTHON_BIN="$(which python)"
else
    echo "❌ 错误: 未找到 Python 解释器"
    echo "请先安装 Python 3.9+"
    exit 1
fi

# 从 config.yaml 读取执行时间（如果文件存在）
CONFIG_FILE="$PROJECT_DIR/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    # 提取 cron_time 配置（使用 grep + awk）
    CRON_TIME=$(grep -E '^\s*cron_time:' "$CONFIG_FILE" | awk -F'"' '{print $2}')
    
    if [ -z "$CRON_TIME" ]; then
        CRON_TIME="11:00"  # 默认值
    fi
else
    CRON_TIME="11:00"
fi

# 将时间转换为 cron 格式 (HH:MM → M H)
HOUR=$(echo "$CRON_TIME" | cut -d':' -f1)
MINUTE=$(echo "$CRON_TIME" | cut -d':' -f2)

# Cron 表达式: "分 时 日 月 周"
# 周一到周五: 1-5
CRON_SCHEDULE="$MINUTE $HOUR * * 1-5"

# Cron 命令: cd 到项目目录并执行 main.py
CRON_COMMAND="cd $PROJECT_DIR && $PYTHON_BIN main.py"

# ==================== 安装 ====================

echo "=================================================="
echo "Wood-ARK Cron 任务安装"
echo "=================================================="
echo "项目目录: $PROJECT_DIR"
echo "Python: $PYTHON_BIN"
echo "执行时间: $CRON_TIME (周一至周五)"
echo "Cron 表达式: $CRON_SCHEDULE"
echo ""

# 检查是否已存在相同任务
if crontab -l 2>/dev/null | grep -q "$PROJECT_DIR/main.py"; then
    echo "⚠️  检测到已存在的 cron 任务"
    echo "当前 cron 配置:"
    crontab -l 2>/dev/null | grep "$PROJECT_DIR/main.py"
    echo ""
    read -p "是否替换为新配置? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消安装"
        exit 0
    fi
    
    # 删除旧任务
    crontab -l 2>/dev/null | grep -v "$PROJECT_DIR/main.py" | crontab -
    echo "✅ 已删除旧任务"
fi

# 添加新任务
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_COMMAND") | crontab -

echo ""
echo "=================================================="
echo "✅ Cron 任务安装成功!"
echo "=================================================="
echo ""
echo "验证安装:"
echo "  crontab -l | grep 'main.py'"
echo ""
echo "查看日志:"
echo "  tail -f $PROJECT_DIR/logs/\$(date +%Y-%m-%d).log"
echo ""
echo "手动测试:"
echo "  cd $PROJECT_DIR && $PYTHON_BIN main.py --manual"
echo ""
echo "卸载任务:"
echo "  ./scripts/uninstall_cron.sh"
echo ""

# 显示当前 crontab 配置
echo "当前 crontab 配置:"
crontab -l | grep "$PROJECT_DIR" || echo "  (无)"
echo ""
