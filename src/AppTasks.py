# 参考 https://scriptcat.org/zh-CN/script-show-page/1703
import logging
import time
import json
import random
import requests
import re  # 添加正则表达式模块导入
from typing import Optional, Dict, Any

LOG_TAG = "[CMY][APP]"

class AppTasks:
    def __init__(self, browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils
        self.username = browser.username
        # API相关配置
        self.api_url = "https://prod.rewardsplatform.microsoft.com/dapi/me/activities"
        self.read_progress_url = "https://prod.rewardsplatform.microsoft.com/dapi/me?channel=SAAndroid&options=613"
        self.oauth_code_url = "https://login.live.com/oauth20_authorize.srf"
        self.oauth_token_url = "https://login.live.com/oauth20_token.srf"
        self.client_id = "0000000040170455"
        self.scope = "service::prod.rewardsplatform.microsoft.com::MBI_SSL"
        self.redirect_uri = "https://login.live.com/oauth20_desktop.srf"
        self.access_token = None
        
    def get_cookies(self) -> Dict[str, str]:
        """
        从浏览器中获取Cookie，用于API请求
        """
        cookie_jar = self.webdriver.get_cookies()
        return {cookie["name"]: cookie["value"] for cookie in cookie_jar}
    
    def get_access_token(self) -> bool:
        """
        获取App端API访问所需的OAuth token
        基于temp.js中的认证流程实现
        """
        try:
            # 第一步：获取授权码
            auth_code_url = f"{self.oauth_code_url}?client_id={self.client_id}&scope={self.scope}&response_type=code&redirect_uri={self.redirect_uri}"
            
            # 使用浏览器会话发起请求获取授权码
            self.webdriver.get(auth_code_url)
            time.sleep(2)  # 等待页面加载
            
            # 获取最终URL来提取授权码
            final_url = self.webdriver.current_url
            # 使用re.search来提取授权码
            code_match = re.search(r"code=([^&]+)", final_url)
            
            if not code_match:
                logging.error(f"{LOG_TAG} {self.username} 无法获取授权码")
                return False
            
            auth_code = code_match.group(1)
            
            # 第二步：使用授权码获取access token
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "okhttp/4.9.1"
            }
            
            # 使用表单数据而不是URL参数
            data = {
                "client_id": self.client_id,
                "code": auth_code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code"
            }
            
            response = requests.post(self.oauth_token_url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                
                if self.access_token:
                    logging.info(f"{LOG_TAG} {self.username} 成功获取access token")
                    return True
                else:
                    logging.error(f"{LOG_TAG} {self.username} 未能从响应中提取access token")
            else:
                logging.error(f"{LOG_TAG} {self.username} 获取token失败: {response.status_code}")
                logging.error(f"{LOG_TAG} {self.username} 响应内容: {response.text}")
        except Exception as e:
            logging.error(f"{LOG_TAG} {self.username} 获取access token异常: {str(e)}")
        
        return False
    
    def app_sign_in(self, startingPoints: int) -> int:
        """
        执行App端每日签到任务
        """
        logging.info(f"{LOG_TAG} {self.username} 开始执行App端签到任务")
        
        try:
            # 添加随机延时，模拟人类操作
            time.sleep(random.uniform(10, 15))
            
            # 获取access token
            if not self.access_token and not self.get_access_token():
                logging.error(f"{LOG_TAG} {self.username} 获取认证失败，无法执行签到")
                return False
            
            # 构造请求头，使用Bearer token认证
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "channel": "SAAndroid",
                "User-Agent": "okhttp/4.9.1",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # 获取当前日期，格式化为所需格式
            current_date = time.localtime()
            date_str = f"{current_date.tm_mon:02d}/{current_date.tm_mday:02d}/{current_date.tm_year}"
            date_num = int(f"{current_date.tm_year}{current_date.tm_mon:02d}{current_date.tm_mday:02d}")
            
            # 构造符合temp.js格式的请求数据
            payload = {
                "amount": 1,
                "attributes": {
                    "offerid": "Gamification_Sapphire_DailyCheckIn",
                    "date": date_num,
                    "signIn": False,
                    "timezoneOffset": "08:00:00"
                },
                "id": "",
                "type": 101,
                "country": "cn",
                "risk_context": {},
                "channel": "SAAndroid"
            }
            
            # 添加随机延时
            time.sleep(random.uniform(10, 15))
            
            # 发送签到请求
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"{LOG_TAG} {self.username} App端签到结果: {result}")
                # result格式为{'response': {'balance': 16622, 'activity': {'id': '5d8c1360-6146-4865-9a14-152e1a8ce18e', 'id_old': None, 'm': 'cn', 't': '2025-10-22T01:32:31.3040489+00:00', 'type': 101, 'p': 0, 'q': 1, 'a': {'offerid': 'Gamification_Sapphire_DailyCheckIn', 'date': '20251022', 'signIn': 'false', 'timezoneOffset': '08:00:00', 'ModifiedDateTimeStamp': '2025-10-22T01:32:31.3670735+00:00'}, 'rbTxEntry': None}, 'info': None, 'isDuplicate': False, 'notifications': None, 'isExpiredTrialUser': False}, 'correlationId': '7c49563a759040408230445e90ea08fd', 'code': 0}
                # 提取新的积分值
                new_points = result["response"]["balance"]
                
                # 检查是否成功签到
                if new_points > startingPoints:
                    logging.info(f"{LOG_TAG} {self.username} App端签到成功，获得 {new_points - startingPoints} 积分")
                else:
                    logging.warning(f"{LOG_TAG} {self.username} App端签到可能已完成或失败")
                
                # 增加延时让积分有时间更新
                time.sleep(random.uniform(5, 10))
                return new_points - startingPoints
            else:
                logging.error(f"{LOG_TAG} {self.username} App端签到HTTP请求失败: {response.status_code}")
                logging.error(f"{LOG_TAG} {self.username} 响应内容: {response.text}")
        except Exception as e:
            logging.error(f"{LOG_TAG} {self.username} App端签到执行异常: {str(e)}")
        
        return -1
    
    def get_read_progress(self) -> Optional[Dict[str, Any]]:
        """
        获取阅读任务进度
        """
        try:
            # 确保有access token
            if not self.access_token and not self.get_access_token():
                return None
            
            headers = {
                "Accept": "application/json",
                "channel": "SAAndroid",
                "User-Agent": "okhttp/4.9.1",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # 添加随机延时
            time.sleep(random.uniform(2, 4))
            
            response = requests.get(
                self.read_progress_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"{LOG_TAG} {self.username} 获取阅读进度失败: {response.status_code}")
                logging.error(f"{LOG_TAG} {self.username} 响应内容: {response.text}")
        except Exception as e:
            logging.error(f"{LOG_TAG} {self.username} 获取阅读进度异常: {str(e)}")
        
        return None
    
    def app_read_articles(self) -> int:
        """
        执行App端阅读文章任务
        """
        logging.info(f"{LOG_TAG} {self.username} 开始执行App端阅读任务")
        
        try:
            # 添加随机延时
            time.sleep(random.uniform(3, 7))
            
            # 确保有access token
            if not self.access_token and not self.get_access_token():
                logging.error(f"{LOG_TAG} {self.username} 获取认证失败，无法执行阅读任务")
                return False
            
            # 构造请求头
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "channel": "SAAndroid",
                "User-Agent": "okhttp/4.9.1",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # 先获取阅读进度
            progress_data = self.get_read_progress()
            if not progress_data:
                logging.warning(f"{LOG_TAG} {self.username} 无法获取阅读进度，跳过阅读任务")
                return False
            
            # 查找阅读任务
            read_progress = {"max": 1, "progress": 0}
            promotions = progress_data.get("response", {}).get("promotions", [])
            
            for promo in promotions:
                if promo.get("attributes", {}).get("offerid") == "ENUS_readarticle3_30points":
                    read_progress = {
                        "max": int(promo.get("attributes", {}).get("max", 1)),
                        "progress": int(promo.get("attributes", {}).get("progress", 0))
                    }
                    break
            
            if read_progress["progress"] >= read_progress["max"]:
                logging.info(f"{LOG_TAG} {self.username} 阅读任务已完成")
                return True
            
            # 执行阅读任务
            total_points = 0
            
            # 修复：将阅读次数从3次修改为10次
            articles_to_read = min(10, read_progress["max"] - read_progress["progress"])
            logging.info(f"{LOG_TAG} {self.username} 需要阅读 {articles_to_read} 篇文章")
            
            for i in range(articles_to_read):
                # 添加较长的随机延时，模拟真实阅读时间
                time.sleep(random.uniform(8, 15))
                
                # 构造符合temp.js格式的请求数据
                payload = {
                    "amount": 1,
                    "country": "cn",
                    "id": "",
                    "type": 101,
                    "attributes": {
                        "offerid": "ENUS_readarticle3_30points"
                    }
                }
                
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # 更准确地提取积分信息
                    points = result.get("response", {}).get("activity", {}).get("p", 0)
                    total_points += points
                    logging.info(f"{LOG_TAG} {self.username} 第{i+1}篇文章阅读完成，获得 {points} 积分")
                else:
                    logging.error(f"{LOG_TAG} {self.username} 第{i+1}篇文章阅读失败: {response.status_code}")
                    logging.error(f"{LOG_TAG} {self.username} 响应内容: {response.text}")
                    
                # 文章间隔，使用更长的随机延时
                time.sleep(random.uniform(5, 10))
            
            # 增加较长延时让积分有时间更新
            time.sleep(random.uniform(10, 15))
            
            # 重新获取阅读进度，确认积分更新
            updated_progress = self.get_read_progress()
            if updated_progress:
                logging.info(f"{LOG_TAG} {self.username} 任务完成后更新的进度数据: {json.dumps(updated_progress.get('response', {}).get('promotions', [])[:2], ensure_ascii=False)}")
            
            logging.info(f"{LOG_TAG} {self.username} App端阅读任务完成，共获得 {total_points} 积分")
            return total_points
            
        except Exception as e:
            logging.error(f"{LOG_TAG} {self.username} App端阅读任务执行异常: {str(e)}")
        
        return -1
    
    def run_all_tasks(self, startingPoints: int) -> Dict[str, int]:
        """
        运行所有App端任务
        """
        results = {
            "app_sign_in": self.app_sign_in(startingPoints),
            "app_read_articles": self.app_read_articles()
        }
        return results