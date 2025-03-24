import request from '@/api/request'
import type { LDAPConfig, SyncConfig, SyncLog, SyncType, SyncFrequency } from './types'

// LDAP配置接口
export const ldapConfigApi = {
  getConfigs: () => {
    return request.get<LDAPConfig[]>('/sync/ldap-configs/')
  },
  
  getConfig: (id: string) => {
    return request.get<LDAPConfig>(`/sync/ldap-configs/${id}/`)
  },
  
  createConfig: (data: Partial<LDAPConfig>) => {
    return request.post<LDAPConfig>('/sync/ldap-configs/', data)
  },
  
  updateConfig: (id: string, data: Partial<LDAPConfig>) => {
    return request.patch<LDAPConfig>(`/sync/ldap-configs/${id}/`, data)
  },
  
  deleteConfig: (id: string) => {
    return request.delete(`/sync/ldap-configs/${id}/`)
  },
  
  testConnection: (id: string) => {
    return request.post(`/sync/ldap-configs/${id}/test_connection/`)
  }
}

// 同步配置接口
export const syncConfigApi = {
  getConfigs: (params?: any) => {
    return request({
      url: '/sync/sync-configs/',
      method: 'get',
      params
    })
  },
  
  getConfig: (id: string) => {
    return request.get<SyncConfig>(`/sync/sync-configs/${id}/`)
  },
  
  createConfig: (data: Partial<SyncConfig>) => {
    return request.post<SyncConfig>('/sync/sync-configs/', data)
  },
  
  updateConfig: (id: string, data: Partial<SyncConfig>) => {
    return request.patch<SyncConfig>(`/sync/sync-configs/${id}/`, data)
  },
  
  deleteConfig: (id: string) => {
    return request.delete(`/sync/sync-configs/${id}/`)
  },
  
  syncNow: (id: string) => {
    return request.post(`/sync/sync-configs/${id}/sync_now/`)
  }
}

// 同步日志接口
export const syncLogApi = {
  getLogs: (params?: any) => {
    return request({
      url: '/sync/sync-logs/',
      method: 'get',
      params
    })
  },
  
  getLog: (id: string) => {
    return request.get<SyncLog>(`/sync/sync-logs/${id}/`)
  },
  
  // 获取同步日志详情
  getLogDetails(logId: string, params?: any) {
    return request({
      url: `/sync/sync-logs/${logId}/details/`,
      method: 'get',
      params
    })
  }
}

// 将表单数据转换为正确的类型
export const convertFormToSyncConfig = (formData: any): Partial<SyncConfig> => {
  return {
    ...formData,
    sync_type: formData.sync_type as SyncType,
    sync_frequency: formData.sync_frequency as SyncFrequency
  }
}

// 获取用户趋势数据
export const getUserTrend = (range: string = 'week') => {
  return request.get('/sync/user-trend/', { params: { range } });
};

// 获取用户统计数据
export const getUserStats = () => {
  return request.get('/sync/user-stats/');
}; 