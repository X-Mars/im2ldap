<template>
  <div class="users-container">
    <div class="header">
      <div class="left">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>新建用户
        </el-button>
      </div>
      <div class="right">
        <el-button type="info" @click="refreshCurrentTab">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" @tab-click="handleTabChange">
      <el-tab-pane label="本地用户" name="local">
        <el-table 
          :data="users" 
          v-loading="loading.local"
          stripe
        >
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="first_name" label="姓名">
            <template #default="{ row }">
              {{ row.first_name }} {{ row.last_name }}
            </template>
          </el-table-column>
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="role" label="角色">
            <template #default="{ row }">
              <el-tag :type="getRoleTagType(row.role)">{{ getRoleLabel(row.role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                :loading="row.statusLoading"
                @change="handleStatusChange(row)"
                :active-text="row.is_active ? '启用' : '禁用'"
                :disabled="row.username === userStore.user?.username"
                inline-prompt
              />
            </template>
          </el-table-column>
          <el-table-column prop="last_active_at" label="最后活跃时间">
            <template #default="{ row }">
              {{ formatDateTime(row.last_active_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="date_joined" label="加入时间">
            <template #default="{ row }">
              {{ formatDateTime(row.date_joined) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" :width="200" fixed="right">
            <template #default="{ row }">
              <el-button-group>
                <el-button 
                  type="primary" 
                  :icon="Edit"
                  @click="handleEdit(row)"
                >
                  编辑
                </el-button>
                <el-button 
                  type="danger" 
                  :icon="Delete"
                  :disabled="row.username === userStore.user?.username"
                  @click="handleDelete(row)"
                >
                  删除
                </el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="企业微信用户" name="wecom">
        <el-table 
          :data="wecomUsers" 
          v-loading="loading.wecom"
          stripe
        >
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="mobile" label="手机号" />
          <el-table-column prop="department" label="部门" />
          <el-table-column prop="position" label="职位" />
          <el-table-column prop="created_at" label="创建时间">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="已关联本地用户" width="180">
            <template #default="{ row }">
              <el-tag v-if="row.linked" type="success">
                {{ getLinkedUserName(row.user_id) }}
              </el-tag>
              <span v-else>未关联</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small"
                @click="handleLinkUser(row, 'wecom')"
              >
                {{ row.linked ? '修改关联' : '关联本地用户' }}
              </el-button>
              <el-button 
                v-if="row.linked"
                type="danger" 
                size="small"
                @click="handleUnlinkUser(row, 'wecom')"
              >
                解除关联
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="飞书用户" name="feishu">
        <el-table 
          :data="feishuUsers" 
          v-loading="loading.feishu"
          stripe
        >
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="mobile" label="手机号" />
          <el-table-column prop="department" label="部门" />
          <el-table-column prop="position" label="职位" />
          <el-table-column prop="created_at" label="创建时间">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="已关联本地用户" width="180">
            <template #default="{ row }">
              <el-tag v-if="row.linked" type="success">
                {{ getLinkedUserName(row.user_id) }}
              </el-tag>
              <span v-else>未关联</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small"
                @click="handleLinkUser(row, 'feishu')"
              >
                {{ row.linked ? '修改关联' : '关联本地用户' }}
              </el-button>
              <el-button 
                v-if="row.linked"
                type="danger" 
                size="small"
                @click="handleUnlinkUser(row, 'feishu')"
              >
                解除关联
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="钉钉用户" name="dingtalk">
        <el-table 
          :data="dingtalkUsers" 
          v-loading="loading.dingtalk"
          stripe
        >
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="mobile" label="手机号" />
          <el-table-column prop="department" label="部门" />
          <el-table-column prop="position" label="职位" />
          <el-table-column prop="created_at" label="创建时间">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="已关联本地用户" width="180">
            <template #default="{ row }">
              <el-tag v-if="row.linked" type="success">
                {{ getLinkedUserName(row.user_id) }}
              </el-tag>
              <span v-else>未关联</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small"
                @click="handleLinkUser(row, 'dingtalk')"
              >
                {{ row.linked ? '修改关联' : '关联本地用户' }}
              </el-button>
              <el-button 
                v-if="row.linked"
                type="danger" 
                size="small"
                @click="handleUnlinkUser(row, 'dingtalk')"
              >
                解除关联
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="GitHub用户" name="github">
        <el-table 
          :data="githubUsers" 
          v-loading="loading.github"
          stripe
        >
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="created_at" label="创建时间">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="已关联本地用户" width="180">
            <template #default="{ row }">
              <el-tag v-if="row.linked" type="success">
                {{ getLinkedUserName(row.user_id) }}
              </el-tag>
              <span v-else>未关联</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small"
                @click="handleLinkUser(row, 'github')"
              >
                {{ row.linked ? '修改关联' : '关联本地用户' }}
              </el-button>
              <el-button 
                v-if="row.linked"
                type="danger" 
                size="small"
                @click="handleUnlinkUser(row, 'github')"
              >
                解除关联
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="Google用户" name="google">
        <el-table 
          :data="googleUsers" 
          v-loading="loading.google"
          stripe
        >
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="created_at" label="创建时间">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="已关联本地用户" width="180">
            <template #default="{ row }">
              <el-tag v-if="row.linked" type="success">
                {{ getLinkedUserName(row.user_id) }}
              </el-tag>
              <span v-else>未关联</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small"
                @click="handleLinkUser(row, 'google')"
              >
                {{ row.linked ? '修改关联' : '关联本地用户' }}
              </el-button>
              <el-button 
                v-if="row.linked"
                type="danger" 
                size="small"
                @click="handleUnlinkUser(row, 'google')"
              >
                解除关联
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="GitLab用户" name="gitlab">
        <el-table 
          :data="gitlabUsers" 
          v-loading="loading.gitlab"
          stripe
        >
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="created_at" label="创建时间">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="已关联本地用户" width="180">
            <template #default="{ row }">
              <el-tag v-if="row.linked" type="success">
                {{ getLinkedUserName(row.user_id) }}
              </el-tag>
              <span v-else>未关联</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small"
                @click="handleLinkUser(row, 'gitlab')"
              >
                {{ row.linked ? '修改关联' : '关联本地用户' }}
              </el-button>
              <el-button 
                v-if="row.linked"
                type="danger" 
                size="small"
                @click="handleUnlinkUser(row, 'gitlab')"
              >
                解除关联
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="Gitee用户" name="gitee">
        <el-table 
          :data="giteeUsers" 
          v-loading="loading.gitee"
          stripe
        >
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="created_at" label="创建时间">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="已关联本地用户" width="180">
            <template #default="{ row }">
              <el-tag v-if="row.linked" type="success">
                {{ getLinkedUserName(row.user_id) }}
              </el-tag>
              <span v-else>未关联</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small"
                @click="handleLinkUser(row, 'gitee')"
              >
                {{ row.linked ? '修改关联' : '关联本地用户' }}
              </el-button>
              <el-button 
                v-if="row.linked"
                type="danger" 
                size="small"
                @click="handleUnlinkUser(row, 'gitee')"
              >
                解除关联
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="dialogVisible"
      :title="currentUser ? '编辑用户' : '新建用户'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item 
          label="密码" 
          prop="password"
          :rules="[
            { required: !currentUser, message: '请输入密码' }
          ]"
        >
          <el-input 
            v-model="form.password" 
            type="password"
            :disabled="currentUser?.username === userStore.user?.username"
            :placeholder="currentUser?.username === userStore.user?.username ? 
              '不能修改自己的密码' : 
              (currentUser ? '不修改请留空' : '请输入密码')"
          />
        </el-form-item>
        <el-form-item label="姓" prop="first_name">
          <el-input v-model="form.first_name" />
        </el-form-item>
        <el-form-item label="名" prop="last_name">
          <el-input v-model="form.last_name" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="超级管理员" value="superuser" />
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 关联用户对话框 -->
    <el-dialog
      v-model="linkDialogVisible"
      title="关联本地用户"
      width="500px"
    >
      <el-form
        ref="linkFormRef"
        :model="linkForm"
        label-width="100px"
      >
        <el-form-item label="第三方用户" prop="thirdPartyUser">
          <el-input v-model="linkForm.thirdPartyUsername" disabled />
        </el-form-item>
        <el-form-item label="本地用户" prop="localUserId">
          <el-select v-model="linkForm.localUserId" filterable placeholder="请选择本地用户">
            <el-option
              v-for="user in availableLocalUsers"
              :key="user.id"
              :label="`${user.first_name} ${user.last_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
          <div class="select-hint" v-if="availableLocalUsers.length === 0">
            没有可用的空闲本地用户，所有用户都已被关联
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="linkDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitLinkUser" :loading="linkSubmitting" 
                   :disabled="availableLocalUsers.length === 0">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { Plus, Edit, Delete, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { userApi } from '@/api/users'
import type { User } from '@/api/types'
import type { 
  WeComUser, 
  FeiShuUser, 
  DingTalkUser, 
  GitHubUser, 
  GoogleUser, 
  GitLabUser, 
  GiteeUser 
} from '@/api/users'
import { useUserStore } from '@/store/user'

// 用户数据
const users = ref<User[]>([])
const wecomUsers = ref<WeComUser[]>([])
const feishuUsers = ref<FeiShuUser[]>([])
const dingtalkUsers = ref<DingTalkUser[]>([])
const githubUsers = ref<GitHubUser[]>([])
const googleUsers = ref<GoogleUser[]>([])
const gitlabUsers = ref<GitLabUser[]>([])
const giteeUsers = ref<GiteeUser[]>([])

// 加载状态
const loading = reactive({
  local: false,
  wecom: false,
  feishu: false,
  dingtalk: false,
  github: false,
  google: false,
  gitlab: false,
  gitee: false
})

const submitting = ref(false)
const dialogVisible = ref(false)
const currentUser = ref<User | null>(null)
const formRef = ref<FormInstance>()
const activeTab = ref('local')

const form = reactive({
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
  role: 'user',
  is_active: true
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { 
      validator: (rule, value, callback) => {
        if (!currentUser.value && !value) {
          callback(new Error('请输入密码'))
        } else if (value && value.length < 6) {
          callback(new Error('密码长度至少为6位，并同时包含大小写字母和数字'))
        } else if (value && !/[A-Z]/.test(value)) {
          callback(new Error('密码长度至少为6位，并同时包含大小写字母和数字'))
        } else if (value && !/[a-z]/.test(value)) {
          callback(new Error('密码长度至少为6位，并同时包含大小写字母和数字'))
        } else if (value && !/\d/.test(value)) {
          callback(new Error('密码长度至少为6位，并同时包含大小写字母和数字'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 关联用户表单数据
const linkDialogVisible = ref(false)
const linkSubmitting = ref(false)
const linkFormRef = ref<FormInstance>()
const linkForm = reactive({
  thirdPartyUserId: '',
  thirdPartyUsername: '',
  thirdPartyType: '',
  localUserId: ''
})

const fetchUsers = async () => {
  loading.local = true
  try {
    const res = await userApi.getUsers()
    users.value = res.data.map(user => ({
      ...user,
      statusLoading: false
    }))
  } catch (error) {
    console.error(error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.local = false
  }
}

const fetchWeComUsers = async () => {
  loading.wecom = true
  try {
    const res = await userApi.getWeComUsers()
    wecomUsers.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('获取企业微信用户列表失败')
  } finally {
    loading.wecom = false
  }
}

const fetchFeiShuUsers = async () => {
  loading.feishu = true
  try {
    const res = await userApi.getFeiShuUsers()
    feishuUsers.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('获取飞书用户列表失败')
  } finally {
    loading.feishu = false
  }
}

const fetchDingTalkUsers = async () => {
  loading.dingtalk = true
  try {
    const res = await userApi.getDingTalkUsers()
    dingtalkUsers.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('获取钉钉用户列表失败')
  } finally {
    loading.dingtalk = false
  }
}

const fetchGitHubUsers = async () => {
  loading.github = true
  try {
    const res = await userApi.getGitHubUsers()
    githubUsers.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('获取GitHub用户列表失败')
  } finally {
    loading.github = false
  }
}

const fetchGoogleUsers = async () => {
  loading.google = true
  try {
    const res = await userApi.getGoogleUsers()
    googleUsers.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('获取Google用户列表失败')
  } finally {
    loading.google = false
  }
}

const fetchGitLabUsers = async () => {
  loading.gitlab = true
  try {
    const res = await userApi.getGitLabUsers()
    gitlabUsers.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('获取GitLab用户列表失败')
  } finally {
    loading.gitlab = false
  }
}

const fetchGiteeUsers = async () => {
  loading.gitee = true
  try {
    const res = await userApi.getGiteeUsers()
    giteeUsers.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('获取Gitee用户列表失败')
  } finally {
    loading.gitee = false
  }
}

const handleTabChange = (tab: any) => {
  const tabName = tab.props.name
  activeTab.value = tabName
  
  // 始终刷新当前标签页的数据
  refreshDataByTabName(tabName)
}

// 添加刷新当前标签页数据的函数
const refreshCurrentTab = () => {
  refreshDataByTabName(activeTab.value)
}

// 根据标签名刷新对应数据的函数
const refreshDataByTabName = (tabName: string) => {
  switch (tabName) {
    case 'local':
      fetchUsers()
      break
    case 'wecom':
      fetchWeComUsers()
      break
    case 'feishu':
      fetchFeiShuUsers()
      break
    case 'dingtalk':
      fetchDingTalkUsers()
      break
    case 'github':
      fetchGitHubUsers()
      break
    case 'google':
      fetchGoogleUsers()
      break
    case 'gitlab':
      fetchGitLabUsers()
      break
    case 'gitee':
      fetchGiteeUsers()
      break
  }
}

// 添加一个新的计算属性，过滤出未关联的本地用户
const availableLocalUsers = computed(() => {
  // 获取所有已关联的用户ID列表
  const linkedUserIds = new Set();
  
  // 收集所有已关联的本地用户ID
  wecomUsers.value.forEach(user => {
    if (user.linked && user.user_id) {
      linkedUserIds.add(user.user_id);
    }
  });
  
  feishuUsers.value.forEach(user => {
    if (user.linked && user.user_id) {
      linkedUserIds.add(user.user_id);
    }
  });
  
  dingtalkUsers.value.forEach(user => {
    if (user.linked && user.user_id) {
      linkedUserIds.add(user.user_id);
    }
  });
  
  githubUsers.value.forEach(user => {
    if (user.linked && user.user_id) {
      linkedUserIds.add(user.user_id);
    }
  });
  
  googleUsers.value.forEach(user => {
    if (user.linked && user.user_id) {
      linkedUserIds.add(user.user_id);
    }
  });
  
  gitlabUsers.value.forEach(user => {
    if (user.linked && user.user_id) {
      linkedUserIds.add(user.user_id);
    }
  });
  
  giteeUsers.value.forEach(user => {
    if (user.linked && user.user_id) {
      linkedUserIds.add(user.user_id);
    }
  });
  
  // 如果正在编辑现有关联，应该包含当前关联的用户
  if (linkForm.thirdPartyType && linkForm.thirdPartyUserId) {
    const currentLinkedUserId = getCurrentLinkedUserId(
      linkForm.thirdPartyType, 
      linkForm.thirdPartyUserId
    );
    
    if (currentLinkedUserId) {
      linkedUserIds.delete(currentLinkedUserId);
    }
  }
  
  // 返回未关联的用户列表
  return users.value.filter(user => !linkedUserIds.has(user.id));
});

// 获取当前第三方用户关联的本地用户ID
const getCurrentLinkedUserId = (type: string, id: string): string | null => {
  let user;
  
  switch (type) {
    case 'wecom':
      user = wecomUsers.value.find(u => u.id === id);
      break;
    case 'feishu':
      user = feishuUsers.value.find(u => u.id === id);
      break;
    case 'dingtalk':
      user = dingtalkUsers.value.find(u => u.id === id);
      break;
    case 'github':
      user = githubUsers.value.find(u => u.id === id);
      break;
    case 'google':
      user = googleUsers.value.find(u => u.id === id);
      break;
    case 'gitlab':
      user = gitlabUsers.value.find(u => u.id === id);
      break;
    case 'gitee':
      user = giteeUsers.value.find(u => u.id === id);
      break;
  }
  
  // 确保返回的是 string 或 null，而不是 undefined
  return (user && user.linked && user.user_id) ? user.user_id : null;
};

// 修改handleLinkUser函数
const handleLinkUser = (user: any, type: string) => {
  linkDialogVisible.value = true;
  linkForm.thirdPartyUserId = user.id;
  linkForm.thirdPartyUsername = `${user.name} (${user.username || user.email})`;
  linkForm.thirdPartyType = type;
  
  // 如果已经关联了用户，则默认选中该用户
  if (user.linked && user.user_id) {
    linkForm.localUserId = user.user_id;
  } else {
    linkForm.localUserId = '';
  }
  
  // 确保已加载本地用户列表
  if (users.value.length === 0) {
    fetchUsers();
  }
};

// 修改提交函数，处理API错误
const submitLinkUser = async () => {
  if (!linkForm.localUserId || !linkForm.thirdPartyUserId || !linkForm.thirdPartyType) {
    ElMessage.warning('请选择本地用户');
    return;
  }
  
  linkSubmitting.value = true;
  try {
    await userApi.linkUser(
      linkForm.localUserId, 
      linkForm.thirdPartyUserId, 
      linkForm.thirdPartyType
    );
    ElMessage.success('关联成功');
    linkDialogVisible.value = false;
    
    // 刷新对应类型的用户列表
    refreshDataByTabName(linkForm.thirdPartyType);
  } catch (error: any) {
    console.error(error);
    // 显示更具体的错误消息
    if (error.response && error.response.data && error.response.data.error) {
      ElMessage.error(error.response.data.error);
    } else {
      ElMessage.error('关联用户失败');
    }
  } finally {
    linkSubmitting.value = false;
  }
};

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.username = ''
  form.password = ''
  form.first_name = ''
  form.last_name = ''
  form.email = ''
  form.role = 'user'
  form.is_active = true
  currentUser.value = null
}

const handleAdd = () => {
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (user: User) => {
  currentUser.value = user
  Object.assign(form, {
    username: user.username,
    password: '',
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    role: user.role,
    is_active: user.is_active
  })
  dialogVisible.value = true
}

const handleSubmit = () => {
  if (!formRef.value) return
  
  formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (currentUser.value) {
          // 编辑用户
          await userApi.updateUser(currentUser.value.id, form)
          ElMessage.success('保存成功')
        } else {
          // 创建用户
          await userApi.createUser(form)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchUsers()
      } catch (error) {
        console.error(error)
        ElMessage.error('保存失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDelete = async (user: User) => {
  if (user.username === userStore.user?.username) {
    ElMessage.warning('不能删除自己的账号')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要删除该用户吗？此操作不可恢复',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await userApi.deleteUser(user.id)
    ElMessage.success('删除成功')
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error('删除失败')
    }
  }
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\//g, '-')
}

// 处理状态切换
const handleStatusChange = async (user: User & { statusLoading?: boolean }) => {
  // 禁止用户禁用自己的账号
  if (user.username === userStore.user?.username && !user.is_active) {
    ElMessage.warning('不能禁用自己的账号')
    user.is_active = true
    return
  }

  user.statusLoading = true
  try {
    await userApi.updateUser(user.id, { is_active: user.is_active })
    ElMessage.success(`已${user.is_active ? '启用' : '禁用'}用户`)
  } catch (error) {
    console.error(error)
    ElMessage.error('更新状态失败')
    // 恢复原状态
    user.is_active = !user.is_active
  } finally {
    user.statusLoading = false
  }
}

const userStore = useUserStore()

const getRoleLabel = (role: string) => {
  const roleMap: { [key: string]: string } = {
    'superuser': '超级管理员',
    'admin': '管理员',
    'user': '普通用户'
  }
  return roleMap[role] || role
}

const getRoleTagType = (role: string) => {
  const typeMap: { [key: string]: 'primary' | 'success' | 'warning' | 'info' | 'danger' } = {
    'superuser': 'danger',
    'admin': 'warning',
    'user': 'success'
  }
  return typeMap[role] || 'info'
}

// 获取已关联本地用户的名称
const getLinkedUserName = (userId: string | undefined) => {
  if (!userId) return '未知用户'
  const user = users.value.find(u => u.id === userId)
  if (user) {
    return `${user.first_name} ${user.last_name} (${user.username})`
  }
  return '未知用户'
}

// 添加解除关联的处理函数
const handleUnlinkUser = async (user: any, type: string) => {
  if (!user.user_id) {
    ElMessage.warning('未找到已关联的本地用户');
    return;
  }

  try {
    await ElMessageBox.confirm(
      '确定要解除关联吗？解除关联后，该第三方用户将无法使用关联的本地账号登录。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    linkSubmitting.value = true;
    await userApi.unlinkUser(user.user_id, type);
    ElMessage.success('已解除关联');

    // 刷新对应类型的用户列表
    switch (type) {
      case 'wecom':
        fetchWeComUsers();
        break;
      case 'feishu':
        fetchFeiShuUsers();
        break;
      case 'dingtalk':
        fetchDingTalkUsers();
        break;
      case 'github':
        fetchGitHubUsers();
        break;
      case 'google':
        fetchGoogleUsers();
        break;
      case 'gitlab':
        fetchGitLabUsers();
        break;
      case 'gitee':
        fetchGiteeUsers();
        break;
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(error);
      if (error.response && error.response.data && error.response.data.message) {
        ElMessage.error(error.response.data.message);
      } else {
        ElMessage.error('解除关联失败');
      }
    }
  } finally {
    linkSubmitting.value = false;
  }
};

onMounted(() => {
  // 获取默认标签页的数据
  refreshDataByTabName(activeTab.value)
})
</script>

<style scoped>
.users-container {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left {
  /* 左侧按钮容器 */
}

.right {
  /* 右侧按钮容器 */
}

:deep(.el-switch) {
  --el-switch-on-color: var(--el-color-success);
}

:deep(.el-tabs__header) {
  margin-bottom: 20px;
}

:deep(.el-tabs__item) {
  padding: 0 20px;
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}

.el-dialog :deep(.el-tabs) {
  margin: -20px;
}

.el-dialog :deep(.el-tab-pane) {
  padding: 20px;
}

.select-hint {
  font-size: 12px;
  color: #F56C6C;
  margin-top: 5px;
}
</style> 