from django.contrib import admin
from .models import LDAPConfig, SyncConfig, SyncLog, SyncLogDetail

@admin.register(LDAPConfig)
class LDAPConfigAdmin(admin.ModelAdmin):
    list_display = ('server_uri', 'bind_dn', 'base_dn', 'use_ssl', 'enabled', 'updated_at')
    list_filter = ('use_ssl', 'enabled')
    search_fields = ('server_uri', 'bind_dn', 'base_dn')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('连接信息', {
            'fields': ('server_uri', 'bind_dn', 'bind_password', 'base_dn', 'use_ssl')
        }),
        ('状态', {
            'fields': ('enabled', 'created_at', 'updated_at')
        }),
    )

@admin.register(SyncConfig)
class SyncConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'sync_type', 'ldap_config', 'last_sync_time', 'enabled')
    list_filter = ('sync_type', 'enabled', 'sync_users', 'sync_departments')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'last_sync_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'sync_type', 'ldap_config', 'enabled')
        }),
        ('同步设置', {
            'fields': ('sync_interval', 'sync_users', 'sync_departments', 'user_ou', 'department_ou')
        }),
        ('时间信息', {
            'fields': ('last_sync_time', 'created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:  # 编辑模式
            # 防止编辑已有记录时修改某些字段
            readonly_fields.append('sync_type')
        return readonly_fields

class SyncLogDetailInline(admin.TabularInline):
    model = SyncLogDetail
    extra = 0
    readonly_fields = ('object_type', 'action', 'object_id', 'object_name', 'old_data', 'new_data', 'details')
    can_delete = False
    max_num = 0

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('config', 'sync_time', 'success', 'users_synced', 'departments_synced')
    list_filter = ('success', 'sync_time', 'config')
    search_fields = ('config__name',)
    readonly_fields = ('config', 'sync_time', 'success', 'users_synced', 'departments_synced')
    inlines = [SyncLogDetailInline]
    
    def has_add_permission(self, request):
        # 不允许手动添加日志
        return False
    
    def has_change_permission(self, request, obj=None):
        # 不允许修改日志
        return False

@admin.register(SyncLogDetail)
class SyncLogDetailAdmin(admin.ModelAdmin):
    list_display = ('sync_log', 'object_type', 'action', 'object_name')
    list_filter = ('object_type', 'action')
    search_fields = ('object_name', 'details')
    readonly_fields = ('sync_log', 'object_type', 'action', 'object_id', 'object_name', 'old_data', 'new_data', 'details')