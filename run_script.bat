REM 在Windows中使用task scheduler创建定时任务
REM 定时任务的执行脚本，用于运行 Python 脚本
@echo off

REM 获取当前脚本所在目录
set SCRIPT_DIR=%~dp0

REM 替换为你的 Python 解释器路径
set PYTHON_PATH=D:\Python\Python313\python.exe
REM 替换为你的 Python 脚本相对于当前脚本目录的相对路径
set SCRIPT_PATH=%SCRIPT_DIR%main.py
REM 执行 Python 脚本
%PYTHON_PATH% %SCRIPT_PATH%
pause
