from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from .serializers import UserSerializer, LoginSerializer, GroupSerializer, WeComConfigSerializer, FeiShuConfigSerializer, DingTalkConfigSerializer, GitHubConfigSerializer, GoogleConfigSerializer, GitLabConfigSerializer, GiteeConfigSerializer
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from .models import User, WeComConfig, FeiShuConfig, DingTalkConfig, GitHubConfig, GoogleConfig, GitLabConfig, GiteeConfig, WeComUser, FeiShuUser, DingTalkUser, GitHubUser, GoogleUser, GitLabUser, GiteeUser
from django.contrib.auth.models import Group
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
import requests as http_requests
import json

User = get_user_model()

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email'
]

class LoginView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            # 验证用户
            user = authenticate(request, username=username, password=password)
            
            if not user:
                return Response({
                    'message': '用户名或密码错误'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
            if not user.is_active:
                return Response({
                    'message': '用户已被禁用'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # 更新最后登录时间
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # 生成 JWT token
            refresh = RefreshToken.for_user(user)
            
            # 准备用户数据
            user_data = UserSerializer(user).data
            
            # 返回登录成功的响应
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_data
            })
            
        except Exception as e:
            return Response({
                'message': '服务器错误',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_stats(request):
    try:
        today = timezone.now().date()
        active_users = User.objects.filter(
            last_active_at__date=today
        ).count()
        
        total_users = User.objects.count()
        
        return Response({
            'active_users': active_users,
            'total_users': total_users
        })
    except Exception as e:
        return Response({
            'message': '获取统计数据失败',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except Exception as e:
            return Response({
                'message': '获取用户信息失败',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserViewSet(viewsets.ModelViewSet):
    """
    用户管理视图集
    """
    queryset = User.objects.filter(is_superuser=False).order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    
    def check_admin(self):
        """检查当前用户是否是管理员"""
        if not self.request.user.role == 'admin' and not self.request.user.role == 'superuser':
            raise PermissionDenied("只有管理员可以执行此操作")
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        # 保存用户
        user = serializer.save()

        # 更新用户时加密密码
        password = serializer.validated_data.get('password')
        if password:
            user.set_password(password)
    
    def perform_update(self, serializer):
        # 先保存一份请求数据的副本
        note_ids = None
        group_ids = None
        if 'note' in self.request.data or 'note_group' in self.request.data:
            self.check_admin()
            note_ids = self.request.data.get('note', [])
            group_ids = self.request.data.get('note_group', [])

        # 如果请求包含笔记或分组授权数据，检查管理员权限
        if 'note' in self.request.data or 'note_group' in self.request.data:
            self.check_admin()
            
        # 获取请求数据中的笔记和分组ID列表
        note_ids = self.request.data.get('note', [])
        group_ids = self.request.data.get('note_group', [])
            
        # 保存用户基本信息
        user = serializer.save()

        # 更新用户时加密密码
        password = serializer.validated_data.get('password')
        if password:
            user.set_password(password)
        
        # 更新笔记授权关系
        if note_ids is not None:
            user.note.clear()
            if note_ids:
                user.note.add(*note_ids)
        
        # 更新分组授权关系
        if group_ids is not None:
            user.note_group.clear()
            if group_ids:
                user.note_group.add(*group_ids)
        
        return user

class GroupViewSet(viewsets.ModelViewSet):
    """
    用户组管理视图集
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class WeComConfigViewSet(viewsets.ModelViewSet):
    queryset = WeComConfig.objects.all()
    serializer_class = WeComConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role in ['admin', 'superuser']:
            raise PermissionDenied("只有管理员可以管理配置")
        return super().get_queryset()

    @action(detail=False, methods=['get'])
    def current(self):
        """获取当前启用的配置"""
        config = WeComConfig.objects.filter(enabled=True).first()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response(None)


class FeiShuConfigViewSet(viewsets.ModelViewSet):
    queryset = FeiShuConfig.objects.all()
    serializer_class = FeiShuConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role in ['admin', 'superuser']:
            raise PermissionDenied("只有管理员可以管理配置")
        return super().get_queryset()

    @action(detail=False, methods=['get'])
    def current(self):
        """获取当前启用的配置"""
        config = FeiShuConfig.objects.filter(enabled=True).first()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response(None)


class DingTalkConfigViewSet(viewsets.ModelViewSet):
    queryset = DingTalkConfig.objects.all()
    serializer_class = DingTalkConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role in ['admin', 'superuser']:
            raise PermissionDenied("只有管理员可以管理配置")
        return super().get_queryset()

    @action(detail=False, methods=['get'])
    def current(self):
        """获取当前启用的配置"""
        config = DingTalkConfig.objects.filter(enabled=True).first()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response(None)


class GitHubConfigViewSet(viewsets.ModelViewSet):
    queryset = GitHubConfig.objects.all()
    serializer_class = GitHubConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role in ['admin', 'superuser']:
            raise PermissionDenied("只有管理员可以管理配置")
        return super().get_queryset()

    @action(detail=False, methods=['get'])
    def current(self):
        """获取当前启用的配置"""
        config = GitHubConfig.objects.filter(enabled=True).first()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response(None)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """健康检查接口"""
    return Response("ok", status=status.HTTP_200_OK)


class GoogleConfigViewSet(viewsets.ModelViewSet):
    queryset = GoogleConfig.objects.all()
    serializer_class = GoogleConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role in ['admin', 'superuser']:
            raise PermissionDenied("只有管理员可以管理配置")
        return super().get_queryset()

    @action(detail=False, methods=['get'])
    def current(self):
        """获取当前启用的配置"""
        config = GoogleConfig.objects.filter(enabled=True).first()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response(None)


class GitLabConfigViewSet(viewsets.ModelViewSet):
    queryset = GitLabConfig.objects.all()
    serializer_class = GitLabConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role in ['admin', 'superuser']:
            raise PermissionDenied("只有管理员可以管理配置")
        return super().get_queryset()

    @action(detail=False, methods=['get'])
    def current(self):
        """获取当前启用的配置"""
        config = GitLabConfig.objects.filter(enabled=True).first()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response(None)

class GiteeConfigViewSet(viewsets.ModelViewSet):
    queryset = GiteeConfig.objects.all()
    serializer_class = GiteeConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role in ['admin', 'superuser']:
            raise PermissionDenied("只有管理员可以管理配置")
        return super().get_queryset()

    @action(detail=False, methods=['get'])
    def current(self):
        """获取当前启用的配置"""
        config = GiteeConfig.objects.filter(enabled=True).first()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response(None)

# 新增第三方用户API视图
class WeComUserViewSet(viewsets.ReadOnlyModelViewSet):
    """企业微信用户视图集"""
    queryset = WeComUser.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'name': user.name,
                'username': user.wecom_user_id,
                'email': user.email,
                'mobile': user.mobile,
                'department': user.department,
                'position': user.position,
                'avatar': user.avatar,
                'wecom_userid': user.wecom_user_id,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'linked': user.user is not None,
                'user_id': user.user.id if user.user else None
            }
            data.append(user_data)
        return Response(data)


class FeiShuUserViewSet(viewsets.ReadOnlyModelViewSet):
    """飞书用户视图集"""
    queryset = FeiShuUser.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'name': user.name,
                'username': user.open_id,
                'email': user.email,
                'mobile': user.mobile,
                'avatar': user.avatar,
                'feishu_userid': user.open_id,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'linked': user.user is not None,
                'user_id': user.user.id if user.user else None
            }
            data.append(user_data)
        return Response(data)


class DingTalkUserViewSet(viewsets.ReadOnlyModelViewSet):
    """钉钉用户视图集"""
    queryset = DingTalkUser.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'name': user.name,
                'username': user.open_id,
                'email': user.email,
                'mobile': user.mobile,
                'department': user.department,
                'position': user.position,
                'avatar': user.avatar,
                'dingtalk_userid': user.open_id,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'linked': user.user is not None,
                'user_id': user.user.id if user.user else None
            }
            data.append(user_data)
        return Response(data)


class GitHubUserViewSet(viewsets.ReadOnlyModelViewSet):
    """GitHub用户视图集"""
    queryset = GitHubUser.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'name': user.name,
                'username': user.login,
                'email': user.email,
                'avatar_url': user.avatar_url,
                'github_id': user.github_id,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'linked': user.user is not None,
                'user_id': user.user.id if user.user else None
            }
            data.append(user_data)
        return Response(data)


class GoogleUserViewSet(viewsets.ReadOnlyModelViewSet):
    """Google用户视图集"""
    queryset = GoogleUser.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'name': user.name,
                'username': user.email,
                'email': user.email,
                'avatar_url': user.picture,
                'google_id': user.google_id,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'linked': user.user is not None,
                'user_id': user.user.id if user.user else None
            }
            data.append(user_data)
        return Response(data)


class GitLabUserViewSet(viewsets.ReadOnlyModelViewSet):
    """GitLab用户视图集"""
    queryset = GitLabUser.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'name': user.name,
                'username': user.username,
                'email': user.email,
                'avatar_url': user.avatar_url,
                'gitlab_id': user.gitlab_id,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'linked': user.user is not None,
                'user_id': user.user.id if user.user else None
            }
            data.append(user_data)
        return Response(data)


class GiteeUserViewSet(viewsets.ReadOnlyModelViewSet):
    """Gitee用户视图集"""
    queryset = GiteeUser.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'name': user.name,
                'username': user.username,
                'email': user.email,
                'avatar_url': user.avatar_url,
                'gitee_id': user.gitee_id,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'linked': user.user is not None,
                'user_id': user.user.id if user.user else None
            }
            data.append(user_data)
        return Response(data)

# 用户链接和解除链接API
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def link_user(request):
    """关联本地用户与第三方用户"""
    # 支持两种参数命名方式
    local_user_id = request.data.get('local_user_id') or request.data.get('localUserId')
    third_party_user_id = request.data.get('third_party_user_id') or request.data.get('thirdPartyUserId')
    third_party_type = request.data.get('third_party_type') or request.data.get('thirdPartyType')
    
    if not all([local_user_id, third_party_user_id, third_party_type]):
        return Response({'error': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 检查本地用户是否存在
        local_user = User.objects.get(id=local_user_id)
        
        # 检查本地用户是否已关联其他第三方账号
        is_linked = False
        error_message = ''
        
        # 检查各个平台是否已关联该本地用户
        if WeComUser.objects.filter(user_id=local_user_id).exists():
            is_linked = True
            error_message = '该本地用户已关联企业微信账号'
        elif FeiShuUser.objects.filter(user_id=local_user_id).exists():
            is_linked = True
            error_message = '该本地用户已关联飞书账号'
        elif DingTalkUser.objects.filter(user_id=local_user_id).exists():
            is_linked = True
            error_message = '该本地用户已关联钉钉账号'
        elif GitHubUser.objects.filter(user_id=local_user_id).exists():
            is_linked = True
            error_message = '该本地用户已关联GitHub账号'
        elif GoogleUser.objects.filter(user_id=local_user_id).exists():
            is_linked = True
            error_message = '该本地用户已关联Google账号'
        elif GitLabUser.objects.filter(user_id=local_user_id).exists():
            is_linked = True
            error_message = '该本地用户已关联GitLab账号'
        elif GiteeUser.objects.filter(user_id=local_user_id).exists():
            is_linked = True
            error_message = '该本地用户已关联Gitee账号'
        
        # 如果用户已被关联，返回错误
        if is_linked:
            return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取第三方用户并进行关联
        if third_party_type == 'wecom':
            third_party_user = WeComUser.objects.get(id=third_party_user_id)
            # 先检查该第三方用户是否已关联其他本地用户
            if third_party_user.user_id and third_party_user.user_id != local_user_id:
                # 更新关联关系
                third_party_user.user_id = local_user_id
                third_party_user.save()
            else:
                third_party_user.user_id = local_user_id
                third_party_user.save()
        elif third_party_type == 'feishu':
            third_party_user = FeiShuUser.objects.get(id=third_party_user_id)
            third_party_user.user_id = local_user_id
            third_party_user.save()
        elif third_party_type == 'dingtalk':
            third_party_user = DingTalkUser.objects.get(id=third_party_user_id)
            third_party_user.user_id = local_user_id
            third_party_user.save()
        elif third_party_type == 'github':
            third_party_user = GitHubUser.objects.get(id=third_party_user_id)
            third_party_user.user_id = local_user_id
            third_party_user.save()
        elif third_party_type == 'google':
            third_party_user = GoogleUser.objects.get(id=third_party_user_id)
            third_party_user.user_id = local_user_id
            third_party_user.save()
        elif third_party_type == 'gitlab':
            third_party_user = GitLabUser.objects.get(id=third_party_user_id)
            third_party_user.user_id = local_user_id
            third_party_user.save()
        elif third_party_type == 'gitee':
            third_party_user = GiteeUser.objects.get(id=third_party_user_id)
            third_party_user.user_id = local_user_id
            third_party_user.save()
        
        return Response({'message': '关联成功'})
    except User.DoesNotExist:
        return Response({'error': '本地用户不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'关联失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def unlink_user(request, user_id):
    """解除本地用户与第三方用户的关联"""
    try:
        user = User.objects.get(id=user_id)
        third_party_type = request.data.get('third_party_type')
        
        if not third_party_type:
            return Response({'message': '缺少必要的参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        if third_party_type == 'wecom':
            try:
                third_party_user = WeComUser.objects.get(user=user)
                third_party_user.user = None
                third_party_user.save()
            except WeComUser.DoesNotExist:
                return Response({'message': '该用户未关联企业微信用户'}, status=status.HTTP_400_BAD_REQUEST)
        elif third_party_type == 'feishu':
            try:
                third_party_user = FeiShuUser.objects.get(user=user)
                third_party_user.user = None
                third_party_user.save()
            except FeiShuUser.DoesNotExist:
                return Response({'message': '该用户未关联飞书用户'}, status=status.HTTP_400_BAD_REQUEST)
        elif third_party_type == 'dingtalk':
            try:
                third_party_user = DingTalkUser.objects.get(user=user)
                third_party_user.user = None
                third_party_user.save()
            except DingTalkUser.DoesNotExist:
                return Response({'message': '该用户未关联钉钉用户'}, status=status.HTTP_400_BAD_REQUEST)
        elif third_party_type == 'github':
            try:
                third_party_user = GitHubUser.objects.get(user=user)
                third_party_user.user = None
                third_party_user.save()
            except GitHubUser.DoesNotExist:
                return Response({'message': '该用户未关联GitHub用户'}, status=status.HTTP_400_BAD_REQUEST)
        elif third_party_type == 'google':
            try:
                third_party_user = GoogleUser.objects.get(user=user)
                third_party_user.user = None
                third_party_user.save()
            except GoogleUser.DoesNotExist:
                return Response({'message': '该用户未关联Google用户'}, status=status.HTTP_400_BAD_REQUEST)
        elif third_party_type == 'gitlab':
            try:
                third_party_user = GitLabUser.objects.get(user=user)
                third_party_user.user = None
                third_party_user.save()
            except GitLabUser.DoesNotExist:
                return Response({'message': '该用户未关联GitLab用户'}, status=status.HTTP_400_BAD_REQUEST)
        elif third_party_type == 'gitee':
            try:
                third_party_user = GiteeUser.objects.get(user=user)
                third_party_user.user = None
                third_party_user.save()
            except GiteeUser.DoesNotExist:
                return Response({'message': '该用户未关联Gitee用户'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': '不支持的第三方类型'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': '解除关联成功'})
    except User.DoesNotExist:
        return Response({'message': '本地用户不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': '解除关联失败', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
