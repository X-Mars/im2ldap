<template>
  <el-card class="sync-status-widget">
    <template #header>
      <div class="widget-header">
        <span>同步状态</span>
        <el-button 
          type="primary" 
          size="small" 
          @click="loadData" 
          :icon="Refresh"
          :loading="loading"
        >
          刷新
        </el-button>
      </div>
    </template>
    
    <div class="widget-content" v-loading="loading">
      <div v-if="syncConfigs.length === 0" class="empty-data">
        <el-empty description="暂无同步配置" />
        <el-button 
          type="primary" 
          @click="goToSyncConfig" 
          size="small" 
          class="add-config-btn"
        >
          添加配置
        </el-button>
      </div>
      
      <template v-else>
        <div 
          v-for="config in syncConfigs" 
          :key="config.id" 
          class="sync-item"
        >
          <div class="sync-info">
            <div class="sync-name">
              <el-tag 
                :type="getSyncTypeTag(config.sync_type)" 
                size="small"
                class="tag-margin"
              >
                {{ getSyncTypeName(config.sync_type) }}
              </el-tag>
              {{ config.name }}
            </div>
            <div class="sync-time">
              最后同步: 
              <span v-if="config.last_sync_time">
                {{ formatDateTime(config.last_sync_time) }}
              </span>
              <span v-else>--</span>
            </div>
          </div>
          
          <div class="sync-action">
            <el-button 
              type="primary" 
              size="small" 
              @click="handleSyncNow(config)"
              :loading="syncingId === config.id"
              :icon="Refresh"
            >
              同步
            </el-button>
          </div>
        </div>
      </template>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { syncConfigApi } from '@/api/sync'
import type { SyncConfig } from '@/api/types'

const router = useRouter()
const syncConfigs = ref<SyncConfig[]>([])
const loading = ref(false)
const syncingId = ref('')

// 获取同步类型名称
const getSyncTypeName = (type: string) => {
  const typeMap: Record<string, string> = {
    'wecom': '企业微信',
    'feishu': '飞书',
    'dingtalk': '钉钉'
  }
  return typeMap[type] || type
}

// 获取同步类型标签样式
const getSyncTypeTag = (type: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' | '' => {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    'wecom': 'primary',
    'feishu': 'success',
    'dingtalk': 'warning'
  }
  return typeMap[type] || ''
}

// 格式化日期时间
const formatDateTime = (datetime: string) => {
  return dayjs(datetime).format('YYYY-MM-DD HH:mm:ss')
}

// 加载同步配置数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await syncConfigApi.getConfigs()
    syncConfigs.value = res.data.filter(config => config.enabled)
  } catch (error) {
    console.error('加载同步配置失败:', error)
    ElMessage.error('加载同步配置失败')
  } finally {
    loading.value = false
  }
}

// 立即同步
const handleSyncNow = async (config: SyncConfig) => {
  syncingId.value = config.id
  try {
    const res = await syncConfigApi.syncNow(config.id)
    ElMessage.success(res.data.message || '同步成功')
    
    // 刷新数据
    loadData()
  } catch (error: any) {
    console.error('同步失败:', error)
    ElMessage.error(error.response?.data?.message || '同步失败')
  } finally {
    syncingId.value = ''
  }
}

// 跳转到同步配置页面
const goToSyncConfig = () => {
  router.push('/sync/configs')
}

// 初始加载
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.sync-status-widget {
  height: 100%;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.widget-content {
  min-height: 200px;
}

.empty-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.add-config-btn {
  margin-top: 15px;
}

.sync-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.sync-item:last-child {
  border-bottom: none;
}

.sync-name {
  font-weight: 500;
  margin-bottom: 5px;
}

.sync-time {
  font-size: 12px;
  color: #909399;
}

.tag-margin {
  margin-right: 5px;
}
</style> 