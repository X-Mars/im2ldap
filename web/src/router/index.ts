import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw, NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useUserStore } from '@/store/user'
import { 
  DataLine, 
  Document, 
  Lock,
  Edit,
  View,
  User,
  Setting,
  Notebook,
  SwitchButton,
  Connection
} from '@element-plus/icons-vue'
import type { Component } from 'vue'

// 扩展 RouteMeta 类型
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: string[]
    title?: string
    icon?: Component
    hidden?: boolean
  }
}

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: {
      requiresAuth: true,
      title: '仪表盘',
      icon: DataLine
    },
    children: [
      {
        path: '/',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          title: '仪表盘',
          icon: DataLine
        }
      }
    ]
  },
  {
    path: '/auth/users',
    name: 'Auth',
    component: () => import('@/views/Layout.vue'),
    meta: { 
      title: '权限管理',
      icon: Lock,
      roles: ['admin', 'superuser']
    },
    children: [
      {
        path: '/auth/users',
        name: 'Users',
        component: () => import('@/views/auth/Users.vue'),
        meta: {
          title: '用户管理',
          icon: User
        }
      },
      // {
      //   path: '/auth/groups',
      //   name: 'AuthGroups',
      //   component: () => import('@/views/auth/Groups.vue'),
      //   meta: {
      //     title: '分组管理',
      //     icon: FolderOpened
      //   }
      // }
    ]
  },
  {
    path: '/oauth/callback',
    name: 'OAuthCallback',
    component: () => import('@/views/auth/OAuthCallback.vue'),
    meta: {
      title: '第三方登录',
      requiresAuth: false
    }
  },
  {
    path: '/system/oauth',
    name: 'System',
    component: () => import('@/views/Layout.vue'),
    meta: {
      title: '系统管理',
      requiresAuth: true,
      roles: ['superuser']
    },
    children: [
      {
        path: '/system/oauth',
        name: 'SystemOAuth',
        component: () => import('@/views/auth/OAuthConfig.vue'),
        meta: {
          title: '第三方登录配置',
          icon: Setting
        }
      }
    ]
  },
  {
    path: '/sync',
    name: 'Sync',
    component: () => import('@/views/Layout.vue'),
    meta: {
      title: '同步管理',
      icon: SwitchButton,
      requiresAuth: true
    },
    children: [
      {
        path: '/sync/ldap-configs',
        name: 'LDAPConfigs',
        component: () => import('@/views/sync/LDAPConfigs.vue'),
        meta: { 
          title: 'LDAP配置', 
          icon: Connection
        }
      },
      {
        path: '/sync/configs',
        name: 'SyncConfigs',
        component: () => import('@/views/sync/SyncConfigs.vue'),
        meta: { 
          title: '同步配置', 
          icon: Setting
        }
      },
      {
        path: '/sync/logs',
        name: 'SyncLogs',
        component: () => import('@/views/sync/SyncLogs.vue'),
        meta: { 
          title: '同步日志', 
          icon: Document
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  const userStore = useUserStore()
  const token = localStorage.getItem('token')

  // 等待用户信息初始化
  await userStore.initialize()

  if (to.meta.requiresAuth && !token) {
    // 需要登录但未登录，跳转到登录页
    next('/login')
  } else if (to.meta.roles && !to.meta.roles.includes(userStore.user?.role)) {
    // 需要特定角色权限但没有权限，重定向到首页
    next('/')
  } else {
    next()
  }
})

export default router 
