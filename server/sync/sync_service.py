import logging
from typing import Dict, List, Optional, Any
from ldap3 import Connection, SUBTREE, MODIFY_REPLACE
from django.utils import timezone

from .models import LDAPConfig, SyncConfig, SyncLog, SyncLogDetail
from .ldap_connector import LDAPConnector

logger = logging.getLogger(__name__)

class SyncService:
    """同步服务，用于将企业微信/飞书/钉钉数据同步到LDAP"""
    
    def __init__(self, sync_config_id: str):
        """
        初始化同步服务
        
        Args:
            sync_config_id: 同步配置ID
        """
        self.sync_config = SyncConfig.objects.get(id=sync_config_id)
        self.ldap_config = self.sync_config.ldap_config
        self.ldap_connector = None
        self.log = None
        self.users_synced = 0  # 初始化用户同步数量
        self.departments_synced = 0  # 初始化部门同步数量
        
    def connect_ldap(self) -> bool:
        """连接到LDAP服务器"""
        try:
            self.ldap_connector = LDAPConnector(
                server_uri=self.ldap_config.server_uri,
                bind_dn=self.ldap_config.bind_dn,
                bind_password=self.ldap_config.bind_password,
                base_dn=self.ldap_config.base_dn,
                use_ssl=self.ldap_config.use_ssl
            )
            return self.ldap_connector.connect()
        except Exception as e:
            logger.error(f"连接LDAP失败: {str(e)}")
            return False
            
    def create_sync_log(self, success=False):
        """创建同步日志"""
        log = SyncLog.objects.create(
            config=self.sync_config,
            success=success,
            users_synced=self.users_synced,
            departments_synced=self.departments_synced
        )
        return log
    
    def ensure_base_ous(self) -> bool:
        """确保基础组织单位存在"""
        if not self.ldap_connector:
            return False
            
        try:
            # 创建用户OU
            if self.sync_config.sync_users and self.sync_config.user_ou:
                user_ou_dn = f"ou={self.sync_config.user_ou},{self.ldap_config.base_dn}"
                self.ldap_connector.add_ou(user_ou_dn)
                
            # 创建部门OU
            if self.sync_config.sync_departments and self.sync_config.department_ou:
                dept_ou_dn = f"ou={self.sync_config.department_ou},{self.ldap_config.base_dn}"
                self.ldap_connector.add_ou(dept_ou_dn)
                
            return True
        except Exception as e:
            logger.error(f"创建基础OU失败: {str(e)}")
            return False
    
    def sync(self) -> SyncLog:
        """执行同步操作"""
        # 创建同步日志
        self.log = self.create_sync_log(success=False)
        
        # 重置计数器
        self.users_synced = 0
        self.departments_synced = 0
        
        try:
            # 连接LDAP
            if not self.connect_ldap():
                self.log.success = False
                self.log.save()
                return self.log
                
            # 确保基础OU存在
            if not self.ensure_base_ous():
                self.log.success = False
                self.log.save()
                return self.log
                
            # 根据同步类型执行不同的同步操作
            if self.sync_config.sync_type == 'wecom':
                # 企业微信同步
                if self.sync_config.sync_departments:
                    self.departments_synced = self._sync_wecom_departments()
                    
                if self.sync_config.sync_users:
                    self.users_synced = self._sync_wecom_users()
                    
            elif self.sync_config.sync_type == 'feishu':
                # 飞书同步
                if self.sync_config.sync_departments:
                    self.departments_synced = self._sync_feishu_departments()
                    
                if self.sync_config.sync_users:
                    self.users_synced = self._sync_feishu_users()
                    
            elif self.sync_config.sync_type == 'dingtalk':
                # 钉钉同步
                if self.sync_config.sync_departments:
                    self.departments_synced = self._sync_dingtalk_departments()
                    
                if self.sync_config.sync_users:
                    self.users_synced = self._sync_dingtalk_users()
            
            # 更新同步记录
            self.log.success = True
            self.log.users_synced = self.users_synced
            self.log.departments_synced = self.departments_synced
            self.log.save()
            
            # 更新上次同步时间
            self.sync_config.last_sync_time = timezone.now()
            self.sync_config.save()
            
            return self.log
            
        except Exception as e:
            error_message = f"同步过程中发生错误: {str(e)}"
            logger.error(error_message)
            self.log.success = False
            self.log.save()
            return self.log
        finally:
            # 关闭LDAP连接
            if self.ldap_connector:
                self.ldap_connector.close()

    def _sync_wecom_departments(self) -> int:
        """同步企业微信部门"""
        from oAuth.models import WeComConfig
        
        try:
            # 获取启用的配置
            config = WeComConfig.objects.filter(enabled=True, sync_enabled=True).first()
            if not config:
                logger.warning("未找到有效的企业微信配置或同步未启用")
                return 0
                
            from utils.wecom_api import WeComAPI
            
            # 初始化API
            wecom_api = WeComAPI(
                corp_id=config.corp_id,
                agent_id=config.agent_id,
                app_secret=config.secret
            )
            
            # 获取所有部门
            departments = wecom_api.get_departments()
            
            if not departments:
                logger.warning("企业微信未返回任何部门数据")
                return 0
                
            logger.info(f"从企业微信获取到 {len(departments)} 个部门")
            
            # 获取LDAP中的部门OU
            dept_ou_dn = f"ou={self.sync_config.department_ou},{self.ldap_config.base_dn}"
            
            # 部门ID和DN的映射
            dept_id_to_dn = {}
            
            # 先确保部门OU存在
            if not self.ldap_connector.search_dn(dept_ou_dn):
                logger.info(f"创建部门基础OU: {dept_ou_dn}")
                self.ldap_connector.add_ou(dept_ou_dn, {'ou': [self.sync_config.department_ou]})
            
            # 按部门ID排序，确保先创建父部门
            departments.sort(key=lambda x: x['id'])
            
            # 建立LDAP部门的映射，用于后续比较
            ldap_dept_map = self._get_existing_dept_map("企业微信部门ID: ")
            
            count = 0
            for dept in departments:
                dept_id = dept['id']
                dept_name = dept['name']
                parent_id = dept.get('parentid', 0)
                
                logger.info(f"处理企业微信部门: ID={dept_id}, 名称={dept_name}, 父ID={parent_id}")
                
                # 首先在LDAP中查找该部门ID对应的部门
                dept_desc = f"企业微信部门ID: {dept_id}"
                
                # 检查部门是否已存在（从前面准备的映射中获取）
                existing_dept_data = ldap_dept_map.get(str(dept_id))
                
                if existing_dept_data:
                    existing_dept_dn = existing_dept_data['dn']
                    existing_dept_name = existing_dept_data['name']
                    existing_parent_id = existing_dept_data.get('parent_id', 0)
                    
                    logger.info(f"找到现有部门DN: {existing_dept_dn}, 名称: {existing_dept_name}")
                    
                    # 确定部门现在应该所在的位置
                    if parent_id == 0 or parent_id not in dept_id_to_dn:
                        # 顶级部门或父部门尚未创建，应挂在部门OU下
                        target_parent_dn = dept_ou_dn
                    else:
                        # 非顶级部门，应挂在父部门下
                        target_parent_dn = dept_id_to_dn[parent_id]
                    
                    # 构建新的目标DN
                    target_dept_dn = f"ou={dept_name},{target_parent_dn}"
                    
                    # 检查是否真正需要更新（名称或位置有变化）
                    name_changed = existing_dept_name != dept_name
                    parent_changed = (parent_id != existing_parent_id) or (existing_dept_dn != target_dept_dn)
                    
                    if name_changed or parent_changed:
                        logger.info(f"检测到部门变更: 名称变更={name_changed}, 位置变更={parent_changed}")
                        
                        # 名称变更，记录日志
                        if name_changed:
                            self.add_log_detail(
                                object_type='department',
                                action='update',
                                object_id=str(dept_id),
                                object_name=dept_name,
                                old_data={'name': existing_dept_name},
                                new_data={'name': dept_name},
                                details=f"更新企业微信部门名称: {existing_dept_name} -> {dept_name}"
                            )
                        
                        # 位置变更，记录日志
                        if parent_changed:
                            old_parent_id = existing_parent_id
                            old_parent_name = "根部门" if old_parent_id == 0 else self._get_dept_name_by_id(old_parent_id, ldap_dept_map)
                            new_parent_name = "根部门" if parent_id == 0 else self._get_dept_name_by_id(parent_id, dept_id_to_dn)
                            
                            self.add_log_detail(
                                object_type='department',
                                action='move',
                                object_id=str(dept_id),
                                object_name=dept_name,
                                old_data={'parent_id': old_parent_id, 'parent_name': old_parent_name},
                                new_data={'parent_id': parent_id, 'parent_name': new_parent_name},
                                details=f"移动企业微信部门: {dept_name} (从 {old_parent_name} 到 {new_parent_name})"
                            )
                        
                        # 尝试移动/重命名部门
                        if existing_dept_dn != target_dept_dn:
                            move_success = self.ldap_connector.move_object(existing_dept_dn, target_dept_dn)
                            
                            if move_success:
                                # 更新部门属性
                                dept_attrs = {
                                    'objectClass': ['top', 'organizationalUnit'],
                                    'ou': [dept_name],
                                    'description': [dept_desc]
                                }
                                
                                self.ldap_connector.modify_object(target_dept_dn, dept_attrs)
                                # 记录新DN
                                dept_id_to_dn[dept_id] = target_dept_dn
                            else:
                                # 如果移动失败，使用旧DN，同时尝试更新属性
                                logger.warning(f"移动部门失败: {existing_dept_dn} -> {target_dept_dn}")
                                # 尝试更新属性，包括部门名称
                                dept_attrs = {
                                    'objectClass': ['top', 'organizationalUnit'],
                                    'ou': [dept_name],
                                    'description': [dept_desc]
                                }
                                self.ldap_connector.modify_object(existing_dept_dn, dept_attrs)
                                dept_id_to_dn[dept_id] = existing_dept_dn
                        else:
                            # 只需更新名称
                            dept_attrs = {
                                'objectClass': ['top', 'organizationalUnit'],
                                'ou': [dept_name],
                                'description': [dept_desc]
                            }
                            self.ldap_connector.modify_object(existing_dept_dn, dept_attrs)
                            dept_id_to_dn[dept_id] = existing_dept_dn
                    else:
                        # 部门无变化，不记录日志，只更新映射
                        logger.info(f"部门 {dept_name} 无变化，跳过更新")
                        dept_id_to_dn[dept_id] = existing_dept_dn
                else:
                    # 部门不存在，需要创建
                    logger.info(f"未找到部门，将创建新部门: ID={dept_id}, 名称={dept_name}")
                    
                    # 构建部门DN
                    if parent_id == 0 or parent_id not in dept_id_to_dn:
                        # 顶级部门或父部门尚未创建，挂在部门OU下
                        dept_dn = f"ou={dept_name},{dept_ou_dn}"
                        parent_name = "根部门"
                    else:
                        # 非顶级部门，挂在父部门下
                        dept_dn = f"ou={dept_name},{dept_id_to_dn[parent_id]}"
                        parent_name = self._get_dept_name_by_id(parent_id, dept_id_to_dn)
                    
                    # 部门属性
                    dept_attrs = {
                        'objectClass': ['top', 'organizationalUnit'],
                        'ou': [dept_name],
                        'description': [dept_desc]
                    }
                    
                    # 创建部门
                    add_success = self.ldap_connector.add_object(dept_dn, dept_attrs)
                    if add_success:
                        logger.info(f"成功创建部门: {dept_dn}")
                        # 记录创建部门的详细日志
                        self.add_log_detail(
                            object_type='department',
                            action='create',
                            object_id=str(dept_id),
                            object_name=dept_name,
                            new_data={
                                'name': dept_name, 
                                'parent_id': parent_id,
                                'parent_name': parent_name
                            },
                            details=f"创建企业微信部门: {dept_name} (父部门: {parent_name})"
                        )
                        # 记录部门ID与DN的映射
                        dept_id_to_dn[dept_id] = dept_dn
                    else:
                        logger.error(f"创建部门失败: {dept_dn}")
                
                count += 1
                
            # 将部门映射存储为同步服务的属性，以便后续用户同步使用
            self.wecom_dept_id_to_dn = dept_id_to_dn
            logger.info(f"同步企业微信部门完成，共处理 {count} 个部门")
                
            return count
            
        except Exception as e:
            logger.error(f"同步企业微信部门失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
        
    def _sync_wecom_users(self) -> int:
        """同步企业微信用户"""
        from oAuth.models import WeComConfig
        
        try:
            # 获取启用的配置
            config = WeComConfig.objects.filter(enabled=True, sync_enabled=True).first()
            if not config:
                logger.warning("未找到有效的企业微信配置或同步未启用")
                return 0
                
            from utils.wecom_api import WeComAPI
            
            # 初始化API
            wecom_api = WeComAPI(
                corp_id=config.corp_id,
                agent_id=config.agent_id,
                app_secret=config.secret
            )
            
            # 获取所有用户
            users = wecom_api.get_users()
            
            if not users:
                logger.warning("企业微信未返回任何用户数据")
                return 0
                
            logger.info(f"从企业微信获取到 {len(users)} 个用户")
            
            # 部门ID和DN的映射应该在同步部门时设置
            if not hasattr(self, 'wecom_dept_id_to_dn') or not self.wecom_dept_id_to_dn:
                logger.warning("未找到部门映射，请先同步部门")
                return 0
                
            # 获取LDAP中的用户OU
            user_ou_dn = f"ou={self.sync_config.user_ou},{self.ldap_config.base_dn}"
            
            # 确保用户OU存在
            if not self.ldap_connector.search_dn(user_ou_dn):
                logger.info(f"创建用户基础OU: {user_ou_dn}")
                self.ldap_connector.add_ou(user_ou_dn, {'ou': [self.sync_config.user_ou]})
            
            # 获取LDAP中的现有用户映射
            ldap_user_map = self._get_existing_user_map("企业微信用户")
            
            count = 0
            for user in users:
                userid = user['userid']
                uid = userid  # 直接使用userid作为uid
                name = user['name']
                mobile = user.get('mobile', '')
                email = user.get('email', '')
                department_ids = user.get('department', [])
                
                logger.info(f"处理企业微信用户: ID={userid}, 姓名={name}, 部门IDs={department_ids}")
                
                # 用户属性
                user_attrs = {
                    'objectClass': ['top', 'person'],
                    'uid': [uid],
                    'userid': [uid],  # 增加userid属性，与uid保持一致
                    'cn': [name],
                    'sn': [name],
                    'employeeNumber': [userid],
                    'description': [f"企业微信用户，用户ID：{userid}"]
                }
                
                if email:
                    user_attrs['mail'] = [email]
                if mobile:
                    user_attrs['telephoneNumber'] = [mobile]
                    
                # 确定用户所属部门DN
                dept_dns = []
                primary_dept_dn = None
                
                for dept_id in department_ids:
                    if dept_id in self.wecom_dept_id_to_dn:
                        dept_dns.append(self.wecom_dept_id_to_dn[dept_id])
                        if not primary_dept_dn:  # 将第一个部门作为主部门
                            primary_dept_dn = self.wecom_dept_id_to_dn[dept_id]
                            
                if not primary_dept_dn:
                    # 如果没有找到有效部门，使用用户OU
                    primary_dept_dn = user_ou_dn
                    
                # 构建用户DN
                user_dn = f"uid={uid},{primary_dept_dn}"
                
                # 检查用户是否已存在
                existing_user_data = ldap_user_map.get(userid)
                
                if existing_user_data:
                    existing_user_dn = existing_user_data['dn']
                    existing_attrs = existing_user_data['attrs']
                    
                    logger.info(f"找到现有用户DN: {existing_user_dn}")
                    
                    # 检查属性是否有变化
                    attrs_changed = False
                    changed_attrs = {}
                    
                    # 检查基本属性变化
                    if existing_attrs.get('cn', [''])[0] != name:
                        attrs_changed = True
                        changed_attrs['姓名'] = {
                            'old': existing_attrs.get('cn', [''])[0],
                            'new': name
                        }
                        
                    if 'mail' in user_attrs and (
                        'mail' not in existing_attrs or 
                        existing_attrs.get('mail', [''])[0] != email
                    ):
                        attrs_changed = True
                        changed_attrs['邮箱'] = {
                            'old': existing_attrs.get('mail', [''])[0] if 'mail' in existing_attrs else '',
                            'new': email
                        }
                        
                    if 'telephoneNumber' in user_attrs and (
                        'telephoneNumber' not in existing_attrs or 
                        existing_attrs.get('telephoneNumber', [''])[0] != mobile
                    ):
                        attrs_changed = True
                        changed_attrs['手机'] = {
                            'old': existing_attrs.get('telephoneNumber', [''])[0] if 'telephoneNumber' in existing_attrs else '',
                            'new': mobile
                        }
                    
                    # 检查是否需要移动用户（部门变更）
                    dn_changed = existing_user_dn != user_dn
                    
                    if attrs_changed or dn_changed:
                        # 记录属性变更日志
                        if attrs_changed:
                            self.add_log_detail(
                                object_type='user',
                                action='update',
                                object_id=userid,
                                object_name=name,
                                old_data={k: v['old'] for k, v in changed_attrs.items()},
                                new_data={k: v['new'] for k, v in changed_attrs.items()},
                                details=f"更新企业微信用户属性: {name}"
                            )
                        
                        # 记录部门变更日志
                        if dn_changed:
                            old_dept = existing_user_dn.split(',', 1)[1]
                            new_dept = user_dn.split(',', 1)[1]
                            self.add_log_detail(
                                object_type='user',
                                action='move',
                                object_id=userid,
                                object_name=name,
                                old_data={'department': old_dept},
                                new_data={'department': new_dept},
                                details=f"移动企业微信用户: {name} (到新部门)"
                            )
                        
                        # 进行实际的更新操作
                        if dn_changed:
                            # 尝试移动用户
                            move_success = self.ldap_connector.move_object(existing_user_dn, user_dn)
                            
                            if move_success:
                                logger.info(f"成功移动用户: {existing_user_dn} -> {user_dn}")
                                # 更新用户属性
                                self.ldap_connector.modify_object(user_dn, user_attrs)
                            else:
                                logger.warning(f"移动用户失败: {existing_user_dn} -> {user_dn}")
                                # 在原位置更新用户属性
                                self.ldap_connector.modify_object(existing_user_dn, user_attrs)
                        else:
                            # 只更新用户属性
                            self.ldap_connector.modify_object(existing_user_dn, user_attrs)
                            logger.info(f"已更新用户属性: {existing_user_dn}")
                    else:
                        logger.info(f"用户 {name} 无变化，跳过更新")
                else:
                    # 创建新用户
                    logger.info(f"创建新用户: {user_dn}")
                    add_success = self.ldap_connector.add_object(user_dn, user_attrs)
                    
                    if add_success:
                        # 记录创建用户日志
                        self.add_log_detail(
                            object_type='user',
                            action='create',
                            object_id=userid,
                            object_name=name,
                            new_data={
                                'name': name,
                                'department': primary_dept_dn,
                                'email': email if email else '',
                                'mobile': mobile if mobile else ''
                            },
                            details=f"创建企业微信用户: {name}"
                        )
                        logger.info(f"成功创建用户: {user_dn}")
                    else:
                        logger.error(f"创建用户失败: {user_dn}")
                
                count += 1
            
            logger.info(f"同步企业微信用户完成，共处理 {count} 个用户")
            return count
            
        except Exception as e:
            logger.error(f"同步企业微信用户失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
        
    def _sync_feishu_departments(self) -> int:
        """同步飞书部门"""
        from oAuth.models import FeiShuConfig
        
        try:
            # 获取启用的配置
            config = FeiShuConfig.objects.filter(enabled=True, sync_enabled=True).first()
            if not config:
                logger.warning("未找到有效的飞书配置或同步未启用")
                return 0
                
            from utils.feishu_api import FeiShuAPI
            
            # 初始化API
            feishu_api = FeiShuAPI(
                app_id=config.app_id,
                app_secret=config.app_secret
            )
            
            # 获取所有部门
            departments = feishu_api.get_departments()
            
            if not departments:
                logger.warning("飞书未返回任何部门数据")
                return 0
                
            logger.info(f"从飞书获取到 {len(departments)} 个部门")
            
            # 获取LDAP中的部门OU
            dept_ou_dn = f"ou={self.sync_config.department_ou},{self.ldap_config.base_dn}"
            
            # 部门ID和DN的映射
            dept_id_to_dn = {}
            
            # 按部门ID排序，确保先创建父部门
            departments.sort(key=lambda x: x['department_id'])
            
            count = 0
            for dept in departments:
                dept_id = dept['department_id']
                dept_name = dept['name']
                parent_id = dept.get('parent_department_id', '0')
                
                # 首先在LDAP中查找该部门ID对应的部门
                existing_dept_dn = self.ldap_connector.find_department_by_description(f"飞书部门ID: {dept_id}", self.ldap_config.base_dn)
                
                if existing_dept_dn:
                    # 部门已存在，检查名称是否需要更新
                    existing_dept_name = existing_dept_dn.split(',')[0].split('=')[1]
                    
                    # 确定部门现在应该所在的位置
                    if parent_id == '0' or parent_id not in dept_id_to_dn:
                        # 顶级部门或父部门尚未创建，应挂在部门OU下
                        target_parent_dn = dept_ou_dn
                    else:
                        # 非顶级部门，应挂在父部门下
                        target_parent_dn = dept_id_to_dn[parent_id]
                    
                    # 构建新的目标DN
                    target_dept_dn = f"ou={dept_name},{target_parent_dn}"
                    
                    # 检查是否需要移动或重命名
                    if existing_dept_dn != target_dept_dn:
                        logger.info(f"检测到部门变更: {existing_dept_dn} -> {target_dept_dn}")
                        
                        # 尝试移动/重命名部门
                        move_success = self.ldap_connector.move_object(existing_dept_dn, target_dept_dn)
                        
                        if move_success:
                            # 更新部门属性
                            dept_attrs = {
                                'objectClass': ['top', 'organizationalUnit'],
                                'ou': [dept_name],
                                'description': [f"飞书部门ID: {dept_id}"]
                            }
                            
                            self.ldap_connector.modify_object(target_dept_dn, dept_attrs)
                            # 记录新DN
                            dept_id_to_dn[dept_id] = target_dept_dn
                        else:
                            # 如果移动失败，使用旧DN
                            logger.warning(f"移动部门失败: {existing_dept_dn} -> {target_dept_dn}")
                            dept_id_to_dn[dept_id] = existing_dept_dn
                    else:
                        # 部门位置和名称未变，只需更新属性
                        dept_attrs = {
                            'objectClass': ['top', 'organizationalUnit'],
                            'ou': [dept_name],
                            'description': [f"飞书部门ID: {dept_id}"]
                        }
                        
                        self.ldap_connector.modify_object(existing_dept_dn, dept_attrs)
                        # 记录DN
                        dept_id_to_dn[dept_id] = existing_dept_dn
                else:
                    # 部门不存在，需要创建
                    # 构建部门DN
                    if parent_id == '0' or parent_id not in dept_id_to_dn:
                        # 顶级部门或父部门尚未创建，挂在部门OU下
                        dept_dn = f"ou={dept_name},{dept_ou_dn}"
                    else:
                        # 非顶级部门，挂在父部门下
                        dept_dn = f"ou={dept_name},{dept_id_to_dn[parent_id]}"
                    
                    # 部门属性
                    dept_attrs = {
                        'objectClass': ['top', 'organizationalUnit'],
                        'ou': [dept_name],
                        'description': [f"飞书部门ID: {dept_id}"]
                    }
                    
                    # 创建部门
                    self.ldap_connector.add_object(dept_dn, dept_attrs)
                    # 记录部门ID与DN的映射
                    dept_id_to_dn[dept_id] = dept_dn
                
                count += 1
                
            # 将部门映射存储为同步服务的属性，以便后续用户同步使用
            self.feishu_dept_id_to_dn = dept_id_to_dn
                
            return count
            
        except Exception as e:
            logger.error(f"同步飞书部门失败: {str(e)}")
            return 0
        
    def _sync_feishu_users(self) -> int:
        """同步飞书用户"""
        from oAuth.models import FeiShuConfig
        
        try:
            # 获取启用的配置
            config = FeiShuConfig.objects.filter(enabled=True, sync_enabled=True).first()
            if not config:
                logger.warning("未找到有效的飞书配置或同步未启用")
                return 0
                
            from utils.feishu_api import FeiShuAPI
            
            # 初始化API
            feishu_api = FeiShuAPI(
                app_id=config.app_id,
                app_secret=config.app_secret
            )
            
            # 获取所有用户
            users = feishu_api.get_users()
            
            if not users:
                logger.warning("飞书未返回任何用户数据")
                return 0
                
            logger.info(f"从飞书获取到 {len(users)} 个用户")
            
            # 部门ID和DN的映射应该在同步部门时设置
            if not hasattr(self, 'feishu_dept_id_to_dn') or not self.feishu_dept_id_to_dn:
                logger.warning("未找到部门映射，请先同步部门")
                return 0
                
            # 获取LDAP中的用户OU
            user_ou_dn = f"ou={self.sync_config.user_ou},{self.ldap_config.base_dn}"
            
            # 确保用户OU存在
            if not self.ldap_connector.search_dn(user_ou_dn):
                logger.info(f"创建用户基础OU: {user_ou_dn}")
                self.ldap_connector.add_ou(user_ou_dn, {'ou': [self.sync_config.user_ou]})
            
            # 获取LDAP中的现有用户映射
            ldap_user_map = self._get_existing_user_map("飞书用户")
            
            count = 0
            for user in users:
                userid = user['user_id']
                uid = userid  # 直接使用userid作为uid
                name = user['name']
                mobile = user.get('mobile', '')
                email = user.get('email', '')
                department_ids = user.get('department_ids', [])
                
                logger.info(f"处理飞书用户: ID={userid}, 姓名={name}, 部门IDs={department_ids}")
                
                # 用户属性
                user_attrs = {
                    'objectClass': ['top', 'person'],
                    'uid': [uid],
                    'userid': [uid],
                    'cn': [name],
                    'sn': [name],
                    'employeeNumber': [userid],
                    'description': [f"飞书用户，用户ID：{userid}"]
                }
                
                if email:
                    user_attrs['mail'] = [email]
                if mobile:
                    user_attrs['telephoneNumber'] = [mobile]
                    
                # 确定用户所属部门DN
                dept_dns = []
                primary_dept_dn = None
                
                for dept_id in department_ids:
                    if dept_id in self.feishu_dept_id_to_dn:
                        dept_dns.append(self.feishu_dept_id_to_dn[dept_id])
                        if not primary_dept_dn:  # 将第一个部门作为主部门
                            primary_dept_dn = self.feishu_dept_id_to_dn[dept_id]
                            
                if not primary_dept_dn:
                    # 如果没有找到有效部门，使用用户OU
                    primary_dept_dn = user_ou_dn
                    
                # 构建用户DN
                user_dn = f"uid={uid},{primary_dept_dn}"
                
                # 检查用户是否已存在
                existing_user_data = ldap_user_map.get(userid)
                
                if existing_user_data:
                    existing_user_dn = existing_user_data['dn']
                    existing_attrs = existing_user_data['attrs']
                    
                    logger.info(f"找到现有用户DN: {existing_user_dn}")
                    
                    # 检查属性是否有变化
                    attrs_changed = False
                    changed_attrs = {}
                    
                    # 检查基本属性变化
                    if existing_attrs.get('cn', [''])[0] != name:
                        attrs_changed = True
                        changed_attrs['姓名'] = {
                            'old': existing_attrs.get('cn', [''])[0],
                            'new': name
                        }
                        
                    if 'mail' in user_attrs and (
                        'mail' not in existing_attrs or 
                        existing_attrs.get('mail', [''])[0] != email
                    ):
                        attrs_changed = True
                        changed_attrs['邮箱'] = {
                            'old': existing_attrs.get('mail', [''])[0] if 'mail' in existing_attrs else '',
                            'new': email
                        }
                        
                    if 'telephoneNumber' in user_attrs and (
                        'telephoneNumber' not in existing_attrs or 
                        existing_attrs.get('telephoneNumber', [''])[0] != mobile
                    ):
                        attrs_changed = True
                        changed_attrs['手机'] = {
                            'old': existing_attrs.get('telephoneNumber', [''])[0] if 'telephoneNumber' in existing_attrs else '',
                            'new': mobile
                        }
                    
                    # 检查是否需要移动用户（部门变更）
                    dn_changed = existing_user_dn != user_dn
                    
                    if attrs_changed or dn_changed:
                        # 记录属性变更日志
                        if attrs_changed:
                            self.add_log_detail(
                                object_type='user',
                                action='update',
                                object_id=userid,
                                object_name=name,
                                old_data={k: v['old'] for k, v in changed_attrs.items()},
                                new_data={k: v['new'] for k, v in changed_attrs.items()},
                                details=f"更新飞书用户属性: {name}"
                            )
                        
                        # 记录部门变更日志
                        if dn_changed:
                            old_dept = existing_user_dn.split(',', 1)[1]
                            new_dept = user_dn.split(',', 1)[1]
                            self.add_log_detail(
                                object_type='user',
                                action='move',
                                object_id=userid,
                                object_name=name,
                                old_data={'department': old_dept},
                                new_data={'department': new_dept},
                                details=f"移动飞书用户: {name} (到新部门)"
                            )
                        
                        # 进行实际的更新操作
                        if dn_changed:
                            # 尝试移动用户
                            move_success = self.ldap_connector.move_object(existing_user_dn, user_dn)
                            
                            if move_success:
                                logger.info(f"成功移动用户: {existing_user_dn} -> {user_dn}")
                                # 更新用户属性
                                self.ldap_connector.modify_object(user_dn, user_attrs)
                            else:
                                logger.warning(f"移动用户失败: {existing_user_dn} -> {user_dn}")
                                # 在原位置更新用户属性
                                self.ldap_connector.modify_object(existing_user_dn, user_attrs)
                        else:
                            # 只更新用户属性
                            self.ldap_connector.modify_object(existing_user_dn, user_attrs)
                            logger.info(f"已更新用户属性: {existing_user_dn}")
                    else:
                        logger.info(f"用户 {name} 无变化，跳过更新")
                else:
                    # 创建新用户
                    logger.info(f"创建新用户: {user_dn}")
                    add_success = self.ldap_connector.add_object(user_dn, user_attrs)
                    
                    if add_success:
                        # 记录创建用户日志
                        self.add_log_detail(
                            object_type='user',
                            action='create',
                            object_id=userid,
                            object_name=name,
                            new_data={
                                'name': name,
                                'department': primary_dept_dn,
                                'email': email if email else '',
                                'mobile': mobile if mobile else ''
                            },
                            details=f"创建飞书用户: {name}"
                        )
                        logger.info(f"成功创建用户: {user_dn}")
                    else:
                        logger.error(f"创建用户失败: {user_dn}")
                
                count += 1
            
            logger.info(f"同步飞书用户完成，共处理 {count} 个用户")
            return count
            
        except Exception as e:
            logger.error(f"同步飞书用户失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
        
    def _sync_dingtalk_departments(self) -> int:
        """同步钉钉部门"""
        from oAuth.models import DingTalkConfig
        
        try:
            # 获取启用的配置
            config = DingTalkConfig.objects.filter(enabled=True, sync_enabled=True).first()
            if not config:
                logger.warning("未找到有效的钉钉配置或同步未启用")
                return 0
                
            from utils.dingtalk_api import DingTalkAPI
            
            # 初始化API
            dingtalk_api = DingTalkAPI(
                client_id=config.client_id,
                client_secret=config.client_secret,
                app_id=config.app_id
            )
            
            # 获取所有部门
            departments = dingtalk_api.get_departments()
            
            if not departments:
                logger.warning("钉钉未返回任何部门数据")
                return 0
                
            logger.info(f"从钉钉获取到 {len(departments)} 个部门")
            
            # 获取LDAP中的部门OU
            dept_ou_dn = f"ou={self.sync_config.department_ou},{self.ldap_config.base_dn}"
            
            # 部门ID和DN的映射
            dept_id_to_dn = {}
            
            # 按部门ID排序，确保先创建父部门
            departments.sort(key=lambda x: x['dept_id'])
            
            count = 0
            for dept in departments:
                dept_id = dept['dept_id']
                dept_name = dept['name']
                parent_id = dept.get('parent_id', 1)
                
                # 首先在LDAP中查找该部门ID对应的部门
                existing_dept_dn = self.ldap_connector.find_department_by_description(f"钉钉部门ID: {dept_id}", self.ldap_config.base_dn)
                
                if existing_dept_dn:
                    # 部门已存在，检查名称是否需要更新
                    existing_dept_name = existing_dept_dn.split(',')[0].split('=')[1]
                    
                    # 确定部门现在应该所在的位置
                    if parent_id == 1 or parent_id not in dept_id_to_dn:
                        # 顶级部门或父部门尚未创建，应挂在部门OU下
                        target_parent_dn = dept_ou_dn
                    else:
                        # 非顶级部门，应挂在父部门下
                        target_parent_dn = dept_id_to_dn[parent_id]
                    
                    # 构建新的目标DN
                    target_dept_dn = f"ou={dept_name},{target_parent_dn}"
                    
                    # 检查是否需要移动或重命名
                    if existing_dept_dn != target_dept_dn:
                        logger.info(f"检测到部门变更: {existing_dept_dn} -> {target_dept_dn}")
                        
                        # 尝试移动/重命名部门
                        move_success = self.ldap_connector.move_object(existing_dept_dn, target_dept_dn)
                        
                        if move_success:
                            # 更新部门属性
                            dept_attrs = {
                                'objectClass': ['top', 'organizationalUnit'],
                                'ou': [dept_name],
                                'description': [f"钉钉部门ID: {dept_id}"]
                            }
                            
                            self.ldap_connector.modify_object(target_dept_dn, dept_attrs)
                            # 记录新DN
                            dept_id_to_dn[dept_id] = target_dept_dn
                        else:
                            # 如果移动失败，使用旧DN
                            logger.warning(f"移动部门失败: {existing_dept_dn} -> {target_dept_dn}")
                            dept_id_to_dn[dept_id] = existing_dept_dn
                    else:
                        # 部门位置和名称未变，只需更新属性
                        dept_attrs = {
                            'objectClass': ['top', 'organizationalUnit'],
                            'ou': [dept_name],
                            'description': [f"钉钉部门ID: {dept_id}"]
                        }
                        
                        self.ldap_connector.modify_object(existing_dept_dn, dept_attrs)
                        # 记录DN
                        dept_id_to_dn[dept_id] = existing_dept_dn
                else:
                    # 部门不存在，需要创建
                    # 构建部门DN
                    if parent_id == 1 or parent_id not in dept_id_to_dn:
                        # 顶级部门或父部门尚未创建，挂在部门OU下
                        dept_dn = f"ou={dept_name},{dept_ou_dn}"
                    else:
                        # 非顶级部门，挂在父部门下
                        dept_dn = f"ou={dept_name},{dept_id_to_dn[parent_id]}"
                    
                    # 部门属性
                    dept_attrs = {
                        'objectClass': ['top', 'organizationalUnit'],
                        'ou': [dept_name],
                        'description': [f"钉钉部门ID: {dept_id}"]
                    }
                    
                    # 创建部门
                    self.ldap_connector.add_object(dept_dn, dept_attrs)
                    # 记录部门ID与DN的映射
                    dept_id_to_dn[dept_id] = dept_dn
                
                count += 1
                
            # 将部门映射存储为同步服务的属性，以便后续用户同步使用
            self.dingtalk_dept_id_to_dn = dept_id_to_dn
                
            return count
            
        except Exception as e:
            logger.error(f"同步钉钉部门失败: {str(e)}")
            return 0
        
    def _sync_dingtalk_users(self) -> int:
        """同步钉钉用户"""
        from oAuth.models import DingTalkConfig
        
        try:
            # 获取启用的配置
            config = DingTalkConfig.objects.filter(enabled=True, sync_enabled=True).first()
            if not config:
                logger.warning("未找到有效的钉钉配置或同步未启用")
                return 0
                
            from utils.dingtalk_api import DingTalkAPI
            
            # 初始化API
            dingtalk_api = DingTalkAPI(
                client_id=config.client_id,
                client_secret=config.client_secret,
                app_id=config.app_id
            )
            
            # 获取所有用户
            users = dingtalk_api.get_users()
            
            if not users:
                logger.warning("钉钉未返回任何用户数据")
                return 0
                
            logger.info(f"从钉钉获取到 {len(users)} 个用户")
            
            # 部门ID和DN的映射应该在同步部门时设置
            if not hasattr(self, 'dingtalk_dept_id_to_dn') or not self.dingtalk_dept_id_to_dn:
                logger.warning("未找到部门映射，请先同步部门")
                return 0
                
            # 获取LDAP中的用户OU
            user_ou_dn = f"ou={self.sync_config.user_ou},{self.ldap_config.base_dn}"
            
            # 确保用户OU存在
            if not self.ldap_connector.search_dn(user_ou_dn):
                logger.info(f"创建用户基础OU: {user_ou_dn}")
                self.ldap_connector.add_ou(user_ou_dn, {'ou': [self.sync_config.user_ou]})
                
            count = 0
            for user in users:
                userid = user['userid']
                uid = userid  # 直接使用userid作为uid
                name = user['name']
                mobile = user.get('mobile', '')
                email = user.get('email', '')
                department_ids = user.get('dept_id_list', [])
                
                logger.info(f"处理钉钉用户: ID={userid}, 姓名={name}, 部门IDs={department_ids}")
                
                # 用户属性
                user_attrs = {
                    'objectClass': ['top', 'person'],
                    'uid': [uid],
                    'userid': [uid],  # 增加userid属性，与uid保持一致
                    'cn': [name],
                    'sn': [name],
                    'employeeNumber': [userid],
                    'description': [f"钉钉用户，用户ID：{userid}"]
                }
                
                if email:
                    user_attrs['mail'] = [email]
                if mobile:
                    user_attrs['telephoneNumber'] = [mobile]
                    
                # 确定用户所属部门DN
                dept_dns = []
                primary_dept_dn = None
                
                for dept_id in department_ids:
                    if dept_id in self.dingtalk_dept_id_to_dn:
                        dept_dns.append(self.dingtalk_dept_id_to_dn[dept_id])
                        if not primary_dept_dn:  # 将第一个部门作为主部门
                            primary_dept_dn = self.dingtalk_dept_id_to_dn[dept_id]
                            
                if not primary_dept_dn:
                    # 如果没有找到有效部门，使用用户OU
                    primary_dept_dn = user_ou_dn
                    
                # 构建用户DN
                user_dn = f"uid={uid},{primary_dept_dn}"
                
                # 检查用户是否已存在（通过uid查找）
                try:
                    userid = user.get('userid')
                    name = user.get('name')
                    email = user.get('email', '')
                    mobile = user.get('mobile', '')
                    department_ids = user.get('dept_id_list', [])
                    
                    logger.info(f"处理钉钉用户: ID={userid}, 姓名={name}, 部门IDs={department_ids}")
                    
                    if not userid or not name:
                        logger.warning(f"用户数据不完整，跳过: {user}")
                        continue
                        
                    # 使用钉钉userid作为LDAP的uid
                    uid = f"dingtalk_{userid}"
                    
                    # 检查用户是否已存在（通过uid查找）
                    existing_user_dn = self.ldap_connector.search_user_by_uid(uid, self.ldap_config.base_dn)
                    
                    # 确定用户所属部门DN
                    dept_dns = []
                    primary_dept_dn = None
                    
                    for dept_id in department_ids:
                        if dept_id in self.dingtalk_dept_id_to_dn:
                            dept_dns.append(self.dingtalk_dept_id_to_dn[dept_id])
                            if not primary_dept_dn:  # 将第一个部门作为主部门
                                primary_dept_dn = self.dingtalk_dept_id_to_dn[dept_id]
                                
                    if not primary_dept_dn:
                        # 如果没有找到有效部门，使用用户OU
                        primary_dept_dn = user_ou_dn
                        
                    # 构建用户DN
                    user_dn = f"uid={uid},{primary_dept_dn}"
                    
                    # 用户属性
                    cn = name
                    sn = name[0] if name else "Unknown"  # 姓氏默认使用名字的第一个字符
                    
                    user_attrs = {
                        'objectClass': ['top', 'person'],
                        'cn': [cn],
                        'sn': [sn],
                        'uid': [uid],
                        'employeeNumber': [userid],
                        'displayName': [name],
                        'description': [f"钉钉用户ID: {userid}"]
                    }
                    
                    if email:
                        user_attrs['mail'] = [email]
                    if mobile:
                        user_attrs['telephoneNumber'] = [mobile]
                        
                    # 添加部门属性
                    if dept_dns:
                        user_attrs['departmentNumber'] = dept_dns
                        
                    if existing_user_dn:
                        logger.info(f"找到现有用户DN: {existing_user_dn}")
                        
                        # 检查是否需要移动用户
                        if existing_user_dn != user_dn:
                            logger.info(f"检测到用户部门变更: {existing_user_dn} -> {user_dn}")
                            
                            # 尝试移动用户
                            move_success = self.ldap_connector.move_object(existing_user_dn, user_dn)
                            
                            if move_success:
                                logger.info(f"成功移动用户: {existing_user_dn} -> {user_dn}")
                                # 更新用户属性
                                self.ldap_connector.modify_object(user_dn, user_attrs)
                            else:
                                logger.warning(f"移动用户失败: {existing_user_dn} -> {user_dn}")
                                # 在原位置更新用户属性
                                self.ldap_connector.modify_object(existing_user_dn, user_attrs)
                        else:
                            # 更新用户属性
                            self.ldap_connector.modify_object(existing_user_dn, user_attrs)
                            logger.info(f"已更新用户属性: {existing_user_dn}")
                    else:
                        # 创建新用户
                        logger.info(f"创建新用户: {user_dn}")
                        self.ldap_connector.add_object(user_dn, user_attrs)
                        
                    count += 1
                except Exception as e:
                    logger.error(f"处理用户 {user.get('userid')} 失败: {str(e)}")
                    continue
                    
            logger.info(f"同步钉钉用户完成，共处理 {count} 个用户")
            return count
            
        except Exception as e:
            logger.error(f"同步钉钉用户失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0 

    def add_log_detail(self, object_type, action, object_id, object_name, old_data=None, new_data=None, details=""):
        """添加同步日志详情"""
        if not self.log:
            return
        
        SyncLogDetail.objects.create(
            sync_log=self.log,
            object_type=object_type,
            action=action,
            object_id=object_id,
            object_name=object_name,
            old_data=old_data,
            new_data=new_data,
            details=details
        ) 

    def _get_existing_dept_map(self, desc_prefix: str) -> dict:
        """获取LDAP中已存在的部门映射
        
        返回格式: {
            "部门ID": {
                "dn": "部门DN",
                "name": "部门名称",
                "parent_id": 父部门ID,
                ...其他属性
            }
        }
        """
        dept_map = {}
        
        try:
            # 获取基础DN下所有部门
            search_filter = f"(&(objectClass=organizationalUnit)(description={desc_prefix}*))"
            entries = self.ldap_connector.search_entries(self.ldap_config.base_dn, search_filter, search_scope='SUBTREE')
            
            for entry in entries:
                dn = entry.entry_dn
                attrs = {}
                
                # 提取部门ID
                desc = getattr(entry, 'description', [])
                if not desc:
                    continue
                    
                desc_value = desc.value
                if isinstance(desc_value, list) and desc_value:
                    desc_value = desc_value[0]
                    
                if not desc_value.startswith(desc_prefix):
                    continue
                    
                dept_id = desc_value[len(desc_prefix):].strip()
                
                # 提取部门名称
                name = getattr(entry, 'ou', []).value
                if isinstance(name, list) and name:
                    name = name[0]
                    
                # 确定父部门ID
                parent_id = 0  # 默认为顶级部门
                parent_dn = ",".join(dn.split(",")[1:])  # 获取父DN
                
                # 从其他映射中找出父部门ID
                for pid, pdata in dept_map.items():
                    if pdata['dn'] == parent_dn:
                        parent_id = int(pid)
                        break
                
                # 存储部门信息
                dept_map[dept_id] = {
                    'dn': dn,
                    'name': name,
                    'parent_id': parent_id,
                    # 可以添加其他需要的属性
                }
                
            return dept_map
        except Exception as e:
            logger.error(f"获取已存在部门映射失败: {str(e)}")
            return {}

    def _get_dept_name_by_id(self, dept_id, dept_map):
        """根据部门ID获取部门名称"""
        if isinstance(dept_map, dict):
            # 如果是ID到数据的映射
            if str(dept_id) in dept_map:
                dept_data = dept_map[str(dept_id)]
                if isinstance(dept_data, dict) and 'name' in dept_data:
                    return dept_data['name']
            
            # 如果是ID到DN的映射
            if dept_id in dept_map:
                dn = dept_map[dept_id]
                if isinstance(dn, str):
                    # 从DN中提取名称
                    return dn.split(',')[0].split('=')[1]
        
        return f"未知部门({dept_id})" 

    def _get_existing_user_map(self, desc_prefix: str) -> dict:
        """获取LDAP中已存在的用户映射
        
        返回格式: {
            "用户ID": {
                "dn": "用户DN",
                "attrs": {
                    "属性名": ["属性值"],
                    ...
                }
            }
        }
        """
        user_map = {}
        
        try:
            # 获取基础DN下所有包含指定描述前缀的用户
            search_filter = f"(&(objectClass=person)(description=*{desc_prefix}*))"
            entries = self.ldap_connector.search_entries(self.ldap_config.base_dn, search_filter, search_scope='SUBTREE')
            
            for entry in entries:
                dn = entry.entry_dn
                attrs = {}
                
                # 提取用户属性
                for attr_name in entry.entry_attributes:
                    attr_values = getattr(entry, attr_name).values
                    if attr_values:
                        attrs[attr_name] = attr_values
                
                # 提取用户ID
                userid = attrs.get('userid', [None])[0]
                if not userid:
                    employeeNumber = attrs.get('employeeNumber', [None])[0]
                    if employeeNumber:
                        userid = employeeNumber
                    else:
                        # 尝试从uid提取
                        uid = attrs.get('uid', [None])[0]
                        if uid:
                            # 如果uid格式为 "platform_id"，则提取id部分
                            if '_' in uid:
                                userid = uid.split('_', 1)[1]
                            else:
                                userid = uid
                
                # 如果仍然没有找到userid，则跳过
                if not userid:
                    logger.warning(f"无法从用户 {dn} 提取userid")
                    continue
                    
                # 存储用户信息
                user_map[userid] = {
                    'dn': dn,
                    'attrs': attrs
                }
                
            return user_map
        except Exception as e:
            logger.error(f"获取已存在用户映射失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {} 