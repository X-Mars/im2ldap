export interface ApiResponse<T> {
  data: T
  status: number
  message?: string
}

export interface PaginatedResponse<T> {
  results: T[]
  count: number
}

export interface Note {
  id: string
  title: string
  content: string
  group: string | null
  created_at: string
  updated_at: string
  creator?: {
    id: string
    username: string
    name: string
  }
  group_detail?: {
    id: string
    name: string
  }
}

export interface NoteResponse {
  results: Note[]
  count: number
}

export interface User {
  id: string
  username: string
  name: string
  first_name: string
  last_name: string
  email: string
  role: string
  is_active: boolean
  last_active_at: string
  date_joined: string
  notes?: string[]
  note_group?: string[]
  statusLoading?: boolean
  avatar?: string
}

export interface Group {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  note_count?: number
  creator?: {
    id: string
    username: string
    name: string
  }
}

export interface OAuthUrls {
  wecom_url: string | null
  feishu_url: string | null
  dingtalk_url: string | null
  github_url: string | null
  google_url: string | null
  gitlab_url: string | null
}

export interface LDAPConfig {
  id: string
  server_uri: string
  bind_dn: string
  bind_password?: string
  base_dn: string
  use_ssl: boolean
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface SyncLog {
  id: string
  config: string
  sync_time: string
  success: boolean
  message: string
  users_synced: number
  departments_synced: number
}

export interface SyncConfig {
  id: string
  name: string
  sync_type: 'wecom' | 'feishu' | 'dingtalk'
  ldap_config: string
  ldap_config_details?: LDAPConfig
  sync_users: boolean
  sync_departments: boolean
  user_ou: string
  department_ou: string
  sync_frequency: 'realtime' | 'hourly' | 'daily' | 'weekly' | 'manual'
  last_sync_time: string | null
  enabled: boolean
  created_at: string
  updated_at: string
  logs?: SyncLog[]
}

// 同步类型
export type SyncType = 'wecom' | 'feishu' | 'dingtalk';

// 同步频率
export type SyncFrequency = 'realtime' | 'hourly' | 'daily' | 'weekly' | 'manual'; 