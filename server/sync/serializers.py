from rest_framework import serializers
from .models import LDAPConfig, SyncConfig, SyncLog, SyncLogDetail

class LDAPConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = LDAPConfig
        fields = ('id', 'server_uri', 'bind_dn', 'bind_password', 'base_dn', 'use_ssl', 'enabled', 'sync_interval', 'created_at', 'updated_at')
        extra_kwargs = {
            'bind_password': {'write_only': True}
        }
    
    def to_representation(self, instance):
        # 不返回密码
        data = super().to_representation(instance)
        if 'bind_password' in data:
            del data['bind_password']
        return data

class SyncLogDetailSerializer(serializers.ModelSerializer):
    """同步日志详情序列化器"""
    object_type_display = serializers.CharField(source='get_object_type_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = SyncLogDetail
        fields = ['id', 'object_type', 'object_type_display', 'action', 'action_display', 
                  'object_id', 'object_name', 'old_data', 'new_data', 'details']

class SyncLogSerializer(serializers.ModelSerializer):
    """同步日志序列化器"""
    details = serializers.SerializerMethodField()
    
    class Meta:
        model = SyncLog
        fields = ['id', 'config', 'sync_time', 'success', 
                 'users_synced', 'departments_synced', 'details']
    
    def get_details(self, obj):
        # 获取已筛选的详情数据
        details = getattr(obj, 'filtered_details', obj.details.all())
        return SyncLogDetailSerializer(details, many=True).data

class SyncConfigSerializer(serializers.ModelSerializer):
    ldap_config_details = LDAPConfigSerializer(source='ldap_config', read_only=True)
    logs = SyncLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = SyncConfig
        fields = ('id', 'name', 'sync_type', 'ldap_config', 'ldap_config_details', 'sync_users', 
                 'sync_departments', 'user_ou', 'department_ou', 'sync_interval',
                 'last_sync_time', 'enabled', 'created_at', 'updated_at', 'logs')
        read_only_fields = ('last_sync_time', 'created_at', 'updated_at')