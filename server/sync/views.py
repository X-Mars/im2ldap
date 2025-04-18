from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
import random
from django.db.models import Count, Prefetch
from django.db.models.functions import TruncDay, TruncMonth
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters

from .models import LDAPConfig, SyncConfig, SyncLog, SyncLogDetail
from .serializers import LDAPConfigSerializer, SyncConfigSerializer, SyncLogSerializer, SyncLogDetailSerializer
from .sync_service import SyncService
from .sync_scheduler import scheduler
from oAuth.models import WeComUser, FeiShuUser, DingTalkUser, WeComConfig, FeiShuConfig, DingTalkConfig
from .ldap_connector import LDAPConnector

class LDAPConfigViewSet(viewsets.ModelViewSet):
    queryset = LDAPConfig.objects.all().order_by('-updated_at')
    serializer_class = LDAPConfigSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试LDAP连接"""
        
        ldap_config = self.get_object()
        try:
            connector = LDAPConnector(
                server_uri=ldap_config.server_uri,
                bind_dn=ldap_config.bind_dn,
                bind_password=ldap_config.bind_password,
                base_dn=ldap_config.base_dn,
                use_ssl=ldap_config.use_ssl
            )
            success = connector.connect()
            if success:
                connector.close()
                return Response({'message': '连接成功'})
            else:
                return Response({'message': '连接失败'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': f'连接错误: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

class SyncConfigViewSet(viewsets.ModelViewSet):
    queryset = SyncConfig.objects.all().order_by('-updated_at')
    serializer_class = SyncConfigSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def perform_create(self, serializer):
        instance = serializer.save()
        # 如果新创建的配置是启用的，刷新调度
        if instance.enabled:
            scheduler.refresh_schedule()
    
    def perform_update(self, serializer):
        instance = serializer.save()
        # 刷新调度
        scheduler.refresh_schedule()
    
    @action(detail=True, methods=['post'])
    def sync_now(self, request, pk=None):
        """立即执行同步任务"""
        try:
            sync_config = self.get_object()
            if not sync_config:
                return Response({
                    'message': '同步配置不存在'
                }, status=status.HTTP_404_NOT_FOUND)
                
            if not sync_config.enabled:
                return Response({
                    'message': '同步配置未启用'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            log = scheduler.run_sync_now(str(sync_config.id))
            if not log:
                return Response({
                    'message': '同步任务执行失败'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            return Response({
                'message': '同步已完成',
                'success': log.success,
                'users_synced': log.users_synced,
                'departments_synced': log.departments_synced
            })
        except Exception as e:
            return Response({
                'message': f'同步错误: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class SyncLogViewSet(viewsets.ModelViewSet):
    """同步日志视图集"""
    queryset = SyncLog.objects.all().order_by('-sync_time')
    serializer_class = SyncLogSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['config__name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 获取筛选参数
        config_id = self.request.query_params.get('config')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        # 应用筛选
        if config_id:
            queryset = queryset.filter(config_id=config_id)
        
        if start_date:
            queryset = queryset.filter(sync_time__gte=f"{start_date} 00:00:00")
        
        if end_date:
            queryset = queryset.filter(sync_time__lte=f"{end_date} 23:59:59")
        
        # 获取详情筛选参数
        object_type = self.request.query_params.get('object_type')
        action = self.request.query_params.get('action')
        
        # 预加载详情数据并应用筛选
        details_filter = {}
        if object_type:
            details_filter['object_type'] = object_type
        if action:
            details_filter['action'] = action
        
        # 使用Prefetch高效加载关联的详情数据
        queryset = queryset.prefetch_related(
            Prefetch(
                'details',
                queryset=SyncLogDetail.objects.filter(**details_filter).order_by('object_type', 'action', 'object_name'),
                to_attr='filtered_details'
            )
        )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# 用户趋势API视图
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_trend_data(request):
    """获取各平台用户数量的趋势数据"""
    time_range = request.query_params.get('range', 'week')
    
    # 确定日期范围
    today = timezone.now().date()
    if time_range == 'week':
        # 过去7天
        start_date = today - timedelta(days=6)
        date_points = 7
        trunc_function = TruncDay
        date_format = '%m-%d'
    elif time_range == 'month':
        # 过去30天
        start_date = today - timedelta(days=29)
        date_points = 30
        trunc_function = TruncDay
        date_format = '%m-%d'
    elif time_range == 'year':
        # 过去12个月
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=330)
        date_points = 12
        trunc_function = TruncMonth
        date_format = '%Y-%m'
    else:
        return Response({"error": "Invalid time range"}, status=400)
    
    # 生成日期列表
    dates = []
    if time_range == 'year':
        # 按月生成
        current_date = start_date
        while current_date <= today:
            dates.append(current_date.strftime(date_format))
            # 移到下一个月
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    else:
        # 按天生成
        for i in range(date_points):
            date = start_date + timedelta(days=i)
            dates.append(date.strftime(date_format))
    
    # 从数据库获取企业微信用户趋势数据
    wecom_data = {}
    for date_entry in WeComUser.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=today
    ).annotate(
        date=trunc_function('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date'):
        date_key = date_entry['date'].strftime(date_format)
        wecom_data[date_key] = wecom_data.get(date_key, 0) + date_entry['count']
    
    # 从数据库获取飞书用户趋势数据
    feishu_data = {}
    for date_entry in FeiShuUser.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=today
    ).annotate(
        date=trunc_function('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date'):
        date_key = date_entry['date'].strftime(date_format)
        feishu_data[date_key] = feishu_data.get(date_key, 0) + date_entry['count']
    
    # 从数据库获取钉钉用户趋势数据
    dingtalk_data = {}
    for date_entry in DingTalkUser.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=today
    ).annotate(
        date=trunc_function('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date'):
        date_key = date_entry['date'].strftime(date_format)
        dingtalk_data[date_key] = dingtalk_data.get(date_key, 0) + date_entry['count']
    
    # 从同步日志获取LDAP用户趋势数据
    ldap_data = {}
    for date_entry in SyncLog.objects.filter(
        sync_time__date__gte=start_date,
        sync_time__date__lte=today,
        success=True
    ).annotate(
        date=trunc_function('sync_time')
    ).values('date').annotate(
        count=Count('users_synced')
    ).order_by('date'):
        date_key = date_entry['date'].strftime(date_format)
        ldap_data[date_key] = ldap_data.get(date_key, 0) + date_entry['count']
    
    # 转换为每日累计的用户数据
    wecom_users = []
    feishu_users = []
    dingtalk_users = []
    ldap_users = []
    
    # 检查是否启用同步
    wecom_enabled = WeComConfig.objects.filter(enabled=True, sync_enabled=True).exists()
    feishu_enabled = FeiShuConfig.objects.filter(enabled=True, sync_enabled=True).exists()
    dingtalk_enabled = DingTalkConfig.objects.filter(enabled=True, sync_enabled=True).exists()
    
    # 获取总用户数
    total_wecom = WeComUser.objects.count() if wecom_enabled else 0
    total_feishu = FeiShuUser.objects.count() if feishu_enabled else 0
    total_dingtalk = DingTalkUser.objects.count() if dingtalk_enabled else 0
    
    # 获取LDAP总用户数 (获取最新成功的同步日志中的users_synced字段)
    latest_sync = SyncLog.objects.filter(success=True).order_by('-sync_time').first()
    total_ldap = latest_sync.users_synced if latest_sync else 0
    
    # 计算历史数据点
    for date in dates:
        # 计算每个平台每个时间点的用户数
        # 如果没有当天数据，则使用前一天的数据
        if len(wecom_users) > 0:
            wecom_users.append(wecom_users[-1] + wecom_data.get(date, 0))
            feishu_users.append(feishu_users[-1] + feishu_data.get(date, 0))
            dingtalk_users.append(dingtalk_users[-1] + dingtalk_data.get(date, 0))
            ldap_users.append(ldap_users[-1] + ldap_data.get(date, 0))
        else:
            # 第一个数据点，计算start_date之前的累计数据
            prev_wecom = WeComUser.objects.filter(created_at__date__lt=start_date).count()
            prev_feishu = FeiShuUser.objects.filter(created_at__date__lt=start_date).count()
            prev_dingtalk = DingTalkUser.objects.filter(created_at__date__lt=start_date).count()
            prev_ldap = 0  # 这里可能需要根据您的数据模型调整
            
            wecom_users.append(prev_wecom + wecom_data.get(date, 0))
            feishu_users.append(prev_feishu + feishu_data.get(date, 0))
            dingtalk_users.append(prev_dingtalk + dingtalk_data.get(date, 0))
            ldap_users.append(prev_ldap + ldap_data.get(date, 0))
    
    # 确保数据长度一致
    while len(wecom_users) < len(dates):
        wecom_users.append(total_wecom)
    while len(feishu_users) < len(dates):
        feishu_users.append(total_feishu)
    while len(dingtalk_users) < len(dates):
        dingtalk_users.append(total_dingtalk)
    while len(ldap_users) < len(dates):
        ldap_users.append(total_ldap)
    
    # 截取或填充到正确的长度
    wecom_users = wecom_users[:len(dates)]
    feishu_users = feishu_users[:len(dates)]
    dingtalk_users = dingtalk_users[:len(dates)]
    ldap_users = ldap_users[:len(dates)]
    
    return Response({
        "dates": dates,
        "wecom_users": wecom_users,
        "feishu_users": feishu_users,
        "dingtalk_users": dingtalk_users,
        "ldap_users": ldap_users
    }) 

class SyncLogDetailView(APIView):
    """同步日志详情视图"""
    
    def get(self, request, log_id):
        """获取指定同步日志的详情"""
        try:
            sync_log = SyncLog.objects.get(id=log_id)
            details = SyncLogDetail.objects.filter(sync_log=sync_log)
            
            # 可以添加过滤条件
            object_type = request.query_params.get('object_type')
            if object_type:
                details = details.filter(object_type=object_type)
                
            action = request.query_params.get('action')
            if action:
                details = details.filter(action=action)
            
            # 分页
            paginator = PageNumberPagination()
            paginator.page_size = 50
            result_page = paginator.paginate_queryset(details, request)
            serializer = SyncLogDetailSerializer(result_page, many=True)
            
            return paginator.get_paginated_response(serializer.data)
        except SyncLog.DoesNotExist:
            return Response({"error": "日志不存在"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stats(request):
    """获取各平台用户数量统计"""
    
    # 从数据库获取企业微信用户数量
    wecom_users = WeComUser.objects.count()
    
    # 从数据库获取飞书用户数量
    feishu_users = FeiShuUser.objects.count()
    
    # 从数据库获取钉钉用户数量
    dingtalk_users = DingTalkUser.objects.count()
    
    # 从LDAP获取用户数量
    ldap_users = 0
    ldap_config = LDAPConfig.objects.filter(enabled=True).first()
    
    if ldap_config:
        try:
            # 连接LDAP
            ldap_connector = LDAPConnector(
                server_uri=ldap_config.server_uri,
                bind_dn=ldap_config.bind_dn,
                bind_password=ldap_config.bind_password,
                base_dn=ldap_config.base_dn,
                use_ssl=ldap_config.use_ssl
            )
            ldap_connector.connect()
            # 使用更广泛的搜索过滤器，匹配任意用户相关的对象类
            # search_filter = '(|(objectClass=person)(objectClass=inetOrgPerson)(objectClass=organizationalPerson))'
            
            # 或者尝试使用uid属性来识别用户
            search_filter = '(uid=*)'
            attributes = ['uid', 'cn']
            
            entries = ldap_connector.search_entries(
                search_base=ldap_config.base_dn,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=attributes
            )
            
            ldap_users = len(entries) if entries else 0

            # 关闭连接
            ldap_connector.close()
            
            print(f"LDAP用户搜索完成，找到 {ldap_users} 个用户")
        except Exception as e:
            print(f"获取LDAP用户数量出错: {str(e)}")
            # 添加更详细的异常信息打印
            import traceback
            traceback.print_exc()
    
    return Response({
        "wecom_users": wecom_users,
        "feishu_users": feishu_users,
        "dingtalk_users": dingtalk_users,
        "ldap_users": ldap_users
    })