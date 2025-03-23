import requests
import logging
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DingTalkAPI:
    """钉钉API封装类"""
    
    def __init__(self, client_id: str, client_secret: str, app_id: str = None):
        """
        初始化钉钉API
        
        Args:
            client_id: 应用ID
            client_secret: 应用密钥
            app_id: 钉钉应用ID，选填
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.app_id = app_id
        self.access_token = None
        self.token_expire_time = 0
        
    def _get_access_token(self) -> Optional[str]:
        """
        获取访问令牌
        
        Returns:
            str: 访问令牌
        """
        # 如果令牌未过期，直接返回
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token
            
        url = "https://oapi.dingtalk.com/gettoken"
        params = {
            "appkey": self.client_id,
            "appsecret": self.client_secret
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            if result.get("errcode") == 0:
                self.access_token = result.get("access_token")
                # 设置过期时间，提前5分钟过期
                self.token_expire_time = time.time() + result.get("expires_in", 7200) - 300
                return self.access_token
            else:
                logger.error(f"获取钉钉访问令牌失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取钉钉访问令牌出错: {str(e)}")
            return None
    
    def get_signature(self, timestamp: str) -> str:
        """
        生成签名
        
        Args:
            timestamp: 时间戳
            
        Returns:
            str: 签名
        """
        string_to_sign = timestamp + "\n" + self.client_secret
        hmac_code = hmac.new(self.client_secret.encode(), string_to_sign.encode(), digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode()
        return urllib.parse.quote_plus(sign)
            
    def get_departments(self) -> List[Dict[str, Any]]:
        """
        获取部门列表
        
        Returns:
            List[Dict[str, Any]]: 部门列表
        """
        token = self._get_access_token()
        if not token:
            logger.error("未能获取有效的访问令牌")
            return []
            
        url = "https://oapi.dingtalk.com/topapi/v2/department/list"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "language": "zh_CN"
        }
        params = {
            "access_token": token
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, data=json.dumps(data))
            response.raise_for_status()
            
            result = response.json()
            if result.get("errcode") == 0:
                return result.get("result", [])
            else:
                logger.error(f"获取钉钉部门列表失败: {result}")
                return []
        except Exception as e:
            logger.error(f"获取钉钉部门列表出错: {str(e)}")
            return []
            
    def get_department_users(self, dept_id: int) -> List[Dict[str, Any]]:
        """
        获取部门用户
        
        Args:
            dept_id: 部门ID
            
        Returns:
            List[Dict[str, Any]]: 用户列表
        """
        token = self._get_access_token()
        if not token:
            logger.error("未能获取有效的访问令牌")
            return []
            
        url = "https://oapi.dingtalk.com/topapi/v2/user/list"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "dept_id": dept_id,
            "language": "zh_CN"
        }
        params = {
            "access_token": token
        }
        
        users = []
        
        try:
            # 分页获取所有用户
            cursor = 0
            has_more = True
            
            while has_more:
                data["cursor"] = cursor
                data["size"] = 100
                
                response = requests.post(url, headers=headers, params=params, data=json.dumps(data))
                response.raise_for_status()
                
                result = response.json()
                if result.get("errcode") == 0:
                    result_data = result.get("result", {})
                    items = result_data.get("list", [])
                    users.extend(items)
                    
                    # 检查是否有更多数据
                    has_more = result_data.get("has_more", False)
                    cursor = cursor + 100
                else:
                    logger.error(f"获取钉钉部门用户失败: {result}")
                    break
                    
            return users
        except Exception as e:
            logger.error(f"获取钉钉部门用户出错: {str(e)}")
            return []
            
    def get_users(self) -> List[Dict[str, Any]]:
        """
        获取所有用户
        
        Returns:
            List[Dict[str, Any]]: 用户列表
        """
        departments = self.get_departments()
        if not departments:
            return []
            
        all_users = []
        # 用户ID去重
        user_ids = set()
        
        for dept in departments:
            dept_id = dept.get("dept_id")
            users = self.get_department_users(dept_id)
            
            for user in users:
                user_id = user.get("userid")
                if user_id and user_id not in user_ids:
                    user_ids.add(user_id)
                    
                    # 处理用户数据
                    user_data = {
                        'userid': user.get('userid'),
                        'unionid': user.get('unionid'),
                        'name': user.get('name'),
                        'email': user.get('email'),
                        'mobile': user.get('mobile'),
                        'avatar': user.get('avatar'),
                        'title': user.get('title'),
                        'department': ','.join([str(d) for d in user.get('dept_id_list', [])]),
                        'job_number': user.get('job_number')
                    }
                    all_users.append(user_data)
        
        return all_users
    
    def get_user_detail(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户详情
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any] or None: 用户详情
        """
        token = self._get_access_token()
        if not token:
            logger.error("未能获取有效的访问令牌")
            return None
            
        url = "https://oapi.dingtalk.com/topapi/v2/user/get"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "userid": user_id,
            "language": "zh_CN"
        }
        params = {
            "access_token": token
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, data=json.dumps(data))
            response.raise_for_status()
            
            result = response.json()
            if result.get("errcode") == 0:
                return result.get("result", {})
            else:
                logger.error(f"获取钉钉用户详情失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取钉钉用户详情出错: {str(e)}")
            return None 