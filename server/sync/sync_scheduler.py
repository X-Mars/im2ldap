from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone
from datetime import datetime

class SyncScheduler:
    def __init__(self):
        self.jobs = {}
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
    
    def refresh_schedule(self):
        """刷新调度任务"""
        from .models import SyncConfig
        
        # 获取所有启用的同步配置
        configs = SyncConfig.objects.filter(enabled=True)
        
        # 清理已有的任务
        for job_id in list(self.jobs.keys()):
            if job_id not in [str(config.id) for config in configs]:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
        
        # 添加或更新任务
        for config in configs:
            job_id = str(config.id)
            
            # 如果任务已存在且间隔相同，则跳过
            if job_id in self.jobs and self.jobs[job_id] == config.sync_interval:
                continue
            
            # 如果任务已存在但间隔不同，则移除旧任务
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
            
            # 添加新任务
            if config.sync_interval > 0:
                self.scheduler.add_job(
                    self.run_sync_now,
                    trigger=IntervalTrigger(seconds=config.sync_interval),
                    id=job_id,
                    args=[job_id],
                    next_run_time=datetime.now()
                )
                self.jobs[job_id] = config.sync_interval
    
    def run_sync_now(self, config_id):
        """立即执行同步任务"""
        from .sync_service import SyncService
        from .models import SyncConfig, SyncLog
        
        try:
            config = SyncConfig.objects.get(id=config_id)
            if not config.enabled:
                return None
                
            service = SyncService(str(config_id))
            log = service.sync()
            
            # 更新最后同步时间
            config.last_sync_time = timezone.now()
            config.save(update_fields=['last_sync_time'])
            
            return log
        except SyncConfig.DoesNotExist:
            raise ValueError(f'同步配置不存在: {config_id}')
        except Exception as e:
            raise Exception(f'同步任务执行失败: {str(e)}')

scheduler = SyncScheduler()