#!/bin/bash
# 下载最近30天的持仓数据

echo "下载最近30天的ARK ETF持仓数据..."

cd /Users/lucian/Documents/个人/Investment/Tools/Wood-ARK

# 生成最近30天的日期列表（美国东部时间）
python3 > /tmp/dates.txt << 'EOF'
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

et_tz = ZoneInfo("America/New_York")

# 获取最近30天的工作日
dates = []
current = datetime.now(et_tz)

for i in range(40):  # 往前推40天，确保有30个工作日
    check_date = current - timedelta(days=i)
    # 只保留工作日（周一到周五）
    if check_date.weekday() < 5:
        dates.append(check_date.strftime('%Y-%m-%d'))
        if len(dates) >= 30:
            break

# 反转列表（从早到晚）
dates.reverse()

# 输出日期列表
for date in dates:
    print(date)
EOF

# 读取日期列表并下载数据
while IFS= read -r date; do
    echo "下载 $date 的数据..."
    python3 main.py --date "$date" --manual 2>&1 | grep -E "(成功|失败)" || true
done < /tmp/dates.txt

echo "✅ 数据下载完成！"
