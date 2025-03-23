import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import re


def validate_password_strength(password):
    """
    验证密码强度
    要求：
    1. 长度至少6位
    2. 包含大写字母
    3. 包含小写字母
    4. 包含数字
    """
    if len(password) < 6:
        raise ValidationError('密码长度至少为6位')
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError('密码必须包含大写字母')
    
    if not re.search(r'[a-z]', password):
        raise ValidationError('密码必须包含小写字母')
    
    if not re.search(r'\d', password):
        raise ValidationError('密码必须包含数字')


class User(AbstractUser):
    role_choices = [
        ('user', '普通用户'),
        ('admin', '管理员'),
        ('superuser', '超级管理员'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField('角色', choices=role_choices, default='user', max_length=20)
    avatar = models.URLField('头像', max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active_at = models.DateTimeField('最后活跃时间', default=timezone.now)

    # 添加 related_name 来解决冲突
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='oauth_user_set',
        related_query_name='oauth_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='oauth_user_set',
        related_query_name='oauth_user'
    )

    def save(self, *args, **kwargs):
        if self._state.adding and self.password:  # 只在创建新用户时验证密码
            validate_password_strength(self.password)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username + ' - ' + self.role


class WeComConfig(models.Model):
    """企业微信配置"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    corp_id = models.CharField('企业ID', max_length=100)
    agent_id = models.CharField('应用ID', max_length=100)
    secret = models.CharField('应用密钥', max_length=100)
    redirect_uri = models.URLField('回调域名', max_length=500, null=True, blank=True)
    enabled = models.BooleanField('是否启用', default=True)
    sync_enabled = models.BooleanField('是否同步', default=True)
    fetch_users = models.BooleanField('是否获取用户列表', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '企业微信配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'企业微信配置 - {self.corp_id}'


class FeiShuConfig(models.Model):
    """飞书配置"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app_id = models.CharField('应用ID', max_length=100)
    app_secret = models.CharField('应用密钥', max_length=100)
    redirect_uri = models.URLField('回调域名', max_length=500, null=True, blank=True)
    enabled = models.BooleanField('是否启用', default=True)
    sync_enabled = models.BooleanField('是否同步', default=True)
    fetch_users = models.BooleanField('是否获取用户列表', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '飞书配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'飞书配置 - {self.app_id}'


class DingTalkConfig(models.Model):
    """钉钉配置"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.CharField('Client ID', max_length=100)
    client_secret = models.CharField('Client Secret', max_length=100)
    app_id = models.CharField('APP ID', max_length=100)
    redirect_uri = models.URLField('回调域名', max_length=500, null=True, blank=True)
    enabled = models.BooleanField('是否启用', default=True)
    sync_enabled = models.BooleanField('是否同步', default=True)
    fetch_users = models.BooleanField('是否获取用户列表', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '钉钉配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'钉钉配置 - {self.client_id}'


class WeComUser(models.Model):
    """企业微信用户"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wecom_info', null=True, blank=True)
    wecom_user_id = models.CharField('企业微信用户ID', max_length=100)
    name = models.CharField('姓名', max_length=50, null=True, blank=True)
    avatar = models.URLField('头像', max_length=500, null=True, blank=True)
    qr_code = models.URLField('二维码', max_length=500, null=True, blank=True)
    mobile = models.CharField('手机号', max_length=20, null=True, blank=True)
    email = models.EmailField('邮箱', max_length=100, null=True, blank=True)
    address = models.CharField('地址', max_length=200, null=True, blank=True)
    position = models.CharField('职位', max_length=100, null=True, blank=True)
    gender = models.CharField('性别', max_length=10, choices=[
        ('male', '男'),
        ('female', '女'),
        ('unknown', '未知')
    ], default='unknown')
    department = models.CharField('部门', max_length=100, null=True, blank=True)
    status = models.CharField('状态', max_length=20, choices=[
        ('active', '在职'),
        ('inactive', '离职'),
        ('pending', '待确认')
    ], default='pending')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '企业微信用户'
        verbose_name_plural = verbose_name
        unique_together = [('wecom_user_id',)]

    def __str__(self):
        return f'企业微信用户 - {self.name or self.user.username}'


class FeiShuUser(models.Model):
    """飞书用户"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feishu_info', null=True, blank=True)
    open_id = models.CharField('飞书用户ID', max_length=100)
    union_id = models.CharField('统一ID', max_length=100, null=True, blank=True)
    name = models.CharField('姓名', max_length=50, null=True, blank=True)
    avatar = models.URLField('头像', max_length=500, null=True, blank=True)
    mobile = models.CharField('手机号', max_length=20, null=True, blank=True)
    email = models.EmailField('邮箱', max_length=100, null=True, blank=True)
    tenant_key = models.CharField('企业标识', max_length=100, null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '飞书用户'
        verbose_name_plural = verbose_name
        unique_together = [('open_id',)]

    def __str__(self):
        return f'飞书用户 - {self.name or self.user.username}'


class DingTalkUser(models.Model):
    """钉钉用户"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dingtalk_info', null=True, blank=True)
    open_id = models.CharField('钉钉用户ID', max_length=100)
    union_id = models.CharField('统一ID', max_length=100, null=True, blank=True)
    name = models.CharField('姓名', max_length=50, null=True, blank=True)
    avatar = models.URLField('头像', max_length=500, null=True, blank=True)
    mobile = models.CharField('手机号', max_length=20, null=True, blank=True)
    email = models.EmailField('邮箱', max_length=100, null=True, blank=True)
    position = models.CharField('职位', max_length=100, null=True, blank=True)
    gender = models.CharField('性别', max_length=10, choices=[
        ('male', '男'),
        ('female', '女'),
        ('unknown', '未知')
    ], default='unknown')
    department = models.CharField('部门', max_length=100, null=True, blank=True)
    job_number = models.CharField('工号', max_length=100, null=True, blank=True)
    status = models.CharField('状态', max_length=20, choices=[
        ('active', '在职'),
        ('inactive', '离职'),
        ('pending', '待确认')
    ], default='pending')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '钉钉用户'
        verbose_name_plural = verbose_name
        unique_together = [('open_id',)]

    def __str__(self):
        return f'钉钉用户 - {self.name or self.user.username}'


class GitHubConfig(models.Model):
    """GitHub OAuth配置"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.CharField('Client ID', max_length=100)
    client_secret = models.CharField('Client Secret', max_length=100)
    redirect_uri = models.URLField('回调域名', max_length=500, null=True, blank=True)
    enabled = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = 'GitHub配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'GitHub配置 - {self.client_id}'


class GitHubUser(models.Model):
    """GitHub用户信息"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='github_user',
        verbose_name='关联用户',
        null=True, blank=True
    )
    github_id = models.CharField('GitHub ID', max_length=100, unique=True)
    login = models.CharField('GitHub用户名', max_length=100)
    name = models.CharField('GitHub昵称', max_length=100, null=True, blank=True)
    email = models.EmailField('GitHub邮箱', null=True, blank=True)
    avatar_url = models.URLField('头像URL', null=True, blank=True)
    bio = models.TextField('个人简介', null=True, blank=True)
    location = models.CharField('所在地', max_length=100, null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = 'GitHub用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'GitHub用户 - {self.name or self.login}'


class OAuthConfig(models.Model):
    provider = models.CharField(max_length=50)  # 'google', 'dingtalk', 'feishu', 'wechat'
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    redirect_uri = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('provider',)

    def __str__(self):
        return f"{self.provider} OAuth Config"


class GoogleConfig(models.Model):
    """Google OAuth配置"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.CharField('Client ID', max_length=100)
    client_secret = models.CharField('Client Secret', max_length=100)
    redirect_uri = models.URLField('回调域名', max_length=500, null=True, blank=True)
    enabled = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = 'Google配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'Google配置 - {self.client_id}'


class GoogleUser(models.Model):
    """Google用户信息"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='google_user',
        verbose_name='关联用户',
        null=True, blank=True
    )
    google_id = models.CharField('Google ID', max_length=100, unique=True)
    email = models.EmailField('邮箱', max_length=100, null=True, blank=True)
    name = models.CharField('姓名', max_length=100, null=True, blank=True)
    given_name = models.CharField('名', max_length=100, null=True, blank=True)
    family_name = models.CharField('姓', max_length=100, null=True, blank=True)
    picture = models.URLField('头像URL', null=True, blank=True)
    locale = models.CharField('语言', max_length=10, null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = 'Google用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'Google用户 - {self.name or self.email}'


class GitLabConfig(models.Model):
    """GitLab 配置"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.CharField(max_length=255, verbose_name='Client ID')
    client_secret = models.CharField(max_length=255, verbose_name='Client Secret')
    redirect_uri = models.CharField(max_length=255, verbose_name='重定向URI', blank=True)
    gitlab_server = models.CharField(max_length=255, verbose_name='GitLab 服务器地址', default='https://gitlab.com')
    enabled = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'GitLab 配置'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'GitLab 配置 {self.id}'


class GitLabUser(models.Model):
    """GitLab用户信息"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='gitlab_user',
        verbose_name='关联用户',
        null=True, blank=True
    )
    gitlab_id = models.CharField('GitLab ID', max_length=100, unique=True)
    username = models.CharField('用户名', max_length=100)
    email = models.EmailField('邮箱', max_length=100, null=True, blank=True)
    name = models.CharField('姓名', max_length=100, null=True, blank=True)
    avatar_url = models.URLField('头像URL', null=True, blank=True)
    web_url = models.URLField('个人主页', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = 'GitLab用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'GitLab用户 - {self.name or self.username}'


class GiteeConfig(models.Model):
    """Gitee 配置"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.CharField(max_length=255, verbose_name='Client ID')
    client_secret = models.CharField(max_length=255, verbose_name='Client Secret')
    redirect_uri = models.CharField(max_length=255, verbose_name='重定向URI', blank=True)
    enabled = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'Gitee 配置'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'Gitee 配置 {self.id}'


class GiteeUser(models.Model):
    """Gitee 用户"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='gitee_user')
    gitee_id = models.CharField(max_length=50, unique=True, verbose_name='Gitee ID')
    name = models.CharField(max_length=100, blank=True, verbose_name='姓名')
    username = models.CharField(max_length=100, blank=True, verbose_name='用户名')
    email = models.EmailField(null=True, blank=True, verbose_name='邮箱')
    avatar_url = models.URLField(blank=True, verbose_name='头像')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'Gitee 用户'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'Gitee 用户 {self.gitee_id} - {self.name}'
