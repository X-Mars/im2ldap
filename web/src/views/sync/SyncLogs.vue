<template>
  <div class="sync-logs-container">
    <div class="page-header">
      <h2>同步日志</h2>
      <div class="filter-section">
        <el-select 
          v-model="filter.config" 
          placeholder="选择配置" 
          clearable
          @change="loadData"
          style="width: 150px; margin-right: 10px;"
        >
          <el-option 
            v-for="config in syncConfigs" 
            :key="config.id" 
            :label="config.name" 
            :value="config.id" 
          />
        </el-select>
        
        <el-date-picker
          v-model="filter.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="loadData"
          style="width: 260px; margin-right: 10px;"
        />
        
        <el-select v-model="filter.objectType" placeholder="对象类型" clearable @change="loadData" style="width: 120px; margin-right: 10px;">
          <el-option label="用户" value="user"/>
          <el-option label="部门" value="department"/>
        </el-select>
        
        <el-select v-model="filter.action" placeholder="操作类型" clearable @change="loadData" style="width: 120px; margin-right: 10px;">
          <el-option label="创建" value="create"/>
          <el-option label="更新" value="update"/>
          <el-option label="删除" value="delete"/>
          <el-option label="移动" value="move"/>
        </el-select>
        
        <el-button type="primary" @click="loadData" :icon="Search">
          搜索
        </el-button>
      </div>
    </div>
    
    <div class="list-header">
      <span>同步日志列表</span>
    </div>
    
    <el-table 
      :data="syncLogs" 
      style="width: 100%" 
      v-loading="loading"
    >
      <el-table-column type="expand">
        <template #default="props">
          <div class="expand-container">
            <el-table 
              :data="props.row.details || []" 
              style="width: 100%"
            >
              <el-table-column prop="object_type_display" label="对象类型" />
              <el-table-column prop="action_display" label="操作类型">
                <template #default="scope">
                  <el-tag 
                    :type="getActionTagType(scope.row.action)"
                    effect="plain"
                  >
                    {{ scope.row.action_display }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="object_name" label="对象名称" />
              <el-table-column prop="details" label="详情描述" min-width="200" />
              <el-table-column label="变更内容" min-width="250">
                <template #default="scope">
                  <div v-if="scope.row.old_data || scope.row.new_data" class="change-content">
                    <!-- 创建操作只显示新值 -->
                    <div v-if="scope.row.action === 'create'" class="change-item-container">
                      <div v-for="(value, key) in scope.row.new_data" :key="key" class="change-item">
                        <span class="change-key">{{ key }}:</span>
                        <span class="change-value new-value">{{ value }}</span>
                      </div>
                    </div>
                    
                    <!-- 删除操作只显示旧值 -->
                    <div v-else-if="scope.row.action === 'delete'" class="change-item-container">
                      <div v-for="(value, key) in scope.row.old_data" :key="key" class="change-item">
                        <span class="change-key">{{ key }}:</span>
                        <span class="change-value old-value">{{ value }}</span>
                      </div>
                    </div>
                    
                    <!-- 更新和移动操作显示前后对比 -->
                    <div v-else class="change-item-container">
                      <div v-for="(value, key) in getChangedAttributes(scope.row)" :key="key" class="change-item">
                        <span class="change-key">{{ key }}:</span>
                        <div class="change-comparison">
                          <span class="change-value old-value">{{ value.old || '-' }}</span>
                          <span class="arrow">→</span>
                          <span class="change-value new-value">{{ value.new || '-' }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <span v-else>无变更数据</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column label="配置名称">
        <template #default="scope">
          <span>{{ getConfigName(scope.row.config) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="sync_time" label="同步时间">
        <template #default="scope">
          {{ formatDateTime(scope.row.sync_time) }}
        </template>
      </el-table-column>
      <el-table-column label="同步结果">
        <template #default="scope">
          <el-tag :type="scope.row.success ? 'success' : 'danger'">
            {{ scope.row.success ? '成功' : '失败' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="同步数据">
        <template #default="scope">
          <div>
            用户: {{ scope.row.users_synced }}
          </div>
          <div>
            部门: {{ scope.row.departments_synced }}
          </div>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="page.current"
        v-model:page-size="page.size"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="page.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { syncLogApi, syncConfigApi } from '@/api/sync'
import type { SyncLog, SyncConfig } from '@/api/types'

// 数据列表
const syncLogs = ref<any[]>([])
const syncConfigs = ref<SyncConfig[]>([])
const loading = ref(false)

// 分页参数
const page = reactive({
  current: 1,
  size: 20,
  total: 0
})

// 过滤条件
const filter = reactive({
  config: '',
  dateRange: [] as string[],
  objectType: '',
  action: ''
})

// 格式化日期时间
const formatDateTime = (datetime: string) => {
  return dayjs(datetime).format('YYYY-MM-DD HH:mm:ss')
}

// 获取配置名称
const getConfigName = (configId: string): string => {
  const config = syncConfigs.value.find(c => c.id === configId)
  return config ? config.name : configId
}

// 获取变更的属性
const getChangedAttributes = (row: any) => {
  const result: Record<string, {old: any, new: any}> = {}
  
  // 如果是创建或删除，直接返回空对象
  if (row.action === 'create' || row.action === 'delete') {
    return result
  }
  
  const oldData = row.old_data || {}
  const newData = row.new_data || {}
  
  // 合并所有键
  const allKeys = [...new Set([...Object.keys(oldData), ...Object.keys(newData)])]
  
  // 比较每个键的值
  for (const key of allKeys) {
    const oldValue = oldData[key]
    const newValue = newData[key]
    
    // 只有值不同时才添加到结果中
    if (oldValue !== newValue) {
      result[key] = {
        old: oldValue,
        new: newValue
      }
    }
  }
  
  return result
}

// 加载同步日志数据
const loadData = async () => {
  loading.value = true
  try {
    // 构建查询参数
    const params: Record<string, any> = {
      page: page.current,
      page_size: page.size
    }
    
    if (filter.config) {
      params.config = filter.config
    }
    
    if (filter.dateRange && filter.dateRange.length === 2) {
      params.start_date = filter.dateRange[0]
      params.end_date = filter.dateRange[1]
    }
    
    if (filter.objectType) {
      params.object_type = filter.objectType
    }
    
    if (filter.action) {
      params.action = filter.action
    }
    
    const res = await syncLogApi.getLogs(params)
    syncLogs.value = res.data.results || res.data
    page.total = res.data.count || res.data.length
  } catch (error) {
    console.error('加载同步日志失败:', error)
    ElMessage.error('加载同步日志失败')
  } finally {
    loading.value = false
  }
}

// 加载同步配置
const loadConfigs = async () => {
  try {
    const res = await syncConfigApi.getConfigs()
    syncConfigs.value = res.data
  } catch (error) {
    console.error('加载同步配置失败:', error)
  }
}

// 获取操作标签类型
const getActionTagType = (action: string): string => {
  const map: Record<string, string> = {
    'create': 'success',
    'update': 'warning',
    'delete': 'danger',
    'move': 'info'
  }
  return map[action] || ''
}

// 处理分页
const handleSizeChange = () => {
  page.current = 1
  loadData()
}

const handleCurrentChange = () => {
  loadData()
}

// 初始加载
onMounted(() => {
  loadConfigs()
  loadData()
})
</script>

<style scoped>
.sync-logs-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: bold;
}

.filter-section {
  display: flex;
  align-items: center;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.list-header span {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.truncate-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.expand-container {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table__expanded-cell) {
  padding: 0 !important;
}

:deep(.el-table__expand-icon) {
  margin-right: 10px;
}

/* 变更内容样式 */
.change-content {
  max-height: 200px;
  overflow-y: auto;
}

.change-item-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.change-item {
  display: flex;
  align-items: flex-start;
  font-size: 13px;
}

.change-key {
  font-weight: bold;
  margin-right: 5px;
  min-width: 70px;
}

.change-comparison {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
}

.change-value {
  word-break: break-word;
}

.old-value {
  color: #f56c6c;
  text-decoration: line-through;
}

.new-value {
  color: #67c23a;
}

.arrow {
  color: #909399;
  margin: 0 5px;
  font-weight: bold;
}
</style> 