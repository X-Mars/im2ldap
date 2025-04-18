import requests
import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class WeComAPI:
    """企业微信API封装类"""
    
    def __init__(self, corp_id: str, app_secret: str, agent_id: str = None):
        """
        初始化企业微信API
        
        Args:
            corp_id: 企业ID
            app_secret: 应用密钥
            agent_id: 应用ID
        """
        self.corp_id = corp_id
        self.app_secret = app_secret
        self.agent_id = agent_id
        self.access_token = None
        
    def _get_access_token(self) -> Optional[str]:
        """
        获取访问令牌
        
        Returns:
            str: 访问令牌
        """
        if self.access_token:
            return self.access_token
            
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.app_secret}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            if result.get("errcode") == 0:
                self.access_token = result.get("access_token")
                return self.access_token
            else:
                logger.error(f"获取企业微信访问令牌失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取企业微信访问令牌出错: {str(e)}")
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
            
        url = f"https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token={token}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            if result.get("errcode") == 0:
                return result.get("department", [])
            else:
                logger.error(f"获取企业微信部门列表失败: {result}")
                return []
        except Exception as e:
            logger.error(f"获取企业微信部门列表出错: {str(e)}")
            return []
            
    def get_department_users(self, department_id: int, department_name: str) -> List[Dict[str, Any]]:
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
            
        url = f"https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token={token}&department_id={department_id}&fetch_child=0"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            user_list = []
            if result.get("errcode") == 0:
                for user in result.get("userlist", []):
                    user["department"] = department_name
                    user_list.append(user)
                return user_list
            else:
                logger.error(f"获取企业微信部门成员失败: {result}")
                return []
        except Exception as e:
            logger.error(f"获取企业微信部门成员出错: {str(e)}")
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
            dept_id = dept["id"]
            department_name = dept["name"]
            users = self.get_department_users(dept_id, department_name)
            
            for user in users:
                user_id = user.get("userid")
                if user_id and user_id not in user_ids:
                    user_ids.add(user_id)
                    all_users.append(user)
        
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
            
        url = f"https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token={token}&userid={user_id}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            if result.get("errcode") == 0:
                return result
            else:
                logger.error(f"获取企业微信用户详情失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取企业微信用户详情出错: {str(e)}")
            return None 