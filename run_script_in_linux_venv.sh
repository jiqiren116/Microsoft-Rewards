#!/bin/bash
# 在 Linux 中使用 cron 创建定时任务
# 定时任务的执行脚本，用于运行使用 venv 虚拟环境的 Python 脚本

# 创建 logs 文件夹（如果不存在）
LOG_DIR="$(dirname "$(realpath "$0")")/logs"
mkdir -p "$LOG_DIR"

# 生成日志文件名，包含日期和时间
LOG_FILE="$LOG_DIR/$(date +'%Y%m%d_%H%M%S').log"

# 获取当前脚本所在目录
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# 虚拟环境激活脚本的相对路径，假设虚拟环境在当前目录下的 .venv 文件夹
VENV_ACTIVATE_PATH="$SCRIPT_DIR/.venv/bin/activate"

# Python 脚本的相对路径，假设 Python 脚本在当前目录下
SCRIPT_PATH="$SCRIPT_DIR/main.py"

{
    echo "Script started at $(date)"

    # 激活虚拟环境
    source "$VENV_ACTIVATE_PATH"
    echo "Virtual environment activated"

    # 执行 Python 脚本
    python3 "$SCRIPT_PATH"

    # 停用虚拟环境
    deactivate
    echo "Virtual environment deactivated"

    echo "Script finished at $(date)"
} >> "$LOG_FILE" 2>&1
