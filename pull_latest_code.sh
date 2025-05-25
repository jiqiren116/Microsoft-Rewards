#!/bin/bash
# 进入项目目录
PROJECT_DIR="/root/workspace/Microsoft-Rewards"
cd $PROJECT_DIR

# 拉取最新代码
git pull origin master

# 输出日志
echo "$(date '+%Y-%m-%d %H:%M:%S'): 成功拉取最新代码" >> $PROJECT_DIR/git_pull.log