import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SyncConfig, LDAPConfig
from .sync_scheduler import scheduler

logger = logging.getLogger(__name__)

# 在配置更新时刷新调度
@receiver(post_save, sender=SyncConfig)
def handle_sync_config_save(sender, instance, **kwargs):
    """当同步配置保存时，更新调度器"""
    logger.info(f"同步配置已更新: {instance.name}, 刷新调度")
    scheduler.refresh_schedule()

@receiver(post_delete, sender=SyncConfig)
def handle_sync_config_delete(sender, instance, **kwargs):
    """当同步配置删除时，更新调度器"""
    logger.info(f"同步配置已删除: {instance.name}, 刷新调度")
    scheduler.refresh_schedule()

# 在LDAP配置更新时检查对应的同步配置是否需要更新
@receiver(post_save, sender=LDAPConfig)
def handle_ldap_config_save(sender, instance, **kwargs):
    """当LDAP配置更新时，可能需要更新调度器"""
    # 如果LDAP配置被禁用，可能需要禁用依赖它的同步任务
    if not instance.enabled:
        affected_configs = SyncConfig.objects.filter(ldap_config=instance, enabled=True)
        for config in affected_configs:
            logger.info(f"LDAP配置 {instance.server_uri} 已禁用，同步配置 {config.name} 将受影响")
    
    # 刷新调度器以确保所有任务都是最新的
    scheduler.refresh_schedule() 