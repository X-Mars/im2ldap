import logging
from typing import Dict, List, Optional, Any, Union
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException, LDAPEntryAlreadyExistsResult, LDAPOperationResult

logger = logging.getLogger(__name__)

class LDAPConnector:
    """LDAP连接器，用于管理LDAP连接和操作"""
    
    def __init__(self, server_uri: str, bind_dn: str, bind_password: str, base_dn: str, use_ssl: bool = False):
        """
        初始化LDAP连接器
        
        Args:
            server_uri: LDAP服务器URI
            bind_dn: 绑定DN
            bind_password: 绑定密码
            base_dn: 基础DN
            use_ssl: 是否使用SSL
        """
        self.server_uri = server_uri
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.base_dn = base_dn
        self.use_ssl = use_ssl
        self.conn = None
        
    def connect(self) -> bool:
        """
        连接到LDAP服务器
        
        Returns:
            bool: 是否连接成功
        """
        try:
            server = Server(self.server_uri, get_info=ALL, use_ssl=self.use_ssl)
            self.conn = Connection(
                server,
                user=self.bind_dn,
                password=self.bind_password,
                auto_bind=True
            )
            logger.info(f"成功连接到LDAP服务器: {self.server_uri}")
            return True
        except LDAPException as e:
            logger.error(f"连接LDAP服务器失败: {str(e)}")
            return False
            
    def close(self):
        """关闭LDAP连接"""
        if self.conn:
            self.conn.unbind()
            self.conn = None
            
    def search_dn(self, dn: str) -> bool:
        """
        检查指定的DN是否存在
        
        Args:
            dn: 要检查的DN
            
        Returns:
            bool: DN是否存在
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return False
        
        try:
            # 直接尝试使用DN进行搜索，LDAP服务器会返回该DN是否存在
            result = self.conn.search(
                search_base=dn,
                search_filter='(objectClass=*)',
                search_scope='BASE',
                attributes=['1.1']  # 只返回条目存在信息，不返回任何属性
            )
            
            # 如果搜索成功并有条目返回，则DN存在
            exists = result and len(self.conn.entries) > 0
            logger.debug(f"检查DN是否存在: {dn}, 结果: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"检查DN存在性时出错: {dn}, 错误: {str(e)}")
            return False
            
    def search_user(self, uid: str, base_dn: Optional[str] = None) -> Optional[str]:
        """
        根据UID在LDAP中查找用户，并返回用户DN
        
        Args:
            uid: 用户ID
            base_dn: 搜索基础DN，默认为self.base_dn
            
        Returns:
            str or None: 用户DN，未找到则返回None
        """
        return self.search_user_by_uid(uid, base_dn)
            
    def add_user(self, dn: str, attributes: Dict[str, Any]) -> bool:
        """
        添加用户
        
        Args:
            dn: 用户DN
            attributes: 用户属性
            
        Returns:
            bool: 是否添加成功
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return False
            
        try:
            result = self.conn.add(dn, ['inetOrgPerson', 'organizationalPerson', 'person'], attributes)
            if result:
                logger.info(f"添加用户成功: {dn}")
                return True
            else:
                logger.error(f"添加用户失败: {dn}, 原因: {self.conn.result}")
                return False
        except LDAPEntryAlreadyExistsResult:
            # 如果用户已存在，则尝试修改
            logger.info(f"用户已存在，尝试修改: {dn}")
            return self.modify_user(dn, attributes)
        except LDAPException as e:
            logger.error(f"添加用户失败: {dn}, 错误: {str(e)}")
            return False
            
    def modify_user(self, dn: str, attributes: Dict[str, Any]) -> bool:
        """
        修改用户
        
        Args:
            dn: 用户DN
            attributes: 用户属性
            
        Returns:
            bool: 是否修改成功
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return False
            
        try:
            # 将属性转换为ldap3要求的格式
            changes = {attr: [(MODIFY_REPLACE, [val])] for attr, val in attributes.items()}
            result = self.conn.modify(dn, changes)
            
            if result:
                logger.info(f"修改用户成功: {dn}")
                return True
            else:
                logger.error(f"修改用户失败: {dn}, 原因: {self.conn.result}")
                return False
        except LDAPException as e:
            logger.error(f"修改用户失败: {dn}, 错误: {str(e)}")
            return False
            
    def add_object(self, dn: str, attributes: Dict[str, Any]) -> bool:
        """
        添加LDAP对象
        
        Args:
            dn: 对象DN
            attributes: 对象属性
            
        Returns:
            bool: 是否添加成功
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return False
            
        try:
            # 提取对象类
            object_classes = attributes.get('objectClass', ['top'])
            if isinstance(object_classes, str):
                object_classes = [object_classes]
                
            # 创建属性副本，移除objectClass以避免重复
            attrs_copy = dict(attributes)
            if 'objectClass' in attrs_copy:
                del attrs_copy['objectClass']
                
            # 根据DN和属性判断对象类型
            if 'uid=' in dn:
                # 用户对象 - 首先尝试使用最全面的对象类
                user_object_class_options = [
                    # 优先尝试最完整的对象类组合
                    ['top', 'person', 'organizationalPerson', 'inetOrgPerson'],
                    ['top', 'organizationalPerson', 'inetOrgPerson'],
                    ['top', 'inetOrgPerson'],
                    # 如果上面失败，尝试更基本的对象类
                    ['top', 'person', 'organizationalPerson'],
                    ['top', 'organizationalPerson'],
                    ['top', 'person'],
                    # 最后尝试更专用的对象类
                    ['top', 'account'],
                    ['posixAccount'],
                    ['top', 'simpleSecurityObject']
                ]
                
                # 对于每种对象类组合尝试添加，直到成功
                for classes in user_object_class_options:
                    try:
                        # 复制属性以便可以为每种对象类过滤
                        current_attrs = dict(attrs_copy)
                        
                        # 根据对象类过滤属性
                        if 'account' in classes and 'inetOrgPerson' not in classes and 'person' not in classes:
                            # account对象类不支持cn和sn属性
                            filtered_attrs = {}
                            for key, value in current_attrs.items():
                                if key not in ['cn', 'sn']:
                                    filtered_attrs[key] = value
                            current_attrs = filtered_attrs
                        
                        logger.info(f"尝试使用对象类 {classes} 添加: {dn}")
                        result = self.conn.add(dn, classes, current_attrs)
                        
                        if result:
                            logger.info(f"使用对象类 {classes} 添加成功: {dn}")
                            return True
                        else:
                            logger.warning(f"使用对象类 {classes} 添加失败: {dn}, 原因: {self.conn.result}")
                    except Exception as e:
                        logger.debug(f"使用对象类 {classes} 添加失败: {dn}, 错误: {str(e)}")
                        continue
                
                # 如果所有尝试都失败，记录详细错误
                logger.error(f"所有尝试添加用户的方法都失败了: {dn}")
                return False
                
            elif 'ou=' in dn and 'ou' in attrs_copy:
                # 组织单位对象
                object_classes = ['top', 'organizationalUnit']
                
                # 添加对象
                logger.info(f"尝试添加组织单位: {dn}, 对象类: {object_classes}")
                result = self.conn.add(dn, object_classes, attrs_copy)
                
                if result:
                    logger.info(f"添加组织单位成功: {dn}")
                    return True
                else:
                    logger.error(f"添加组织单位失败: {dn}, 原因: {self.conn.result}")
                    return False
            else:
                # 其他类型的对象，使用提供的对象类
                logger.info(f"尝试添加其他类型对象: {dn}, 对象类: {object_classes}")
                result = self.conn.add(dn, object_classes, attrs_copy)
                
                if result:
                    logger.info(f"添加对象成功: {dn}")
                    return True
                else:
                    logger.error(f"添加对象失败: {dn}, 原因: {self.conn.result}")
                    return False
                    
        except LDAPEntryAlreadyExistsResult:
            # 如果对象已存在，则尝试修改
            logger.info(f"对象已存在，尝试修改: {dn}")
            return self.modify_object(dn, attributes)
        except LDAPException as e:
            logger.error(f"添加对象失败: {dn}, 错误: {str(e)}")
            return False
            
    def modify_object(self, dn: str, attributes: Dict[str, Any]) -> bool:
        """
        修改LDAP对象
        
        Args:
            dn: 对象DN
            attributes: 对象属性
            
        Returns:
            bool: 是否修改成功
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return False
            
        try:
            # 创建属性副本，移除objectClass以避免修改对象类
            attrs_copy = dict(attributes)
            if 'objectClass' in attrs_copy:
                del attrs_copy['objectClass']
                
            # 将属性转换为ldap3要求的格式
            changes = {}
            for attr, values in attrs_copy.items():
                if isinstance(values, list):
                    changes[attr] = [(MODIFY_REPLACE, values)]
                else:
                    changes[attr] = [(MODIFY_REPLACE, [values])]
                    
            result = self.conn.modify(dn, changes)
            
            if result:
                logger.info(f"修改对象成功: {dn}")
                return True
            else:
                logger.error(f"修改对象失败: {dn}, 原因: {self.conn.result}")
                return False
        except LDAPException as e:
            logger.error(f"修改对象失败: {dn}, 错误: {str(e)}")
            return False
            
    def add_ou(self, dn: str, attributes: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加组织单位
        
        Args:
            dn: 组织单位DN
            attributes: 组织单位属性，可选
            
        Returns:
            bool: 是否添加成功
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return False
            
        # 默认属性
        ou_attrs = attributes or {}
        
        try:
            # 检查OU是否已存在
            ou_name = dn.split(',')[0].split('=')[1]
            self.conn.search(
                search_base=dn.split(',', 1)[1],
                search_filter=f"(ou={ou_name})",
                search_scope=SUBTREE,
                attributes=['*']
            )
            
            if self.conn.entries:
                logger.info(f"组织单位已存在: {dn}")
                return True
                
            # 创建OU
            result = self.conn.add(dn, ['organizationalUnit'], ou_attrs)
            
            if result:
                logger.info(f"添加组织单位成功: {dn}")
                return True
            else:
                logger.error(f"添加组织单位失败: {dn}, 原因: {self.conn.result}")
                return False
        except LDAPEntryAlreadyExistsResult:
            logger.info(f"组织单位已存在: {dn}")
            return True
        except LDAPException as e:
            logger.error(f"添加组织单位失败: {dn}, 错误: {str(e)}")
            return False
            
    def search_user_by_uid(self, uid: str, base_dn: Optional[str] = None) -> Optional[str]:
        """
        根据UID在LDAP中查找用户，并返回用户DN
        
        Args:
            uid: 用户ID
            base_dn: 搜索基础DN，默认为self.base_dn
            
        Returns:
            str or None: 用户DN，未找到则返回None
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return None
            
        base = base_dn or self.base_dn
        search_filter = f"(uid={uid})"
        
        try:
            logger.debug(f"根据UID搜索用户: {uid}, 基础DN: {base}")
            self.conn.search(
                search_base=base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['*']
            )
            
            if self.conn.entries:
                entry = self.conn.entries[0]
                user_dn = entry.entry_dn
                logger.debug(f"找到用户DN: {user_dn}")
                return user_dn
            else:
                logger.debug(f"未找到UID为 {uid} 的用户")
                return None
        except LDAPException as e:
            logger.error(f"搜索用户失败: {str(e)}")
            return None
            
    def find_department_by_description(self, description_pattern: str, base_dn: Optional[str] = None) -> Optional[str]:
        """
        根据描述信息在LDAP中查找部门，并返回部门DN
        
        Args:
            description_pattern: 描述信息模式，如"企业微信部门ID: 123"
            base_dn: 搜索基础DN，默认为self.base_dn
            
        Returns:
            str or None: 部门DN，未找到则返回None
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return None
            
        base = base_dn or self.base_dn
        # 修复搜索过滤器，使用通配符匹配描述信息
        search_filter = f"(&(objectClass=organizationalUnit)(description=*{description_pattern}*))"
        
        try:
            logger.debug(f"根据描述信息搜索部门: {description_pattern}, 基础DN: {base}")
            self.conn.search(
                search_base=base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['*']
            )
            
            if self.conn.entries:
                entry = self.conn.entries[0]
                dept_dn = entry.entry_dn
                logger.debug(f"找到部门DN: {dept_dn}")
                return dept_dn
            else:
                logger.debug(f"未找到描述为 {description_pattern} 的部门")
                return None
        except LDAPException as e:
            logger.error(f"搜索部门失败: {str(e)}")
            return None
            
    def move_object(self, old_dn: str, new_dn: str) -> bool:
        """
        移动LDAP对象（重命名DN）
        
        Args:
            old_dn: 原DN
            new_dn: 新DN
            
        Returns:
            bool: 是否移动成功
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return False
            
        try:
            # 分解DN
            old_rdn = old_dn.split(',')[0]
            new_rdn = new_dn.split(',')[0]
            old_parent = ','.join(old_dn.split(',')[1:])
            new_parent = ','.join(new_dn.split(',')[1:])
            
            logger.info(f"移动对象: {old_dn} -> {new_dn}")
            logger.debug(f"旧RDN: {old_rdn}, 新RDN: {new_rdn}, 旧上级: {old_parent}, 新上级: {new_parent}")
            
            # 检查是否仅仅是重命名
            if old_parent == new_parent:
                try:
                    # 仅重命名，不修改上级
                    result = self.conn.modify_dn(old_dn, new_rdn)
                    
                    if result:
                        logger.info(f"重命名对象成功: {old_dn} -> {new_dn}")
                        return True
                    else:
                        logger.warning(f"重命名对象失败: {old_dn} -> {new_dn}, 原因: {self.conn.result}")
                except Exception as e:
                    logger.warning(f"重命名对象时发生异常: {str(e)}")
            else:
                try:
                    # 如果需要移动到不同父级，尝试直接使用新DN
                    result = self.conn.modify_dn(old_dn, new_rdn, new_superior=new_parent)
                    
                    if result:
                        logger.info(f"移动并重命名对象成功: {old_dn} -> {new_dn}")
                        return True
                    else:
                        logger.warning(f"移动并重命名对象失败: {old_dn} -> {new_dn}, 原因: {self.conn.result}")
                except Exception as e:
                    logger.warning(f"移动并重命名对象时发生异常: {str(e)}")
            
            # 如果直接方法失败，尝试备选方案 - 复制新建然后删除
            try:
                # 1. 查询旧对象的所有属性
                self.conn.search(
                    search_base=old_dn,
                    search_filter='(objectClass=*)',
                    search_scope='BASE',
                    attributes=['*']
                )
                
                if not self.conn.entries:
                    logger.error(f"无法获取原对象属性: {old_dn}")
                    return False
                
                old_entry = self.conn.entries[0]
                object_classes = old_entry['objectClass'].values
                
                # 2. 建立属性字典
                attrs = {}
                for attr_name in old_entry.entry_attributes:
                    if attr_name.lower() != 'objectclass':  # objectClass会在add时单独提供
                        if hasattr(old_entry[attr_name], 'values') and old_entry[attr_name].values:
                            attrs[attr_name] = old_entry[attr_name].values
                
                # 3. 提取新对象的RDN属性名和值
                new_rdn_attr, new_rdn_value = new_rdn.split('=', 1)
                # 确保RDN属性在新对象的属性中
                attrs[new_rdn_attr] = [new_rdn_value]
                
                # 4. 检查目标位置是否存在对象（防止覆盖）
                if self.search_dn(new_dn):
                    logger.warning(f"目标位置已存在对象，无法复制: {new_dn}")
                    return False
                
                # 5. 创建新对象
                add_result = self.conn.add(new_dn, object_classes, attrs)
                if not add_result:
                    logger.error(f"创建新对象失败: {new_dn}, 原因: {self.conn.result}")
                    return False
                
                # 6. 获取旧对象下的子对象
                try:
                    self.conn.search(
                        search_base=old_dn,
                        search_filter='(objectClass=*)',
                        search_scope='LEVEL',
                        attributes=['*']
                    )
                    
                    child_entries = self.conn.entries
                    
                    # 7. 移动所有子对象到新对象下
                    for child in child_entries:
                        child_dn = child.entry_dn
                        child_rdn = child_dn.split(',')[0]
                        new_child_dn = f"{child_rdn},{new_dn}"
                        
                        # 尝试移动子对象
                        child_move_result = self.move_object(child_dn, new_child_dn)
                        if not child_move_result:
                            logger.warning(f"移动子对象失败: {child_dn} -> {new_child_dn}")
                            # 继续处理其他子对象，不中断流程
                except Exception as e:
                    logger.warning(f"查找或移动子对象时发生异常: {str(e)}")
                
                # 8. 删除旧对象
                try:
                    delete_result = self.conn.delete(old_dn)
                    if not delete_result:
                        logger.warning(f"删除原对象失败: {old_dn}, 原因: {self.conn.result}")
                        # 不影响总体结果，主要是新对象创建成功
                except Exception as e:
                    logger.warning(f"删除原对象时发生异常: {str(e)}")
                
                logger.info(f"通过复制的方式成功移动对象: {old_dn} -> {new_dn}")
                return True
                
            except Exception as e:
                logger.error(f"通过复制方式移动对象时发生异常: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return False
            
            # 所有方法都失败
            logger.error(f"所有尝试移动对象的方法都失败: {old_dn} -> {new_dn}")
            return False
        except Exception as e:
            logger.error(f"移动对象过程中发生未预期的错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    def delete_object(self, dn: str) -> bool:
        """
        删除LDAP对象
        
        Args:
            dn: 对象DN
            
        Returns:
            bool: 是否删除成功
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return False
            
        try:
            logger.info(f"删除对象: {dn}")
            result = self.conn.delete(dn)
            
            if result:
                logger.info(f"删除对象成功: {dn}")
                return True
            else:
                logger.error(f"删除对象失败: {dn}, 原因: {self.conn.result}")
                return False
        except LDAPException as e:
            logger.error(f"删除对象失败: {dn}, 错误: {str(e)}")
            return False
            
    def search_user_with_filter(self, search_filter: str, base_dn: Optional[str] = None) -> Optional[str]:
        """
        使用自定义过滤器在LDAP中查找用户，并返回用户DN
        
        Args:
            search_filter: LDAP搜索过滤器，如"(&(uid=123)(userSource=wecom))"
            base_dn: 搜索基础DN，默认为self.base_dn
            
        Returns:
            str or None: 用户DN，未找到则返回None
        """
        if not self.conn:
            logger.error("未连接到LDAP服务器")
            return None
            
        base = base_dn or self.base_dn
        
        try:
            logger.debug(f"使用过滤器搜索用户: {search_filter}, 基础DN: {base}")
            self.conn.search(
                search_base=base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['*']
            )
            
            if self.conn.entries:
                entry = self.conn.entries[0]
                user_dn = entry.entry_dn
                logger.debug(f"找到用户DN: {user_dn}")
                return user_dn
            else:
                logger.debug(f"未找到符合条件的用户: {search_filter}")
                return None
        except LDAPException as e:
            logger.error(f"搜索用户失败: {str(e)}")
            return None
            
    def get_object_attrs(self, dn):
        """获取LDAP对象的属性"""
        if not self.conn:
            return {}
        
        try:
            self.conn.search(dn, '(objectClass=*)', search_scope='BASE', attributes=['*'])
            if self.conn.entries:
                entry = self.conn.entries[0]
                attrs = {}
                for attr in entry.entry_attributes:
                    attrs[attr] = list(getattr(entry, attr))
                return attrs
            return {}
        except Exception as e:
            logger.error(f"获取对象属性失败: {dn}, 错误: {str(e)}")
            return {}

    def search_entries(self, search_base, search_filter, search_scope='SUBTREE', attributes=None):
        """搜索LDAP条目并返回原始条目列表"""
        if attributes is None:
            attributes = ['*']
        
        if not self.conn:
            return []
        
        try:
            self.conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=search_scope,
                attributes=attributes
            )
            return self.conn.entries
        except Exception as e:
            logger.error(f"LDAP搜索失败: {str(e)}")
            return [] 