<template>
  <div class="ldap-configs-container">
    <div class="page-header">
      <h2>LDAP 配置</h2>
      <el-button 
        type="primary" 
        @click="handleAddConfig"
        :icon="Plus"
      >
        新增配置
      </el-button>
    </div>
      
    <el-table 
      :data="ldapConfigs" 
      v-loading="loading"
      class="ldap-table"
      :height="tableHeight"
    >
      <el-table-column prop="server_uri" label="服务器URI" min-width="200" />
      <el-table-column prop="bind_dn" label="绑定DN" min-width="280" />
      <el-table-column prop="base_dn" label="基础DN" min-width="180" />
      <el-table-column label="SSL" min-width="100">
        <template #default="scope">
          <el-tag :type="scope.row.use_ssl ? 'success' : 'info'">
            {{ scope.row.use_ssl ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" min-width="100">
        <template #default="scope">
          <el-tag :type="scope.row.enabled ? 'success' : 'danger'">
            {{ scope.row.enabled ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="220" fixed="right">
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
              @click="handleTestConnection(scope.row)"
              :loading="testingId === scope.row.id"
              :icon="Connection"
            >
              测试连接
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
      :title="isEdit ? '编辑LDAP配置' : '新增LDAP配置'"
      width="600px"
    >
      <el-form 
        :model="formData" 
        label-width="120px" 
        :rules="formRules"
        ref="formRef"
      >
        <el-form-item label="服务器URI" prop="server_uri">
          <el-input v-model="formData.server_uri" placeholder="例如: ldap://example.com:389" value="ldap://localhost:389"/>
        </el-form-item>
        
        <el-form-item label="绑定DN" prop="bind_dn">
          <el-input v-model="formData.bind_dn" placeholder="例如: cn=admin,dc=example,dc=com" />
        </el-form-item>
        
        <el-form-item label="绑定密码" prop="bind_password">
          <el-input 
            v-model="formData.bind_password" 
            type="password" 
            placeholder="请输入绑定密码" 
            show-password
          />
        </el-form-item>
        
        <el-form-item label="基础DN" prop="base_dn">
          <el-input v-model="formData.base_dn" placeholder="例如: dc=example,dc=com" />
        </el-form-item>
        
        <el-form-item label="启用SSL">
          <el-switch v-model="formData.use_ssl" />
        </el-form-item>
        
        <el-form-item label="启用">
          <el-switch v-model="formData.enabled" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleTestConnectionInForm" 
            :loading="testingInForm"
            :disabled="!isFormChanged"
          >
            测试连接
          </el-button>
          <el-button 
            type="success" 
            @click="handleSaveConfig" 
            :loading="saving"
            :disabled="!connectionTested"
          >
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, watch, computed, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Edit, Delete, Plus, Connection } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { ldapConfigApi } from '@/api/sync'
import type { LDAPConfig } from '@/api/types'

// 数据列表
const ldapConfigs = ref<LDAPConfig[]>([])
const loading = ref(false)
const testingId = ref('')
const tableHeight = ref('calc(100vh - 180px)')

// 自适应表格高度
const updateTableHeight = () => {
  nextTick(() => {
    // 获取页面可用高度并减去其他元素的高度
    const pageHeader = document.querySelector('.page-header')
    const headerHeight = pageHeader ? pageHeader.clientHeight : 60
    const padding = 40 // 顶部和底部的内边距
    
    tableHeight.value = `calc(100vh - ${headerHeight + padding + 60}px)`
  })
}

// 表单相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const saving = ref(false)
const testingInForm = ref(false)
const connectionTested = ref(false)
const isFormChanged = ref(false)
const originalFormData = ref<any>({})

const formData = reactive({
  id: '',
  server_uri: '',
  bind_dn: '',
  bind_password: '',
  base_dn: '',
  use_ssl: false,
  enabled: true
})

// 表单校验规则
const formRules = {
  server_uri: [
    { required: true, message: '请输入服务器URI', trigger: 'blur' },
    { pattern: /^ldaps?:\/\/\S+/, message: '服务器URI格式不正确', trigger: 'blur' }
  ],
  bind_dn: [
    { required: true, message: '请输入绑定DN', trigger: 'blur' }
  ],
  base_dn: [
    { required: true, message: '请输入基础DN', trigger: 'blur' }
  ]
}

// 监听窗口大小变化
const handleResize = () => {
  updateTableHeight()
}

// 加载LDAP配置数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await ldapConfigApi.getConfigs()
    ldapConfigs.value = res.data
    // 数据加载完后更新表格高度
    updateTableHeight()
  } catch (error) {
    console.error('加载LDAP配置失败:', error)
    ElMessage.error('加载LDAP配置失败')
  } finally {
    loading.value = false
  }
}

// 监听表单变化
const watchFormChanges = () => {
  // 表单有修改时，需要重新测试连接
  if (
    formData.server_uri !== originalFormData.value.server_uri ||
    formData.bind_dn !== originalFormData.value.bind_dn ||
    formData.bind_password !== originalFormData.value.bind_password ||
    formData.base_dn !== originalFormData.value.base_dn ||
    formData.use_ssl !== originalFormData.value.use_ssl
  ) {
    connectionTested.value = false
    isFormChanged.value = true
  } else {
    isFormChanged.value = false
  }
}

// 添加配置
const handleAddConfig = () => {
  isEdit.value = false
  // 重置表单
  Object.assign(formData, {
    id: '',
    server_uri: '',
    bind_dn: '',
    bind_password: '',
    base_dn: '',
    use_ssl: false,
    enabled: true
  })
  
  // 记录原始表单数据用于比较
  originalFormData.value = { ...formData }
  
  // 重置连接测试状态
  connectionTested.value = false
  isFormChanged.value = false
  
  dialogVisible.value = true
}

// 编辑配置
const handleEditConfig = (row: LDAPConfig) => {
  isEdit.value = true
  
  // 填充表单
  Object.assign(formData, {
    id: row.id,
    server_uri: row.server_uri,
    bind_dn: row.bind_dn,
    // 不回填密码
    bind_password: '',
    base_dn: row.base_dn,
    use_ssl: row.use_ssl,
    enabled: row.enabled
  })
  
  // 记录原始表单数据用于比较
  originalFormData.value = { ...formData }
  
  // 重置连接测试状态
  connectionTested.value = false
  isFormChanged.value = false
  
  dialogVisible.value = true
}

// 删除配置
const handleDeleteConfig = (row: LDAPConfig) => {
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
      await ldapConfigApi.deleteConfig(row.id)
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

// 测试连接
const handleTestConnection = async (row: LDAPConfig) => {
  testingId.value = row.id
  try {
    const res = await ldapConfigApi.testConnection(row.id)
    ElMessage.success(res.data.message || '连接成功')
  } catch (error: any) {
    console.error('测试连接失败:', error)
    ElMessage.error(error.response?.data?.message || '连接失败')
  } finally {
    testingId.value = ''
  }
}

// 在表单中测试连接
const handleTestConnectionInForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      testingInForm.value = true
      try {
        let configId = formData.id;
        
        // 如果是编辑模式且有ID，先更新配置（但不刷新列表）
        if (isEdit.value && formData.id) {
          // 处理密码，如果为空则不更新
          const updateData = { ...formData } as Partial<LDAPConfig>;
          if (!updateData.bind_password) {
            updateData.bind_password = undefined;
          }
          
          // 更新配置
          const updateRes = await ldapConfigApi.updateConfig(formData.id, updateData);
          configId = updateRes.data.id;
        } else {
          // 新增模式，先创建配置
          const createRes = await ldapConfigApi.createConfig(formData);
          configId = createRes.data.id;
          // 更新表单ID，以便后续操作
          formData.id = configId;
          // 设置为编辑模式
          isEdit.value = true;
        }
        
        // 然后测试连接
        const testRes = await ldapConfigApi.testConnection(configId);
        ElMessage.success(testRes.data.message || '连接成功');
        connectionTested.value = true;
        isFormChanged.value = false;
        originalFormData.value = { ...formData };
      } catch (error: any) {
        console.error('测试连接失败:', error)
        ElMessage.error(error.response?.data?.message || '连接失败')
        connectionTested.value = false
      } finally {
        testingInForm.value = false
      }
    }
  })
}

// 保存配置
const handleSaveConfig = async () => {
  if (!formRef.value || !connectionTested.value) return
  
  // 由于我们已经在测试连接时创建/更新了配置，这里只需要刷新列表
  dialogVisible.value = false;
  ElMessage.success(isEdit.value ? '更新成功' : '创建成功');
  loadData();
}

// 添加watch函数监听formData变化
watch(
  () => [
    formData.server_uri,
    formData.bind_dn,
    formData.bind_password,
    formData.base_dn, 
    formData.use_ssl
  ],
  () => {
    watchFormChanges()
  },
  { deep: true }
)

// 初始加载
onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
  updateTableHeight()
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.ldap-configs-container {
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
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

.ldap-table {
  flex: 1;
  width: 100%;
  margin-bottom: 20px;
}

:deep(.el-dialog__body) {
  padding-top: 20px;
}

:deep(.el-table) {
  height: 100% !important;
}

:deep(.el-table__inner-wrapper) {
  height: 100%;
}
</style> 