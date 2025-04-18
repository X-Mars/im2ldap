import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SyncConfig, LDAPConfig

logger = logging.getLogger(__name__)

# 在LDAP配置更新时检查对应的同步配置
@receiver(post_save, sender=LDAPConfig)
def handle_ldap_config_save(sender, instance, **kwargs):
    """当LDAP配置更新时，检查受影响的同步配置"""
    # 如果LDAP配置被禁用，记录受影响的同步配置
    if not instance.enabled:
        affected_configs = SyncConfig.objects.filter(ldap_config=instance, enabled=True)
        for config in affected_configs:
            logger.info(f"LDAP配置 {instance.server_uri} 已禁用，同步配置 {config.name} 将受影响")