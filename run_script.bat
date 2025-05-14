REM 在Windows中使用task scheduler创建定时任务
REM 定时任务的执行脚本，用于运行 Python 脚本
@echo off
REM 替换为你的 Python 解释器路径
set PYTHON_PATH=D:\Python\Python313\python.exe
REM 替换为你的 Python 脚本路径
set SCRIPT_PATH=d:\MyProject\Microsoft-Rewards\main.py
REM 执行 Python 脚本
%PYTHON_PATH% %SCRIPT_PATH%
pause
