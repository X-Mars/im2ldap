import requests
import logging
import json
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FeiShuAPI:
    """飞书API封装类"""
    
    def __init__(self, app_id: str, app_secret: str):
        """
        初始化飞书API
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
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
            
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                # 设置过期时间，提前5分钟过期
                self.token_expire_time = time.time() + result.get("expire", 7200) - 300
                return self.access_token
            else:
                logger.error(f"获取飞书访问令牌失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取飞书访问令牌出错: {str(e)}")
            return None
            
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
            
        url = "https://open.feishu.cn/open-apis/contact/v3/departments/children"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "department_id": "0",  # 根部门
            "fetch_child": True
        }
        
        departments = []
        page_token = None
        
        try:
            # 分页获取所有部门
            while True:
                if page_token:
                    params["page_token"] = page_token
                    
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                result = response.json()
                if result.get("code") == 0:
                    items = result.get("data", {}).get("items", [])
                    departments.extend(items)
                    
                    # 检查是否有下一页
                    page_token = result.get("data", {}).get("page_token")
                    if not page_token:
                        break
                else:
                    logger.error(f"获取飞书部门列表失败: {result}")
                    break
                    
            return departments
        except Exception as e:
            logger.error(f"获取飞书部门列表出错: {str(e)}")
            return []
            
    def get_department_users(self, department_id: str) -> List[Dict[str, Any]]:
        """
        获取部门成员
        
        Args:
            department_id: 部门ID
            
        Returns:
            List[Dict[str, Any]]: 用户列表
        """
        token = self._get_access_token()
        if not token:
            logger.error("未能获取有效的访问令牌")
            return []
            
        url = "https://open.feishu.cn/open-apis/contact/v3/users"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "department_id": department_id
        }
        
        users = []
        page_token = None
        
        try:
            # 分页获取所有用户
            while True:
                if page_token:
                    params["page_token"] = page_token
                    
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                result = response.json()
                if result.get("code") == 0:
                    items = result.get("data", {}).get("items", [])
                    users.extend(items)
                    
                    # 检查是否有下一页
                    page_token = result.get("data", {}).get("page_token")
                    if not page_token:
                        break
                else:
                    logger.error(f"获取飞书部门成员失败: {result}")
                    break
                    
            return users
        except Exception as e:
            logger.error(f"获取飞书部门成员出错: {str(e)}")
            return []
            
    def get_users(self) -> List[Dict[str, Any]]:
        """
        获取所有用户
        
        Returns:
            List[Dict[str, Any]]: 用户列表
        """
        token = self._get_access_token()
        if not token:
            logger.error("未能获取有效的访问令牌")
            return []
            
        url = "https://open.feishu.cn/open-apis/contact/v3/users"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        users = []
        page_token = None
        
        try:
            # 分页获取所有用户
            while True:
                params = {}
                if page_token:
                    params["page_token"] = page_token
                    
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                result = response.json()
                if result.get("code") == 0:
                    items = result.get("data", {}).get("items", [])
                    
                    # 处理用户数据格式
                    for user in items:
                        user_data = {
                            'open_id': user.get('open_id'),
                            'union_id': user.get('union_id'),
                            'name': user.get('name'),
                            'email': user.get('email'),
                            'mobile': user.get('mobile'),
                            'avatar_url': user.get('avatar', {}).get('url')
                        }
                        users.append(user_data)
                    
                    # 检查是否有下一页
                    page_token = result.get("data", {}).get("page_token")
                    if not page_token:
                        break
                else:
                    logger.error(f"获取飞书用户列表失败: {result}")
                    break
                    
            return users
        except Exception as e:
            logger.error(f"获取飞书用户列表出错: {str(e)}")
            return []
    
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
            
        url = f"https://open.feishu.cn/open-apis/contact/v3/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0:
                return result.get("data", {}).get("user", {})
            else:
                logger.error(f"获取飞书用户详情失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取飞书用户详情出错: {str(e)}")
            return None 