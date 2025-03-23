from django.apps import AppConfig

class SyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sync'
    verbose_name = "同步管理"
    
    def ready(self):
        # 导入信号处理器
        import sync.signals
        
        # 启动调度器
        from sync.sync_scheduler import scheduler
        # 注意：scheduler中没有initialize方法，直接使用start
        scheduler.start() 