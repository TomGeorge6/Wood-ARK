#!/bin/bash
# 设置 Launchd 定时任务脚本

set -e

echo "=========================================="
echo "Wood-ARK 自动化部署脚本"
echo "=========================================="
echo ""

# 获取当前脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "项目路径: $PROJECT_DIR"
echo ""

# 检查 Python 路径
PYTHON_PATH=$(which python3)
echo "Python 路径: $PYTHON_PATH"
echo ""

# 从 config.yaml 读取执行时间
CRON_TIME=$(grep "cron_time:" "$PROJECT_DIR/config.yaml" | awk '{print $2}' | tr -d '"')
HOUR=$(echo "$CRON_TIME" | cut -d':' -f1)
MINUTE=$(echo "$CRON_TIME" | cut -d':' -f2)

echo "从 config.yaml 读取执行时间: $CRON_TIME (Hour=$HOUR, Minute=$MINUTE)"
echo ""

# 创建 Launchd plist 文件
PLIST_FILE="$HOME/Library/LaunchAgents/com.lucian.wood-ark.plist"

echo "创建 Launchd 配置文件: $PLIST_FILE"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lucian.wood-ark</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$PROJECT_DIR/main.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>$HOUR</integer>
        <key>Minute</key>
        <integer>$MINUTE</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/launchd.log</string>
    
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/launchd_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ 配置文件已创建"
echo ""

# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

# 卸载旧任务（如果存在）
if launchctl list | grep -q "com.lucian.wood-ark"; then
    echo "卸载旧任务..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# 加载新任务
echo "加载定时任务..."
launchctl load "$PLIST_FILE"

echo ""
echo "=========================================="
echo "✅ 部署成功！"
echo "=========================================="
echo ""
echo "任务详情："
echo "  - 任务名称: com.lucian.wood-ark"
echo "  - 执行时间: 每天 $CRON_TIME"
echo "  - 工作日检测: 自动跳过周末"
echo "  - 日志文件: $PROJECT_DIR/logs/launchd.log"
echo ""
echo "常用命令："
echo "  - 查看任务状态: launchctl list | grep wood-ark"
echo "  - 手动执行: launchctl start com.lucian.wood-ark"
echo "  - 停止任务: launchctl stop com.lucian.wood-ark"
echo "  - 卸载任务: launchctl unload $PLIST_FILE"
echo "  - 查看日志: tail -f $PROJECT_DIR/logs/launchd.log"
echo ""
echo "现在执行测试运行..."
echo ""

# 测试运行
cd "$PROJECT_DIR"
python3 main.py --manual

echo ""
echo "✅ 测试完成！请检查企业微信是否收到推送。"
echo ""
