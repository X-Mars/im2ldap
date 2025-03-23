from django.db import models
from django.utils import timezone
import uuid

class LDAPConfig(models.Model):
    """LDAP服务器配置"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server_uri = models.CharField(max_length=255, verbose_name="服务器URI")
    bind_dn = models.CharField(max_length=255, verbose_name="绑定DN")
    bind_password = models.CharField(max_length=255, verbose_name="绑定密码")
    base_dn = models.CharField(max_length=255, verbose_name="基础DN")
    use_ssl = models.BooleanField(default=False, verbose_name="使用SSL")
    enabled = models.BooleanField(default=True, verbose_name="启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "LDAP配置"
        verbose_name_plural = "LDAP配置"
    
    def __str__(self):
        return self.server_uri

class SyncConfig(models.Model):
    """同步配置"""
    
    SYNC_TYPE_CHOICES = (
        ('wecom', '企业微信'),
        ('feishu', '飞书'),
        ('dingtalk', '钉钉'),
    )
    
    SYNC_FREQUENCY_CHOICES = (
        ('realtime', '实时同步'),
        ('hourly', '每小时'),
        ('daily', '每天'),
        ('weekly', '每周'),
        ('manual', '手动'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="配置名称")
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES, verbose_name="同步类型")
    ldap_config = models.ForeignKey(LDAPConfig, on_delete=models.CASCADE, verbose_name="LDAP配置")
    sync_users = models.BooleanField(default=True, verbose_name="同步用户")
    sync_departments = models.BooleanField(default=True, verbose_name="同步部门")
    user_ou = models.CharField(max_length=255, default="users", verbose_name="用户OU")
    department_ou = models.CharField(max_length=255, default="departments", verbose_name="部门OU")
    sync_frequency = models.CharField(max_length=20, choices=SYNC_FREQUENCY_CHOICES, default="manual", verbose_name="同步频率")
    last_sync_time = models.DateTimeField(null=True, blank=True, verbose_name="上次同步时间")
    enabled = models.BooleanField(default=True, verbose_name="启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "同步配置"
        verbose_name_plural = "同步配置"
    
    def __str__(self):
        return self.name

class SyncLog(models.Model):
    """同步日志"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(SyncConfig, on_delete=models.CASCADE, related_name='logs', verbose_name="同步配置")
    sync_time = models.DateTimeField(default=timezone.now, verbose_name="同步时间")
    success = models.BooleanField(default=False, verbose_name="是否成功")
    users_synced = models.IntegerField(default=0, verbose_name="同步用户数")
    departments_synced = models.IntegerField(default=0, verbose_name="同步部门数")
    
    class Meta:
        verbose_name = "同步日志"
        verbose_name_plural = "同步日志"
        ordering = ['-sync_time']
    
    def __str__(self):
        return f"{self.config.name} - {self.sync_time.strftime('%Y-%m-%d %H:%M:%S')}"

class SyncLogDetail(models.Model):
    """同步日志详情"""
    
    OBJECT_TYPE_CHOICES = (
        ('user', '用户'),
        ('department', '部门'),
    )
    
    ACTION_CHOICES = (
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('move', '移动'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sync_log = models.ForeignKey(SyncLog, on_delete=models.CASCADE, related_name='details', verbose_name="所属同步日志")
    object_type = models.CharField(max_length=20, choices=OBJECT_TYPE_CHOICES, verbose_name="对象类型")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="操作类型")
    object_id = models.CharField(max_length=255, verbose_name="对象ID")
    object_name = models.CharField(max_length=255, verbose_name="对象名称")
    old_data = models.JSONField(null=True, blank=True, verbose_name="原数据")
    new_data = models.JSONField(null=True, blank=True, verbose_name="新数据")
    details = models.TextField(blank=True, verbose_name="详情描述")
    
    class Meta:
        verbose_name = "同步日志详情"
        verbose_name_plural = "同步日志详情"
        ordering = ['object_type', 'action', 'object_name']
    
    def __str__(self):
        return f"{self.get_object_type_display()} {self.object_name} - {self.get_action_display()}" 