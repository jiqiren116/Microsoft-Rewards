![Made with Python](https://forthebadge.com/images/badges/made-with-python.svg)
![Built by Developers](http://ForTheBadge.com/images/badges/built-by-developers.svg)
![Uses Git](http://ForTheBadge.com/images/badges/uses-git.svg)
![Build with Love](http://ForTheBadge.com/images/badges/built-with-love.svg)

```ascii
███╗   ███╗███████╗    ███████╗ █████╗ ██████╗ ███╗   ███╗███████╗██████╗
████╗ ████║██╔════╝    ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝██╔══██╗
██╔████╔██║███████╗    █████╗  ███████║██████╔╝██╔████╔██║█████╗  ██████╔╝
██║╚██╔╝██║╚════██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║███████║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██║  ██║
╚═╝     ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝
       by Charles Bel (@charlesbel)          version 3.0
```

![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge)
![MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)

## :wave: Welcome to the future of automation

### A simple bot that uses selenium to farm Microsoft Rewards written in Python

```diff
- Use it at your own risk, Microsoft may ban your account (and I would not be responsible for it)
```

## Installation

1. Install requirements with the following command :

   `pip install -r requirements.txt`

2. Make sure you have Chrome installed

3. ~~Install ChromeDriver:~~

   You no longer need to do this step since selenium >=4.10.0 include a webdriver manager

   To update your selenium version, run this command : `pip install selenium --upgrade`

4. (Windows Only) Make sure Visual C++ redistributable DLLs are installed

   If they're not, install the current "vc_redist.exe" from this link and reboot your computer : https://learn.microsoft.com/en-GB/cpp/windows/latest-supported-vc-redist?view=msvc-170

5. Edit the `accounts.json.sample` with your accounts credentials and rename it by removing `.sample` at the end. The "proxy" field is not mandatory, you can ommit it if you don't want to use proxy (don't keep it as an empty string, remove it completely).

   - If you want to add more than one account, the syntax is the following:

   ```json
   [
     {
       "username": "Your Email 1",
       "password": "Your Password 1",
       "proxy": "http://user:pass@host1:port"
     },
     {
       "username": "Your Email 2",
       "password": "Your Password 2",
       "proxy": "http://user:pass@host2:port"
     }
   ]
   ```

6. Run the script:

   `python main.py`

   Or if you want to keep it updated (it will check on each run if a new version is available, if so, will download and run it), use :

   `python autoupdate_main.py`

## Launch arguments

- -v/--visible to disable headless
- -l/--lang to force a language (ex: en)
- -g/--geo to force a geolocation (ex: US)
- -p/--proxy to add a proxy to the whole program, supports http/https/socks4/socks5 (overrides per-account proxy in accounts.json) (ex: http://user:pass@host:port)
- -t/--telegram to add a telegram notification, requires Telegram Bot Token and Chat ID (ex: 123456789:ABCdefGhIjKlmNoPQRsTUVwxyZ 123456789)
- -d/--discord to add a discord notification, requires Discord Webhook URL (ex: https://discord.com/api/webhooks/123456789/ABCdefGhIjKlmNoPQRsTUVwxyZ)

## Features

- Bing searches (Desktop, Mobile and Edge) with User-Agents
- Complete automatically the daily set
- Complete automatically punch cards
- Complete automatically the others promotions
- Headless Mode
- Multi-Account Management
- Session storing (3.0)
- 2FA Support (3.0)
- Notifications (discord, telegram) (3.0)
- Proxy Support (3.0)

## Future Features

- GUI
## python创建虚拟环境
`python -m venv .venv`

## 根据requirements.txt安装依赖
pip install -r requirements.txt  --index-url https://pypi.tuna.tsinghua.edu.cn/simple

## windows如何进入python的venv环境

在 Windows 系统中，若要进入 Python 的虚拟环境（venv），可按以下步骤操作：

### 1. 开启命令提示符或 PowerShell

你可以按下 Win+R 组合键，输入`cmd`或者`powershell`，随后按下回车键来打开命令行工具。

### 2. 定位到虚拟环境所在目录

借助`cd`命令，进入你创建虚拟环境的那个目录。

```bash
cd path\to\your\project  # 请替换成实际的项目路径
```

### 3. 激活虚拟环境

#### 3.1 命令提示符（CMD）

```bash
your_venv\Scripts\activate.bat  # your_venv为虚拟环境的名称
```

#### 3.2 PowerShell

```bash
your_venv\Scripts\Activate.ps1  # your_venv为虚拟环境的名称
```

### 验证虚拟环境是否激活

当虚拟环境成功激活后，命令行提示符最前方会显示虚拟环境的名称，类似下面这样：

```bash
(your_venv) C:\path\to\your\project>
```

### 退出虚拟环境

若要退出当前的虚拟环境，在命令行中输入`deactivate`即可。

```bash
deactivate
```

### 补充说明

- 要创建虚拟环境，可使用命令`python -m venv your_venv`。
- 激活虚拟环境之后，安装的所有 Python 包都会被存放在该虚拟环境目录里，不会对系统全局的 Python 环境产生影响。

## 关于搜索的一些问题
1、 看贴吧说，大概10分钟可以搜索12分。
2、 看贴吧说，一个ip最多可以搞6个账户，我目前是同ip下4个账户。

## 配置tash scheduler时无命令行运行
用task scheduler运行的脚本是run_script_venv.bat
https://blog.csdn.net/qq_39188306/article/details/88689224

## 注意，要先下载谷歌浏览器和对应的chromedriver驱动，并把路径配置到config.json文件中
例如像下面这样配置
```config.json
{
    "driver_executable_path": "D:\\App\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe",
    "browser_executable_path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "add_visible_flag": true,
    "pushplus_token": "your pushplus_token",
    "target_point": 17925
}
```

## 随后将邮箱和密码配置到accounts.json文件中