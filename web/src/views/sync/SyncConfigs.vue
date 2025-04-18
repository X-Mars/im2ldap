<template>
  <div class="sync-configs-container">
    <div class="page-header">
      <h2>同步配置</h2>
      <el-button 
        type="primary" 
        @click="handleAddConfig"
        :icon="Plus"
      >
        新增配置
      </el-button>
    </div>
      
      <el-table 
        :data="syncConfigs" 
        style="width: 100%" 
        v-loading="loading"
      >
        <el-table-column prop="name" label="配置名称" />
        <el-table-column label="同步类型">
          <template #default="scope">
            <el-tag :type="getSyncTypeTag(scope.row.sync_type)">
              {{ getSyncTypeName(scope.row.sync_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="同步范围">
          <template #default="scope">
            <div>
              <el-tag type="success" size="small" v-if="scope.row.sync_users">用户</el-tag>
              <el-tag type="info" size="small" v-else>不同步用户</el-tag>
            </div>
            <div style="margin-top: 5px">
              <el-tag type="success" size="small" v-if="scope.row.sync_departments">部门</el-tag>
              <el-tag type="info" size="small" v-else>不同步部门</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="同步频率">
          <template #default="scope">
            <el-tag :type="getFrequencyTag(scope.row.sync_interval)">
              {{ getFrequencyName(scope.row.sync_interval) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上次同步">
          <template #default="scope">
            <span v-if="scope.row.last_sync_time">{{ formatDateTime(scope.row.last_sync_time) }}</span>
            <span v-else>从未同步</span>
          </template>
        </el-table-column>
        <el-table-column label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.enabled ? 'success' : 'danger'">
              {{ scope.row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button-group>
              <el-button 
                type="primary" 
                @click="handleEditConfig(scope.row)"
                :icon="Edit"
              >
                编辑
              </el-button>
              <el-button 
                type="primary"
                @click="handleSyncNow(scope.row)"
                :loading="syncingId === scope.row.id"
                :icon="Refresh"
              >
                同步
              </el-button>
              <el-button 
                type="danger" 
                @click="handleDeleteConfig(scope.row)"
                :icon="Delete"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    
    <!-- 编辑/新增对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑同步配置' : '新增同步配置'"
      width="600px"
    >
      <el-form 
        :model="formData" 
        label-width="120px" 
        :rules="formRules"
        ref="formRef"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入配置名称" />
        </el-form-item>
        
        <el-form-item label="同步类型" prop="sync_type">
          <el-select 
            v-model="formData.sync_type" 
            placeholder="请选择同步类型"
            style="width: 100%"
            :disabled="isEdit"
          >
            <el-option label="企业微信" value="wecom" />
            <el-option label="飞书" value="feishu" />
            <el-option label="钉钉" value="dingtalk" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="LDAP配置" prop="ldap_config">
          <el-select 
            v-model="formData.ldap_config" 
            placeholder="请选择LDAP配置"
            style="width: 100%"
          >
            <el-option 
              v-for="config in ldapConfigs" 
              :key="config.id" 
              :label="config.server_uri" 
              :value="config.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="同步范围">
          <el-checkbox v-model="formData.sync_users">同步用户</el-checkbox>
          <el-checkbox v-model="formData.sync_departments">同步部门</el-checkbox>
        </el-form-item>
        
        <el-form-item label="用户OU" prop="user_ou" v-if="formData.sync_users">
          <el-input v-model="formData.user_ou" placeholder="用户OU，例如：users" />
        </el-form-item>
        
        <el-form-item label="部门OU" prop="department_ou" v-if="formData.sync_departments">
          <el-input v-model="formData.department_ou" placeholder="部门OU，例如：departments" />
        </el-form-item>
        
        <el-form-item label="同步间隔(秒)" prop="sync_interval">
          <el-input-number 
            v-model="formData.sync_interval" 
            :min="60"
            :max="86400"
            :step="60"
            style="width: 100%"
            placeholder="请输入同步间隔秒数"
          />
          <div class="form-item-tip">最小60秒，最大86400秒(24小时)</div>
        </el-form-item>
        
        <el-form-item label="启用">
          <el-switch v-model="formData.enabled" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveConfig" :loading="saving">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Edit, Delete, Plus, Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { ldapConfigApi, syncConfigApi, convertFormToSyncConfig } from '@/api/sync'
import type { LDAPConfig, SyncConfig } from '@/api/types'

// 数据列表
const syncConfigs = ref<SyncConfig[]>([])
const ldapConfigs = ref<LDAPConfig[]>([])
const loading = ref(false)
const syncingId = ref('')

// 表单相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const saving = ref(false)
const formData = reactive({
  id: '',
  name: '',
  sync_type: 'wecom',
  ldap_config: '',
  sync_users: true,
  sync_departments: true,
  user_ou: 'users',
  department_ou: 'departments',
  sync_frequency: 'manual',
  enabled: true
})

// 表单校验规则
const formRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  sync_type: [
    { required: true, message: '请选择同步类型', trigger: 'change' }
  ],
  ldap_config: [
    { required: true, message: '请选择LDAP配置', trigger: 'change' }
  ],
  user_ou: [
    { required: true, message: '请输入用户OU', trigger: 'blur' }
  ],
  department_ou: [
    { required: true, message: '请输入部门OU', trigger: 'blur' }
  ],
  sync_frequency: [
    { required: true, message: '请选择同步频率', trigger: 'change' }
  ]
}

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
const getSyncTypeTag = (type: string): 'primary' | 'success' | 'warning' | 'info' => {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'info'> = {
    'wecom': 'primary',
    'feishu': 'success',
    'dingtalk': 'warning'
  }
  return typeMap[type] || 'info'
}

// 获取频率名称
const getFrequencyName = (interval: number) => {
  if (interval < 300) { // 5分钟以内
    return '每' + interval + '秒'
  } else if (interval < 3600) { // 1小时以内
    return '每' + Math.floor(interval / 60) + '分钟'
  } else if (interval < 86400) { // 24小时以内
    return '每' + Math.floor(interval / 3600) + '小时'
  } else { // 超过24小时
    return '每' + Math.floor(interval / 86400) + '天'
  }
}

// 获取频率标签样式
const getFrequencyTag = (interval: number): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  if (interval < 300) { // 5分钟以内
    return 'danger'
  } else if (interval < 3600) { // 1小时以内
    return 'warning'
  } else if (interval < 86400) { // 24小时以内
    return 'success'
  } else { // 超过24小时
    return 'primary'
  }
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
    syncConfigs.value = res.data
  } catch (error) {
    console.error('加载同步配置失败:', error)
    ElMessage.error('加载同步配置失败')
  } finally {
    loading.value = false
  }
}

// 加载LDAP配置
const loadLDAPConfigs = async () => {
  try {
    const res = await ldapConfigApi.getConfigs()
    ldapConfigs.value = res.data.filter(config => config.enabled)
  } catch (error) {
    console.error('加载LDAP配置失败:', error)
    ElMessage.error('加载LDAP配置失败')
  }
}

// 添加配置
const handleAddConfig = async () => {
  // 加载LDAP配置
  await loadLDAPConfigs()
  if (ldapConfigs.value.length === 0) {
    ElMessage.warning('请先添加LDAP配置')
    return
  }
  
  isEdit.value = false
  // 重置表单
  Object.assign(formData, {
    id: '',
    name: '',
    sync_type: 'wecom',
    ldap_config: ldapConfigs.value[0].id, // 默认选择第一个LDAP配置
    sync_users: true,
    sync_departments: true,
    user_ou: 'users',
    department_ou: 'departments',
    sync_frequency: 'manual',
    enabled: true
  })
  
  dialogVisible.value = true
}

// 编辑配置
const handleEditConfig = async (row: SyncConfig) => {
  // 加载LDAP配置
  await loadLDAPConfigs()
  
  isEdit.value = true
  
  // 填充表单
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    sync_type: row.sync_type,
    ldap_config: row.ldap_config,
    sync_users: row.sync_users,
    sync_departments: row.sync_departments,
    user_ou: row.user_ou,
    department_ou: row.department_ou,
    sync_frequency: row.sync_frequency,
    enabled: row.enabled
  })
  
  dialogVisible.value = true
}

// 删除配置
const handleDeleteConfig = (row: SyncConfig) => {
  ElMessageBox.confirm(
    '此操作将永久删除该配置, 是否继续?',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await syncConfigApi.deleteConfig(row.id)
      ElMessage.success('删除成功')
      loadData()
    } catch (error) {
      console.error('删除配置失败:', error)
      ElMessage.error('删除配置失败')
    }
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

// 立即同步
const handleSyncNow = async (row: SyncConfig) => {
  syncingId.value = row.id
  try {
    const res = await syncConfigApi.syncNow(row.id)
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

// 保存配置
const handleSaveConfig = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        const configData = convertFormToSyncConfig(formData)
        
        if (isEdit.value) {
          // 编辑模式
          await syncConfigApi.updateConfig(formData.id, configData)
          ElMessage.success('更新成功')
        } else {
          // 新增模式
          await syncConfigApi.createConfig(configData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
      } catch (error) {
        console.error('保存配置失败:', error)
        ElMessage.error('保存配置失败')
      } finally {
        saving.value = false
      }
    }
  })
}

// 初始加载
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.sync-configs-container {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-dialog__body) {
  padding-top: 20px;
}
</style>