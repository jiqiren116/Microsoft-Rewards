REM 在Windows中使用task scheduler创建定时任务
REM 定时任务的执行脚本，用于运行使用venv虚拟环境的Python脚本
@echo off

REM 获取当前脚本所在目录
set SCRIPT_DIR=%~dp0

REM 虚拟环境激活脚本的相对路径，假设虚拟环境在当前目录下的 .venv 文件夹
set VENV_ACTIVATE_PATH=%SCRIPT_DIR%.venv\Scripts\activate.bat

REM Python 脚本的相对路径，假设 Python 脚本在当前目录下
set SCRIPT_PATH=%SCRIPT_DIR%main.py

REM 激活虚拟环境
call %VENV_ACTIVATE_PATH%

REM 执行git pull，不管是否成功都继续执行
cd %SCRIPT_DIR%
git pull || echo "Git pull failed, continuing anyway"

REM 等待5秒
timeout /t 5 /nobreak >nul

REM 执行 Python 脚本
python %SCRIPT_PATH%

REM 停用虚拟环境
call deactivate

REM task scheduler配置无命令行窗口黑框执行程序链接 https://blog.csdn.net/qq_39188306/article/details/88689224