import logging
import threading
import time
import schedule
from typing import Dict, Optional
from django.db import connection, ProgrammingError, OperationalError

logger = logging.getLogger(__name__)

class SyncScheduler:
    """同步调度器，管理定时同步任务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SyncScheduler, cls).__new__(cls)
            cls._instance.jobs = {}
            cls._instance.running = False
            cls._instance.thread = None
        return cls._instance
    
    def start(self):
        """启动调度器，安全地检查数据库表是否存在"""
        if self.running:
            return
            
        logger.info("启动同步调度器")
        self.running = True
        
        # 创建守护线程运行调度器
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
        # 在单独的线程中尝试初始化，避免阻塞应用启动
        threading.Thread(target=self._safe_init_scheduler, daemon=True).start()
    
    def _safe_init_scheduler(self):
        """安全地初始化调度器，避免在表不存在时出错"""
        # 等待一段时间，确保数据库迁移有机会完成
        time.sleep(5)
        try:
            # 尝试调度所有任务
            self._schedule_all_sync_tasks()
        except (ProgrammingError, OperationalError) as e:
            logger.warning(f"数据库表尚未准备好，调度器将在表创建后初始化: {str(e)}")
        except Exception as e:
            logger.error(f"初始化调度器出错: {str(e)}")
        
    def stop(self):
        """停止调度器"""
        if not self.running:
            return
            
        logger.info("停止同步调度器")
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
            
    def _run(self):
        """运行调度器循环"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
            
    def _schedule_all_sync_tasks(self):
        """调度所有同步任务"""
        # 导入SyncConfig以避免循环导入
        from .models import SyncConfig
        
        # 清除现有任务
        schedule.clear()
        self.jobs = {}
        
        try:
            # 获取所有启用的同步配置
            sync_configs = SyncConfig.objects.filter(enabled=True)
            
            for config in sync_configs:
                self._schedule_sync_task(config)
                
            logger.info(f"已初始化 {len(sync_configs)} 个同步任务")
        except Exception as e:
            logger.error(f"调度同步任务失败: {str(e)}")
            
    def _schedule_sync_task(self, config):
        """调度单个同步任务"""
        if not config.enabled:
            return
            
        # 如果已经有该配置的任务，先清除
        if str(config.id) in self.jobs:
            schedule.cancel_job(self.jobs[str(config.id)])
            
        # 根据同步频率设置任务
        job = None
        
        if config.sync_frequency == 'hourly':
            job = schedule.every().hour.do(self._run_sync, config_id=str(config.id))
        elif config.sync_frequency == 'daily':
            job = schedule.every().day.at("01:00").do(self._run_sync, config_id=str(config.id))
        elif config.sync_frequency == 'weekly':
            job = schedule.every().monday.at("01:00").do(self._run_sync, config_id=str(config.id))
            
        if job:
            self.jobs[str(config.id)] = job
            logger.info(f"已调度同步任务: {config.name} ({config.sync_frequency})")
            
    def _run_sync(self, config_id: str):
        """执行同步任务"""
        from .sync_service import SyncService
        
        try:
            logger.info(f"开始执行同步任务: {config_id}")
            service = SyncService(config_id)
            log = service.sync()
            logger.info(f"同步任务完成: {config_id}, 结果: {'成功' if log.success else '失败'}")
        except Exception as e:
            logger.error(f"执行同步任务出错: {config_id}, 错误: {str(e)}")
            
    def refresh_schedule(self):
        """刷新所有调度任务"""
        try:
            self._schedule_all_sync_tasks()
        except Exception as e:
            logger.error(f"刷新调度任务失败: {str(e)}")
        
    def run_sync_now(self, config_id: str):
        """立即执行同步任务"""
        from .sync_service import SyncService
        
        try:
            logger.info(f"立即执行同步任务: {config_id}")
            service = SyncService(config_id)
            log = service.sync()
            logger.info(f"同步任务完成: {config_id}, 结果: {'成功' if log.success else '失败'}")
            return log
        except Exception as e:
            logger.error(f"执行同步任务出错: {config_id}, 错误: {str(e)}")
            raise

# 创建调度器单例
scheduler = SyncScheduler() 