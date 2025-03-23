from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, UserInfoView, UserViewSet, GroupViewSet,
    WeComConfigViewSet, FeiShuConfigViewSet, DingTalkConfigViewSet,
    GitHubConfigViewSet, GoogleConfigViewSet, GitLabConfigViewSet,
    GiteeConfigViewSet, health_check,
    WeComUserViewSet, FeiShuUserViewSet, DingTalkUserViewSet,
    GitHubUserViewSet, GoogleUserViewSet, GitLabUserViewSet, GiteeUserViewSet,
    link_user, unlink_user
)
from .utils import WeComLoginView, FeiShuLoginView, DingTalkLoginView, LoginQRCodeView, GitHubLoginView
from .utils.google import GoogleLoginView
from .utils.gitlab import GitLabLoginView
from .utils.gitee import GiteeLoginView
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'wecom-config', WeComConfigViewSet)
router.register(r'feishu-config', FeiShuConfigViewSet)
router.register(r'dingtalk-config', DingTalkConfigViewSet)
router.register(r'github-config', GitHubConfigViewSet)
router.register(r'google-config', GoogleConfigViewSet)
router.register(r'gitlab-config', GitLabConfigViewSet)
router.register(r'gitee-config', GiteeConfigViewSet)
router.register(r'wecom-users', WeComUserViewSet)
router.register(r'feishu-users', FeiShuUserViewSet)
router.register(r'dingtalk-users', DingTalkUserViewSet)
router.register(r'github-users', GitHubUserViewSet)
router.register(r'google-users', GoogleUserViewSet)
router.register(r'gitlab-users', GitLabUserViewSet)
router.register(r'gitee-users', GiteeUserViewSet)

urlpatterns = [
    # 包含路由器生成的URL
    path('', include(router.urls)),
    
    # 其他URL保持不变
    path('login/', LoginView.as_view(), name='login'),
    path('wecom/login/', WeComLoginView.as_view(), name='wecom_login'),
    path('feishu/login/', FeiShuLoginView.as_view(), name='feishu_login'),
    path('dingtalk/login/', DingTalkLoginView.as_view(), name='dingtalk_login'),
    path('github/login/', GitHubLoginView.as_view(), name='github_login'),
    path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('gitlab/login/', GitLabLoginView.as_view(), name='gitlab_login'),
    path('gitee/login/', GiteeLoginView.as_view(), name='gitee_login'),
    path('login/qrcode/', LoginQRCodeView.as_view(), name='login_qrcode'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserInfoView.as_view(), name='user_info'),
    path('stats/', views.get_stats, name='user-stats'),
    path('health/', health_check, name='health_check'),
    
    # 用户链接相关API
    path('users/<str:user_id>/link/', link_user, name='link_user'),
    path('users/<str:user_id>/unlink/', unlink_user, name='unlink_user'),
]
